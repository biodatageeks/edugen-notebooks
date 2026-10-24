"""Pomiary równoległości na laptopie uczestnika (wersja dockerowa warsztatu)."""
import os
import time


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
