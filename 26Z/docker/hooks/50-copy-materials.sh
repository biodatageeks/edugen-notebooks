#!/bin/bash
# Przy starcie kontenera kopiuje materiały warsztatu do ~/work/omics-2026, nie nadpisując
# plików, które uczestnik już zmienił (np. w zamontowanym katalogu).
target="${HOME}/work/omics-2026"
mkdir -p "${target}"
cp -r --update=none /opt/workshop/materials/. "${target}/" 2>/dev/null || true
