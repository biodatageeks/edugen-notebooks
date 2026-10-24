"""Czas jednego zapytania polars-bio przy zadanej liczbie partycji/wątków; świeży proces na pomiar."""
import json
import sys
import time

import polars as pl
import polars_bio as pb
from analysis_tasks import overlap_query, vcf_query


def main():
    task, n, output, *inputs = sys.argv[1:]
    n = int(n)
    pb.set_option('datafusion.execution.target_partitions', str(n))
    if task == 'overlap':
        query = overlap_query(*inputs)
    elif task == 'vcf':
        query = vcf_query(inputs[0])
    elif task == 'ailist':
        # ex-rna × ex-anno: ~307 mln par; liczymy je strumieniowo, bez gromadzenia w RAM
        cols = ['contig', 'pos_start', 'pos_end']
        rna, anno = (pl.scan_parquet(f'{inputs[0]}/{name}/*.parquet') for name in ('ex-rna', 'ex-anno'))
        for table in (rna, anno):
            table.config_meta.set(coordinate_system_zero_based=False)
        query = pb.overlap(rna, anno, cols1=cols, cols2=cols).select(pl.len().alias('pairs'))
    else:
        raise ValueError('Supported tasks: overlap, vcf, ailist')
    start = time.perf_counter()
    df = query.collect(engine='streaming') if task == 'ailist' else query.collect()
    seconds = time.perf_counter() - start
    rows = df['pairs'][0] if task == 'ailist' else df.height
    result = dict(task=task, threads=n, seconds=seconds, rows=rows,
                  fingerprint=str(df.hash_rows(seed=42).sum()))
    with open(output, 'w') as stream:
        json.dump(result, stream)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
