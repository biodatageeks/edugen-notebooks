"""Funkcje pomocnicze części 3 (polars-bio, vepyr): przygotowanie danych, pomiary czasu i pamięci, wykresy."""
from pathlib import Path
import hashlib, importlib.metadata, json, os, platform
import shutil, statistics, subprocess, sys, time

SCRIPTS = Path(__file__).resolve().parent
# dane części 3 (pobierane przez setup/prepare_data.sh); manifest danych jest w repozytorium
ROOT = Path(os.environ.get('WORKSHOP_DATA', Path.home() / 'work' / 'data')) / 'part3'
PINS = {'polars-bio': '0.36.0', 'polars': '1.37.1', 'pyarrow': '23.0.1',
        'datafusion': '53.0.0',
        'vepyr': '0.9.0', 'pysam': '0.23.3'}


def setup():
    """Sprawdza sumy kontrolne danych części 3 (w razie potrzeby je pobiera) i przygotowuje pliki robocze."""
    (ROOT / 'data').mkdir(parents=True, exist_ok=True)
    shutil.copy(SCRIPTS.parent / 'data' / 'real_sources.json', ROOT / 'data' / 'real_sources.json')
    from prepare_real_data import prepare
    from prepare_intervals import prepare as prepare_intervals
    vcf, annotation_vcf, cache, reference_fasta = prepare(ROOT)
    variants, exons = prepare_intervals(ROOT, vcf)
    return vcf, annotation_vcf, cache, variants, exons, reference_fasta

def resources():
    import psutil
    return {'Python': platform.python_version(), 'Widoczne CPU': os.cpu_count(),
            'RAM [GiB]': round(psutil.virtual_memory().total/2**30, 2),
            'Wolny dysk [GiB]': round(shutil.disk_usage(ROOT).free/2**30, 2),
            'System': platform.platform(),
            'Wersje': {p: importlib.metadata.version(p) for p in PINS}}

def fingerprint(record):
    return record['records'], tuple(record['fingerprints'])

def measure_streaming(source):
    """Compare materialization and streaming with parallelism fixed at one."""
    from vcf_header import align_header_with_index
    source = align_header_with_index(source)  # outside every timer
    directory = ROOT/'runs'/f'polars_bio_{time.time_ns()}'
    directory.mkdir(parents=True)
    sequence = [(1,'collect_write'),(1,'sink'),(1,'collect_write'),(1,'sink'),(1,'sink'),(1,'collect_write')]
    results = []
    for i, (n, mode) in enumerate(sequence):
        destination = directory/f'run_{i}.json'
        env = os.environ.copy()
        env.update(POLARS_MAX_THREADS=str(n), RAYON_NUM_THREADS=str(n),
                   OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS=str(n))
        command = [sys.executable, str(SCRIPTS/'measure_polars_bio.py'),
                   str(source), mode, str(destination)]
        result = subprocess.run(command,
                                env=env, capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise RuntimeError('Pomiar przerwany:\n'+result.stderr[-4000:])
        record = json.loads(destination.read_text())
        record['warmup'] = i < 2
        results.append(record)
        print('Rozgrzewka' if i<2 else 'Pomiar', mode, f'ustawienie {n}:',
              f"{record['seconds']:.2f} s; RSS maks. {record['peak_rss_gib']:.3f} GiB; "
              f"CPU/czas {record['cpu_seconds']/record['seconds']:.2f}", flush=True)
    assert len({fingerprint(r) for r in results}) == 1, 'Wyniki różnią się — nie interpretuj pomiarów.'
    inputs = [source]
    checksums = {}
    for path in inputs:
        with open(path, 'rb') as stream:
            checksums[Path(path).name] = hashlib.file_digest(stream, 'sha256').hexdigest()
    metadata = dict(environment=resources(), measurements=results, inputs_sha256=checksums)
    (directory/'measurements.json').write_text(json.dumps(metadata,indent=2))
    plot_measurements(results)
    count = f"{results[0]['records']:,}".replace(',', ' ')
    print(f"Wynik zapytania: {count} rekordów × {results[0]['columns']} kolumn.")
    print('Zgodne liczby rekordów i dwie sumy kontrolne. Metadane:', directory)
    print('RSS: próbki pamięci procesu podczas zapytania, co około 10 ms; bez odczytu wyniku do walidacji.')
    return results

def plot_measurements(records):
    import matplotlib.pyplot as plt
    rows = [r for r in records if not r['warmup']]
    key = 'mode'
    groups = ['collect_write','sink']
    labels = ['Wynik w RAM\n+ zapis','Zapis porcjami\nsink_parquet']
    fields = ['seconds','peak_rss_gib']
    fig, axes = plt.subplots(1,len(fields),figsize=(11,4),squeeze=False)
    for ax, field in zip(axes[0],fields):
        values = [statistics.median(r[field] for r in rows if r[key]==g) for g in groups]
        bars = ax.bar(labels,values,color=['#17384c','#008b87'])
        for i, group in enumerate(groups):
            observed = [r[field] for r in rows if r[key] == group]
            offsets = [0] if len(observed) == 1 else [(-.12 + .24*j/(len(observed)-1)) for j in range(len(observed))]
            ax.scatter([i+d for d in offsets], observed, color='#D75E47', s=28, zorder=3)
        ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=4)
        ax.set_ylim(0,max(r[field] for r in rows)*1.2)
        ax.set_ylabel('Czas [s]' if field=='seconds' else 'Maks. zaobserwowane RSS [GiB]')
        ax.spines[['top','right']].set_visible(False)
    title = 'filtr SNV · mediana z 2 pomiarów'
    fig.suptitle('polars-bio · '+title+'\npunkty = poszczególne pomiary')
    fig.tight_layout(); plt.show()

