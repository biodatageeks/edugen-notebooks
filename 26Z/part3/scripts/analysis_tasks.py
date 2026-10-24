"""Operations shown in the notebook; native tool parallelism only."""

def vcf_query(path):
    import polars as pl
    import polars_bio as pb
    return (
        pb.scan_vcf(path, info_fields=[], format_fields=[], use_zero_based=False)
        .filter(pl.col('chrom').is_in(['chr' + str(i) for i in range(1, 23)]))
        .filter((pl.col('ref').str.len_chars() == 1) &
                (pl.col('alt').str.len_chars() == 1))
        .select('chrom', 'start', 'ref', 'alt', 'qual', 'filter')
    )


def overlap_query(variants_path, exons_path):
    import polars as pl
    import polars_bio as pb
    # Współdzielony indeks eksonów; równoległe przeszukiwanie w silniku natywnym.
    pb.set_option('datafusion.optimizer.repartition_joins', 'false')
    variants = pl.scan_parquet(variants_path)
    exons = pl.scan_parquet(exons_path)
    for table in (variants, exons):
        table.config_meta.set(coordinate_system_zero_based=True)
    return pb.overlap(exons, variants, suffixes=('_exon', '_variant')).select(
        pl.col('chrom_variant').alias('chrom'),
        pl.col('start_variant').alias('start'),
        pl.col('end_variant').alias('end'),
        pl.col('ref_variant').alias('ref'),
        pl.col('alt_variant').alias('alt'),
        pl.col('gene_id_exon').alias('gene_id'),
        pl.col('gene_exon').alias('gene'),
        pl.col('start_exon').alias('exon_start'),
        pl.col('end_exon').alias('exon_end'),
    )
