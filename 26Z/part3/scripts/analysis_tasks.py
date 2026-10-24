"""Zapytanie vcf_query (to samo co w notatniku 03), używane przez skrypty przygotowania danych i pomiaru pamięci."""

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