def annotation_chart(frame):
    import matplotlib.pyplot as plt
    counts = frame.group_by('most_severe_consequence').len().sort('len',descending=True).head(8).sort('len')
    fig, ax = plt.subplots(figsize=(10,4))
    ax.barh(counts['most_severe_consequence'],counts['len'],color='#008b87')
    ax.set_xlabel('Rekordy VCF'); ax.set_title('HG002 chr22 — przewidywane konsekwencje')
    ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(); plt.show()


def thread_counts(limit=None):
    cores = os.cpu_count() or 1
    limit = min(limit or cores, cores)
    return sorted({n for n in (1, 2, 4, 8, 16, limit) if n <= limit})


def measure_partitions(run, threads=None, repeats=2):
    """Czas wywołania run() przy różnej liczbie partycji DataFusion (polars-bio); zwraca {partycje: najlepszy czas}."""
    import polars_bio as pb
    results = []
    for n in threads or thread_counts():
        pb.set_option('datafusion.execution.target_partitions', str(n))
        for _ in range(repeats):
            start = time.perf_counter()
            value = run()
            seconds = time.perf_counter() - start
            results.append(dict(threads=n, seconds=seconds, result=value))
            number = f'{value:,}'.replace(',', ' ')
            print(f'partycje: {n} | {seconds:.2f} s | wynik: {number}', flush=True)
    pb.set_option('datafusion.execution.target_partitions', '1')
    assert len({r['result'] for r in results}) == 1, 'Wyniki różnią się między pomiarami.'
    return best_times(results)


def best_times(results):
    times = {}
    for r in results:
        times[r['threads']] = min(times.get(r['threads'], float('inf')), r['seconds'])
    return dict(sorted(times.items()))


def plot_speedup(series, title):
    """series: {etykieta: {wątki: czas}}"""
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for label, times in series.items():
        threads = list(times)
        axes[0].plot(threads, list(times.values()), 'o-', label=label)
        axes[1].plot(threads, [times[threads[0]] / t for t in times.values()], 'o-', label=label)
    all_threads = sorted({t for times in series.values() for t in times})
    axes[1].plot(all_threads, [t / all_threads[0] for t in all_threads], '--', color='grey', label='idealne')
    axes[0].set_ylabel('Czas [s]')
    axes[1].set_ylabel('Przyspieszenie względem 1 wątku')
    for ax in axes:
        ax.set_xlabel('Wątki / partycje')
        ax.set_xticks(all_threads)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend()
    fig.suptitle(title)
    fig.tight_layout()
    plt.show()


def timed(label, action):
    start = time.perf_counter()
    result = action()
    seconds = time.perf_counter() - start
    print(f'{label}: {seconds:.1f} s', flush=True)
    return result, seconds
