"""Pobranie i przygotowanie danych części 3 (HG002, GENCODE 47, cache Ensembl 116 chr22, FASTA chr22).
Te same funkcje notatnik 03 wywołuje przy starcie (workshop_helpers.setup); pliki z poprawną sumą
SHA-256 nie są pobierane ponownie.
    python setup/prepare_part3.py <katalog_danych_części_3>"""
import shutil
import sys
from pathlib import Path

part3 = Path(__file__).resolve().parents[1] / 'part3'
root = Path(sys.argv[1])
(root / 'data').mkdir(parents=True, exist_ok=True)
shutil.copy(part3 / 'data' / 'real_sources.json', root / 'data' / 'real_sources.json')
sys.path.insert(0, str(part3 / 'scripts'))

from prepare_intervals import prepare as prepare_intervals  # noqa: E402
from prepare_real_data import prepare  # noqa: E402

vcf, annotation_vcf, cache, reference_fasta = prepare(root)
prepare_intervals(root, vcf)
