# Porównanie VEP i vepyr na Linuksie

Wykres porównania jest osadzony na początku C5 notatnika 03; powstał z danych w `summary.tsv` i `vep_summary.tsv` (sam wykres nie wykonuje benchmarku).

## Dane źródłowe

- `vep_summary.tsv`: dostarczona tabela z `vepyr/performance-tests/vep/outputs/116/merged_fork_scaling/summary.tsv`; Ensembl VEP 116.
- `summary.tsv`: dostarczona tabela z `vepyr/performance-tests/vepyr/outputs/116/merged_worker_scaling/summary.tsv`; vepyr 0.3.0.

Ten sam zestaw jest używany do panelu C w `vepyr/paper/figure1/build_performance.py`. [Projekt vepyr / performance-tests](https://github.com/biodatageeks/vepyr/tree/master/performance-tests).

## Warunki i interpretacja

Linux/x86-64; HG002 chr1–22 (4 096 123 rekordy), GRCh38, merged cache 116 (Ensembl + RefSeq), pełna adnotacja z HGVS, wynik jako nieskompresowany VCF na SSD. Pomiary z 23 sierpnia 2026, pojedyncze uruchomienia.

Porównanie używa **czasu całego procesu**: `elapsed_seconds` dla VEP i `process_elapsed_wall` dla vepyra. Nie używa krótszego `annotation_seconds`. Przy ustawieniu 8: 6326 s / 187,67 s = 33,7×. Oś Y jest logarytmiczna. Pojedyncze uruchomienia nie pozwalają oszacować zmienności; nie jest to pomiar Colaba.

Model CPU i pamięć maszyny nie są udokumentowane w dostarczonym podsumowaniu. Liczba workerów nie jest ścisłym limitem wszystkich wątków programu. Zgodność liczby rekordów nie dowodzi identyczności każdej adnotacji. W ćwiczeniu Colab używamy vepyra 0.5.0 i mniejszego zbioru chr22 z bazą Ensembl 116; nie zestawiamy bezpośrednio tych czasów.
