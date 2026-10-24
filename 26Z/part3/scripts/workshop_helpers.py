"""Pomiary równoległości na laptopie uczestnika (wersja dockerowa warsztatu)."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def thread_counts(limit=None):
    cores = os.cpu_count() or 1
    limit = min(limit or cores, cores)
    return sorted({n for n in (1, 2, 4, 8, 16, limit) if n <= limit})


def measure_threads(task, inputs, threads=None, repeats=1):
    """Uruchamia to samo zapytanie przy różnej liczbie wątków, każdy pomiar w osobnym procesie."""
    results = []
    for n in threads or thread_counts():
        env = os.environ.copy()
        env.update(POLARS_MAX_THREADS=str(n), RAYON_NUM_THREADS=str(n), OMP_NUM_THREADS=str(n))
        for _ in range(repeats):
            with tempfile.NamedTemporaryFile(suffix='.json') as out:
                cmd = [sys.executable, str(SCRIPTS / 'measure_threads.py'), task, str(n), out.name,
                       *map(str, inputs)]
                done = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
                if done.returncode:
                    raise RuntimeError('Pomiar przerwany:\n' + done.stderr[-3000:])
                record = json.loads(Path(out.name).read_text())
            results.append(record)
            print(f"{task}: {n} wątk.: {record['seconds']:.2f} s, {record['rows']:,} wierszy".replace(',', ' '),
                  flush=True)
    assert len({r['fingerprint'] for r in results}) == 1, 'Wyniki różnią się między pomiarami.'
    return results


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
