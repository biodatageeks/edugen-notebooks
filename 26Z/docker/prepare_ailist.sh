#!/usr/bin/env bash
# Rzeczywiste zbiory przedziałów z publikacji AIList (Feng, Ratan, Sheffield, Bioinformatics 2019), w formacie
# Parquet z benchmarków polars-bio: ex-rna (~10 mln mapowań odczytów direct RNA) i ex-anno (~1,2 mln elementów
# adnotacji GENCODE). Z archiwum (419 MB) zostawiamy tylko te dwa zbiory (~91 MB).
set -euo pipefail
OUT=${1:-/opt/workshop/part3/ailist}
URL="https://drive.usercontent.google.com/download?id=1lctmude31mSAh9fWjI60K1bDrbeDPGfm&export=download&confirm=t"
SHA256=dd582741c51c6bd6bccf31daee0c45f8e64a1499decbcdd1525ecef50ccaa114
tmp=$(mktemp -d)
curl -fsSL --retry 5 -o "$tmp/databio.zip" "$URL"
echo "$SHA256  $tmp/databio.zip" | sha256sum -c -
unzip -q "$tmp/databio.zip" 'databio/ex-rna/*.parquet' 'databio/ex-anno/*.parquet' -d "$tmp"
mkdir -p "$OUT"
mv "$tmp/databio/ex-rna" "$tmp/databio/ex-anno" "$OUT/"
rm -rf "$tmp"
