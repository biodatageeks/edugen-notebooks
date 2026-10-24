#!/bin/bash
# Przy starcie kontenera synchronizuje materiały warsztatu z obrazu do ~/work/omics-2026:
# - brakujące pliki są kopiowane,
# - pliki niezmienione przez uczestnika są aktualizowane do wersji z obrazu,
# - jeśli uczestnik zmienił plik, a w obrazie jest nowsza wersja, zapisujemy ją obok jako *.nowa.<rozszerzenie>.
src=/opt/workshop/materials
target="${HOME}/work/omics-2026"
manifest="${target}/.materials.sha256"
mkdir -p "${target}"
(
cd "${src}" || exit 0
find . -type f | while read -r f; do
    dst="${target}/${f#./}"
    new=$(sha256sum "${f}" | cut -d' ' -f1)
    if [ ! -e "${dst}" ]; then
        mkdir -p "$(dirname "${dst}")" && cp "${f}" "${dst}"
        continue
    fi
    cur=$(sha256sum "${dst}" | cut -d' ' -f1)
    [ "${cur}" = "${new}" ] && continue
    old=$(awk -v f="${f}" '$2 == f {print $1}' "${manifest}" 2>/dev/null)
    if [ "${cur}" = "${old}" ]; then
        cp "${f}" "${dst}"
    else
        cp "${f}" "${dst%.*}.nowa.${dst##*.}"
    fi
done
find . -type f -exec sha256sum {} + > "${manifest}"
) 2>/dev/null || true
