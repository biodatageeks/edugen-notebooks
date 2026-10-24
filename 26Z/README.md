# Big Data w genomice · OMICS Data Science 2026

Warsztaty (8 godzin, jeden dzień): Tomasz Gambin i Mateusz Dawidziuk.

| Część | Notatnik | Prowadzi |
|---|---|---|
| 1. Apache Spark: przetwarzanie rozproszone na przykładzie FASTQ, kubełki | `01_spark_fastq.ipynb` | TG |
| 2. Potoki przetwarzania: WDL i Cromwell, scatter-gather, sharding | `02_pipelines_wdl.ipynb` | MD |
| 3. polars-bio i vepyr: leniwe zapytania, równoległość, streaming, adnotacja | `03_polars_bio_vepyr.ipynb` | TG |

Wszystkie narzędzia, biblioteki i dane są w jednym obrazie Dockera. Działa na macOS (Apple Silicon M1–M4 i Intel), Windows (WSL 2) i Linuksie; `docker pull` sam wybiera wariant (`linux/arm64` lub `linux/amd64`).

## Przed zajęciami (najlepiej dzień wcześniej)

1. **Zainstaluj Dockera**
   * macOS i Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows: z backendem WSL 2).
   * Linux: [Docker Engine](https://docs.docker.com/engine/install/).
2. **Przydziel zasoby** (Docker Desktop → Settings → Resources): co najmniej **6 GB RAM** (zalecane 8 GB), wszystkie rdzenie CPU, około **15 GB** wolnego miejsca na dysku.
3. **Pobierz obraz** (kilka GB – nie zostawiaj tego na salę):
   ```
   docker pull tgambin65716/omics-bigdata:2026.10
   ```
4. **Sprawdź środowisko** (około minuty; na końcu powinno pojawić się `Środowisko gotowe.`):
   ```
   docker run --rm tgambin65716/omics-bigdata:2026.10 workshop-check
   ```

## Uruchomienie

```
docker run --rm -it -p 127.0.0.1:8888:8888 -p 127.0.0.1:4040:4040 -v omics-2026:/home/jovyan/work tgambin65716/omics-bigdata:2026.10
```

Polecenie jest takie samo w terminalu macOS/Linux i w PowerShellu na Windows. Następnie otwórz w przeglądarce **http://127.0.0.1:8888/lab**. Materiały są w katalogu `omics-2026`.

* `-p 127.0.0.1:8888:8888` – JupyterLab; `-p 127.0.0.1:4040:4040` – Spark UI (część 1). Adres `127.0.0.1` sprawia, że serwer jest dostępny tylko z Twojego komputera, a nie z sieci na sali.
* `-v omics-2026:/home/jovyan/work` – wolumen Dockera: Twoje zmiany i wyniki przetrwają zamknięcie kontenera. Przy kolejnym uruchomieniu nie nadpisujemy zmienionych plików.
* Zakończenie pracy: `Ctrl+C` w terminalu. Pliki pobierzesz z JupyterLaba (prawy przycisk → *Download*).

## Dane w obrazie

| Katalog | Zawartość | Źródło |
|---|---|---|
| `/opt/workshop/data/trio` | trio matka–ojciec–syn: referencja b37 (fragment chr20) z indeksem BWA, BAM, FASTQ, FASTQ jako Parquet | publiczny kubełek `gs://gatk-tutorials/workshop_1906/2-germline` |
| `/opt/workshop/part3` | GIAB HG002 v4.2.1 (GRCh38), GENCODE 47, cache Ensembl 116 (chr22), FASTA chr22 | `part3/data/real_sources.json` (adresy i sumy SHA-256) |
| `/opt/workshop/part3/ailist` | zbiory AIList ex-rna (~10 mln mapowań direct RNA) i ex-anno (~1,2 mln elementów GENCODE) – benchmark równoległości | archiwum `databio.zip` z [dokumentacji polars-bio](https://biodatageeks.org/polars-bio/supplement/), suma SHA-256 w `docker/prepare_ailist.sh` |

Wersje narzędzi i bibliotek: `/opt/workshop/VERSIONS.txt` w kontenerze.

## Budowanie obrazu

```
cd 26Z
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile -t tgambin65716/omics-bigdata:2026.10 --push .
```

Etap `data` (pobieranie i przygotowanie danych) wykonuje się raz, natywnie na maszynie budującej.

Dwie zmienne środowiskowe obrazu są konieczne na arm64 (Apple Silicon):
* `GLIBC_TUNABLES=glibc.rtld.optional_static_tls=65536` – bez tego polars-bio i vepyr nie dają się zaimportować w jednym procesie (`cannot allocate memory in static TLS block`);
* `JAVA_TOOL_OPTIONS=-Djdk.lang.processReaperUseDefaultStackSize=true` – zwiększona rezerwa TLS zabiera miejsce na bardzo małym stosie wątku „process reaper” JVM, przez co Spark i Cromwell zawieszały się (`StackOverflowError`). Każde uruchomienie Javy wypisuje więc linię `Picked up JAVA_TOOL_OPTIONS`.
