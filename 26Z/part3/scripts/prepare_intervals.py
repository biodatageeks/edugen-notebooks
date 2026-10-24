"""Prepare real SNV/exon interval tables once, outside benchmark timers."""
from pathlib import Path
import gzip
import json
import re


def exon_table(gtf):
    """Unique exon coordinates per gene; GTF closed positions -> half-open."""
    import polars as pl
    autosomes = {'chr' + str(i) for i in range(1, 23)}
    rows = []
    with gzip.open(gtf, 'rt') as stream:
        for line in stream:
            if line.startswith('#'):
                continue
            fields = line.rstrip('\n').split('\t')
            if len(fields) != 9 or fields[2] != 'exon' or fields[0] not in autosomes:
                continue
            attrs = dict(re.findall(r'(\w+) "([^"]+)"', fields[8]))
            rows.append((fields[0], int(fields[3]) - 1, int(fields[4]),
                         attrs['gene_id'], attrs.get('gene_name', attrs['gene_id'])))
    return pl.DataFrame(rows, schema=['chrom', 'start', 'end', 'gene_id', 'gene'],
                        orient='row').unique().sort('chrom', 'start', 'end', 'gene_id')


def prepare(root, vcf):
    import polars as pl
    import polars_bio as pb
    import pyarrow.parquet as pq
    from analysis_tasks import vcf_query
    from prepare_real_data import download, sha256

    root = Path(root)
    source = json.loads((root/'data/real_sources.json').read_text())['exons']
    folder = root/'real_data'
    folder.mkdir(parents=True, exist_ok=True)
    gtf = folder/'gencode.v47.basic.annotation.gtf.gz'
    print('GENCODE 47 / GRCh38: pobranie 34 MB i przygotowanie przedziałów.', flush=True)
    download(source['url'], gtf, source['sha256'])
    variants = folder/'HG002_snv_intervals.parquet'
    exons = folder/'gencode47_exons.parquet'
    metadata = folder/'interval_preparation.json'
    inputs = {'vcf_sha256': sha256(vcf), 'gtf_sha256': source['sha256'],
              'coordinates': '0-based half-open', 'preparation_version': 1}
    if metadata.exists() and variants.exists() and exons.exists():
        saved = json.loads(metadata.read_text())
        if (saved.get('inputs') == inputs and
            saved.get('variants_sha256') == sha256(variants) and
            saved.get('exons_sha256') == sha256(exons)):
            print(f"Gotowe tabele: {saved['variants']:,} SNV i {saved['exons']:,} przedziałów eksonów.", flush=True)
            return variants, exons

    pb.set_option('datafusion.execution.target_partitions', '1')
    vcf_query(str(vcf)).select(
        'chrom', (pl.col('start').cast(pl.Int64) - 1).alias('start'),
        pl.col('start').cast(pl.Int64).alias('end'), 'ref', 'alt',
    ).sink_parquet(variants, compression='zstd', row_group_size=100000)
    features = exon_table(gtf)
    assert features.height == source['unique_exons'], 'Nieoczekiwana liczba eksonów.'
    features.write_parquet(exons, compression='zstd', row_group_size=50000)
    n = pq.read_metadata(variants).num_rows
    assert n == source['hg002_snv_records'], 'Nieoczekiwana liczba SNV.'
    metadata.write_text(json.dumps(dict(
        inputs=inputs, variants=n, exons=features.height,
        variants_sha256=sha256(variants), exons_sha256=sha256(exons),
    ), indent=2))
    print(f'Gotowe tabele: {n:,} SNV i {features.height:,} przedziałów eksonów.', flush=True)
    return variants, exons
