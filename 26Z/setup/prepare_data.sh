#!/usr/bin/env bash
# Pobiera i przygotowuje dane warsztatu z publicznych źródeł (około 1,2 GB do pobrania).
# Każdy etap pomija się, jeśli jego dane są już gotowe; można go bezpiecznie uruchomić ponownie.
#   bash setup/prepare_data.sh [katalog_danych]     (domyślnie ~/work/data)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DATA=${1:-${HOME}/work/data}
mkdir -p "${DATA}"
status=0

step() {  # step <znacznik> <opis> <polecenie...>
    local marker=$1 label=$2; shift 2
    if [ -f "${marker}" ]; then echo "[dane] ${label}: gotowe"; return 0; fi
    echo "[dane] ${label}..."
    if "$@"; then mkdir -p "$(dirname "${marker}")" && touch "${marker}"; echo "[dane] ${label}: OK"
    else echo "[dane] ${label}: BŁĄD"; return 1; fi
}

trio() {
    bash "${HERE}/prepare_trio.sh" "${DATA}/trio" &&
        python "${HERE}/fastq_to_parquet.py" "${DATA}/trio/fastq_parquet" \
            "${DATA}/trio/fastq/mother.fq" "${DATA}/trio/fastq/father.fq" "${DATA}/trio/fastq/son.fq"
}

step "${DATA}/trio/.gotowe" "Trio GATK (b37, fragment chr20): referencja, indeks BWA, BAM, FASTQ" trio || status=1
step "${DATA}/part3/.gotowe" "HG002, GENCODE 47, cache Ensembl 116 chr22, FASTA chr22" \
    python "${HERE}/prepare_part3.py" "${DATA}/part3" || status=1
step "${DATA}/part3/ailist/.gotowe" "AIList ex-rna × ex-anno (benchmark równoległości)" \
    bash "${HERE}/prepare_ailist.sh" "${DATA}/part3/ailist" || status=1

if [ ${status} -eq 0 ]; then echo "[dane] Wszystkie dane gotowe: ${DATA}"
else echo "[dane] Część danych nie została przygotowana – uruchom ponownie (kontener lub ten skrypt)."; fi
exit ${status}
