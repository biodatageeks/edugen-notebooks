#!/usr/bin/env bash
# Uruchamiany przez obraz przy każdym starcie kontenera, po pobraniu/aktualizacji repozytorium
# (katalog roboczy: 26Z). Przygotowuje dane, jeśli jeszcze ich nie ma albo zmieniła się ich wersja.
DATA="${WORKSHOP_DATA:-${HOME}/work/data}"
DATA_VERSION=1

if [ "$(cat "${DATA}/.gotowe" 2>/dev/null)" = "${DATA_VERSION}" ]; then
    echo "[warsztaty] Dane gotowe: ~/work/data"
    exit 0
fi
echo "[warsztaty] Pobieram i przygotowuję dane warsztatu (około 1,2 GB, zwykle 5–15 minut; tylko za pierwszym razem)."
echo "[warsztaty] Przy zwykłym uruchomieniu JupyterLab wystartuje po zakończeniu."
bash setup/prepare_data.sh "${DATA}" && echo "${DATA_VERSION}" > "${DATA}/.gotowe"
