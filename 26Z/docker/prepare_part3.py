"""Pobranie i przygotowanie danych części 3 (HG002, GENCODE 47, cache Ensembl 116 chr22, FASTA chr22)
przy budowie obrazu. Te same funkcje notatnik wywołuje przy starcie; pliki z poprawną sumą
SHA-256 nie są pobierane ponownie."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'scripts'))

import colab_helpers as wh  # noqa: E402

wh.setup()
