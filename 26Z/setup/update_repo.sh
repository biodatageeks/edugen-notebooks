#!/usr/bin/env bash
# Aktualizacja klonu repozytorium do FETCH_HEAD z ochroną zmian uczestnika. Wywołuje go docker/workshop-sync
# (z katalogu głównego klonu), zawsze w wersji z nowego commita – logikę można poprawiać bez przebudowy obrazu.
#   - plik niezmieniony lokalnie: nowa wersja,
#   - plik zmieniony lokalnie: zostaje; nowa wersja trafia do <nazwa>.nowa.<roz>, a jeśli uczestnik pracuje już
#     w poprzedniej <nazwa>.nowa.<roz>, to do <nazwa>.nowa-<commit>.<roz>,
#   - plik usunięty lokalnie: przywracany w nowej wersji.
SUBDIR=${1:-26Z}
log() { echo "[warsztaty] $*"; }
old=$(git rev-parse HEAD)
new=$(git rev-parse FETCH_HEAD)
short=$(git rev-parse --short FETCH_HEAD)

conflicted=()
while IFS= read -r f; do
    [ -n "${f}" ] || continue
    if [ ! -e "${f}" ]; then
        # usunięty lokalnie: przywracamy starą wersję, reset wstawi nową
        git cat-file -e "${old}:${f}" 2>/dev/null && git checkout -q "${old}" -- "${f}"
    elif ! git cat-file -e "${old}:${f}" 2>/dev/null || ! git diff --quiet "${old}" -- "${f}"; then
        # zmieniony lokalnie (albo plik uczestnika o nazwie nowego pliku z repozytorium): odkładamy na bok
        mv "${f}" "${f}.moje-tmp"
        git cat-file -e "${old}:${f}" 2>/dev/null && git checkout -q "${old}" -- "${f}"
        conflicted+=("${f}")
    fi
done < <(git diff --name-only "${old}" "${new}" -- "${SUBDIR}")

updated=0
if git reset -q --keep "${new}"; then
    updated=1
    log "Zaktualizowano notatniki (commit ${short})."
else
    log "Nie udało się zaktualizować notatników – pracujesz na dotychczasowej wersji."
fi

for f in "${conflicted[@]}"; do
    if [ "${updated}" = 1 ] && [ -e "${f}" ]; then
        base="${f%.*}"; ext="${f##*.}"
        target="${base}.nowa.${ext}"
        # poprzednia .nowa była kopią wersji ${old}; jeśli uczestnik ją zmienił, nie nadpisujemy jej
        if [ -e "${target}" ] && ! git show "${old}:${f}" 2>/dev/null | cmp -s - "${target}"; then
            target="${base}.nowa-${short}.${ext}"
        fi
        cp "${f}" "${target}"
        log "Twoja wersja ${f} zostaje; nowa wersja z repozytorium: ${target}"
    fi
    mv "${f}.moje-tmp" "${f}"
done
