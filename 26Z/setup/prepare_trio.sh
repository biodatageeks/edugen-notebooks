#!/usr/bin/env bash
# Dane trio (mother/father/son) z publicznego kubełka gs://gatk-tutorials (GATK workshop 1906):
# referencja b37 (fragment chr20), BAM -> FASTQ (pary przeplecione, dla bwa mem -p), indeks BWA.
set -euo pipefail
OUT=${1:-$HOME/work/data/trio}
BASE=https://storage.googleapis.com/gatk-tutorials/workshop_1906/2-germline
mkdir -p "$OUT/ref" "$OUT/bam" "$OUT/fastq"

for f in ref.fasta ref.fasta.fai ref.dict; do
    curl -fsSL --retry 3 -o "$OUT/ref/$f" "$BASE/ref/$f"
done

for s in mother father son; do
    curl -fsSL --retry 3 -o "$OUT/bam/$s.bam" "$BASE/bams/$s.bam"
    curl -fsSL --retry 3 -o "$OUT/bam/$s.bam.bai" "$BASE/bams/$s.bai"
    # pary odczytów obok siebie (/1, /2), bez singletonów
    samtools collate -u -O "$OUT/bam/$s.bam" \
        | samtools fastq -N -s /dev/null -0 /dev/null - > "$OUT/fastq/$s.fq"
done

bwa index "$OUT/ref/ref.fasta"
(cd "$OUT" && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
