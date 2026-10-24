# Skalowanie polars-bio — wykres z dokumentacji

Wykres osadzony w C3 notatnika 03 to niezmieniony wykres **Thread scalability (dataset 8-7)** z [publikacji projektu z 20 lutego 2026](https://biodatageeks.org/polars-bio/blog/2026/02/20/interval-operations-benchmark--update-february-2026/#thread-scalability-dataset-8-7).

- Biblioteka w opublikowanym pomiarze: **polars-bio 0.24.0**. Ćwiczenia instalują **0.36.0**.
- Dane AIList: para **8-7**, ex-rna (około 9,945 mln przedziałów) × ex-anno (około 1,194 mln). Artykuł podaje 307 184 634 przecięcia dla współrzędnych od 1.
- Oś X: 1, 2, 4, 8 wątków. Oś Y: czas rzeczywisty w sekundach. Linie przerywane pokazują idealne skalowanie względem czasu przy jednym wątku.
- W warsztacie omawiamy niebieską serię **Overlap**: **4,03 s → 0,74 s**, opublikowane przyspieszenie **5,43×**. Czasy w tabeli są zaokrąglone, dlatego ich iloraz nie odtwarza dokładnie opublikowanego współczynnika.
- Artykuł nie podaje modelu CPU, RAM, liczby powtórzeń ani pełnych granic stopera dla tego wykresu. Nie przypisujemy mu konfiguracji z innych publikacji. To ilustracja skalowania konkretnego opublikowanego eksperymentu, a nie przewidywanie czasu w Colabie ani pomiar naszego HG002 × GENCODE.

Źródło obrazu: [plik w repozytorium polars-bio](https://github.com/biodatageeks/polars-bio/blob/a1f724f87cf09c248587f37cf923fea6bee777af/docs/blog/posts/figures/benchmark-operations-2026-02/polars_bio_scalability_8_7.png).
Zweryfikowano 2026-10-04 względem drzewa GitHub: `a1f724f87cf09c248587f37cf923fea6bee777af`.
Git blob SHA-1: `89633eb3773c3d7e334c17dfd09898eacb554ce9`.
SHA-256: `abb35f12ec18b4029a4bfaa8d729d026333477b21c96c00eab3d7486cbce3369`.

Obraz jest osadzony w sekcji C3 notebooka i na slajdzie 10. Nie wymaga uruchomienia kodu ani dostępu uczestnika do repozytorium.
