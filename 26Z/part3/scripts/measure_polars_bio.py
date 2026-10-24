"""VCF-to-Parquet memory experiment, fixed parallelism, fresh process."""
import json, resource, sys, time
from pathlib import Path
import polars as pl
import polars_bio as pb
from analysis_tasks import vcf_query
from rss_monitor import RssMonitor

def main():
    source, mode, output = sys.argv[1:]
    if mode not in ('collect_write', 'sink'):
        raise ValueError('Supported modes: collect_write, sink')
    n = 1
    pb.set_option('datafusion.execution.target_partitions', str(n))
    query = vcf_query(source)
    parquet = Path(output).with_suffix('.parquet')
    rss_unit = 2**30 if sys.platform == 'darwin' else 2**20
    lifetime_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rss_unit
    with RssMonitor() as memory:
        cpu_start = time.process_time()
        start = time.perf_counter()
        if mode == 'collect_write':
            df = query.collect(engine='streaming')
            df.write_parquet(parquet, compression='zstd', row_group_size=5000)
        elif mode == 'sink':
            query.sink_parquet(parquet, compression='zstd', row_group_size=5000)
        seconds = time.perf_counter() - start
        cpu_seconds = time.process_time() - cpu_start
    lifetime_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rss_unit
    # Validation happens AFTER the time and peak-memory measurements.
    if mode == 'sink':
        df = pl.read_parquet(parquet)
    result = dict(parallelism=n, mode=mode, seconds=seconds,
                  cpu_seconds=cpu_seconds, **memory.result,
                  lifetime_peak_rss_before_gib=lifetime_before,
                  lifetime_peak_rss_after_gib=lifetime_after,
                  records=df.height, columns=df.width,
                  fingerprints=[str(df.hash_rows(seed=s).sum()) for s in (42, 97)],
                  polars_threads=pl.thread_pool_size())
    Path(output).write_text(json.dumps(result, indent=2))
    if parquet.exists():
        parquet.unlink()  # only this experiment's scratch output
    print(json.dumps(result))

if __name__ == '__main__':
    main()
