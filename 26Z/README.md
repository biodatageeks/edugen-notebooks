# Big Data w genomice · OMICS Data Science 2026

Warsztaty: **niedziela, 25 października 2026, 8 godzin z przerwami**. Prowadzący: Tomasz Gambin i Mateusz Dawidziuk.

| Część | Notatnik | Temat |
|---|---|---|
| 1 | `01_spark_fastq.ipynb` | Apache Spark: przetwarzanie rozproszone na przykładzie plików FASTQ, kubełki |
| 2 | `02_pipelines_wdl.ipynb` | Potoki przetwarzania: WDL i Cromwell, scatter-gather, sharding |
| 3 | `03_polars_bio_vepyr.ipynb` | polars-bio i vepyr: leniwe zapytania, równoległość, streaming, adnotacja wariantów |

Pracujemy na własnych laptopach. Wszystkie programy, biblioteki i dane są w jednym obrazie Dockera, który działa na macOS (Apple Silicon M1–M4 i Intel), Windows i Linuksie.

---

## Przed zajęciami – zrób to dziś (około 30 minut)

Obraz ma około 3,4 GB. Pobranie go na sali, przez 20 osób jednocześnie, nie zadziała – **pobierz go wcześniej**.

### 1. Zainstaluj Dockera

* **macOS:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) – wybierz wersję dla swojego procesora (menu Apple → *Ten Mac*: „Apple M…” albo „Intel”).
* **Windows 10/11:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) z backendem **WSL 2** (instalator go zaproponuje). Wymaga włączonej wirtualizacji w BIOS/UEFI.
* **Linux:** [Docker Engine](https://docs.docker.com/engine/install/). Żeby nie pisać `sudo` przed każdym poleceniem: `sudo usermod -aG docker $USER`, potem wyloguj się i zaloguj ponownie.

### 2. Uruchom Dockera i przydziel mu zasoby

Uruchom Docker Desktop (ikona wieloryba na pasku). W **Settings → Resources** ustaw:
* **Memory:** co najmniej **6 GB** (zalecane 8 GB),
* **CPUs:** wszystkie dostępne,
* wolne miejsce na dysku: co najmniej **20 GB**.

Na Linuksie kontener korzysta z zasobów komputera bez dodatkowych ustawień.

### 3. Pobierz obraz

W terminalu (macOS/Linux) lub w PowerShellu (Windows):

```
docker pull tgambin65716/omics-bigdata:2026.10
```

### 4. Sprawdź środowisko

```
docker run --rm tgambin65716/omics-bigdata:2026.10 workshop-check
```

Test trwa około minuty. Każda linia powinna zaczynać się od `[OK]`, a na końcu powinien pojawić się napis **`Środowisko gotowe.`** Linie `Picked up JAVA_TOOL_OPTIONS` są normalne. Przykładowy wynik:

```
Architektura: aarch64 | CPU: 8 | RAM: 7 GiB
  [OK]   Java                         openjdk version "17.0.20.1" 2026-08-18
  ...
  [OK]   Cromwell                     workflow Succeeded
Środowisko gotowe.
```

Jeśli pojawi się `[BŁĄD]`, prześlij prowadzącym cały wynik tego polecenia jeszcze przed zajęciami.

### 5. Otwórz JupyterLab

Uruchom kontener (polecenie poniżej, w sekcji *Uruchomienie*) i sprawdź, że w przeglądarce widzisz katalog `omics-2026` z trzema notatnikami. Potem zamknij kontener (`Ctrl+C` w terminalu).

---

## Uruchomienie

```
docker run --rm -it --name omics -p 127.0.0.1:8888:8888 -p 127.0.0.1:4040:4040 -v omics-2026:/home/jovyan/work tgambin65716/omics-bigdata:2026.10
```

Polecenie jest takie samo w terminalu macOS/Linux i w PowerShellu na Windows. Następnie otwórz w przeglądarce **http://127.0.0.1:8888/lab** i wejdź do katalogu `omics-2026`. Notatniki uruchamiamy kernelem **Python 3 (ipykernel)** – jest jedynym kernelem w obrazie i wybiera się sam.

| Opcja | Znaczenie |
|---|---|
| `--name omics` | nazwa kontenera (przydaje się do kopiowania plików, patrz niżej) |
| `-p 127.0.0.1:8888:8888` | JupyterLab |
| `-p 127.0.0.1:4040:4040` | Spark UI (część 1): http://127.0.0.1:4040, gdy działa sesja Sparka |
| `-v omics-2026:/home/jovyan/work` | wolumen z Twoimi plikami (patrz niżej) |
| `--rm` | po zamknięciu usuwa kontener – **ale nie wolumen z Twoimi plikami** |

`127.0.0.1` sprawia, że JupyterLab jest dostępny tylko z Twojego komputera, a nie z sieci na sali. Zakończenie pracy: `Ctrl+C` w terminalu, w którym działa kontener.

---

## Twoje pliki: wolumen `omics-2026`

Notatniki, wyniki obliczeń i Twoje własne pliki są w **wolumenie Dockera** o nazwie `omics-2026`. W JupyterLabie widzisz go jako katalog `omics-2026`. Wolumen przechowuje Docker – nie jest to zwykły folder widoczny w Finderze czy Eksploratorze.

**Co przetrwa zamknięcie kontenera?** Wszystko, co jest w wolumenie: notatniki z Twoimi zmianami i wynikami, katalog `wyniki/`, `cromwell-executions/` z części 2. Przy kolejnym uruchomieniu wszystko będzie na miejscu.

**Czy restart nadpisze moje notatniki?** Nie.

| Sytuacja przy starcie kontenera | Co się dzieje |
|---|---|
| ten sam obraz | nic się nie zmienia |
| nowa wersja obrazu (po `docker pull`), plik przez Ciebie niezmieniony | plik zostaje zaktualizowany do nowej wersji |
| nowa wersja obrazu, plik przez Ciebie zmieniony (także przez uruchomienie komórek) | Twój plik zostaje bez zmian, nowa wersja pojawia się obok jako `*.nowa.ipynb` |
| Twoje własne pliki i wyniki | nigdy nie są zmieniane |

### Jak wyjąć pliki z wolumenu?

* **Pojedyncze pliki:** w JupyterLabie kliknij plik prawym przyciskiem → **Download**.
* **Cały katalog:** gdy kontener działa, w **drugim** oknie terminala wpisz:
  ```
  docker cp omics:/home/jovyan/work/omics-2026 ./omics-2026-kopia
  ```
  Kopia pojawi się w katalogu, w którym jesteś w terminalu.
* **Wgranie pliku do wolumenu:** przeciągnij plik do panelu plików JupyterLaba (lub przycisk **Upload**).
* **Terminal wewnątrz kontenera:** w JupyterLabie *File → New → Terminal* (pliki są w `~/work/omics-2026`).

### Jak zacząć od zera?

Zamknij kontener i usuń wolumen. **Usuwa to wszystkie Twoje pliki i wyniki** – najpierw zrób kopię.

```
docker volume rm omics-2026
```

Przy następnym uruchomieniu notatniki zostaną skopiowane od nowa.

---

## Najczęstsze problemy

| Komunikat / objaw | Rozwiązanie |
|---|---|
| `Cannot connect to the Docker daemon` | uruchom Docker Desktop (Linux: `sudo systemctl start docker`) |
| `permission denied ... docker.sock` (Linux) | `sudo usermod -aG docker $USER`, wyloguj się i zaloguj; albo dodaj `sudo` przed `docker` |
| `port is already allocated` | port jest zajęty – zmień port na komputerze, np. `-p 127.0.0.1:8890:8888`, i otwórz http://127.0.0.1:8890/lab |
| `The container name "/omics" is already in use` | poprzedni kontener nadal działa lub nie został usunięty: `docker rm -f omics` |
| Windows: błąd WSL 2 lub wirtualizacji | w PowerShellu jako administrator: `wsl --install`; włącz wirtualizację (Intel VT-x / AMD-V) w BIOS/UEFI |
| kernel notatnika się restartuje, „Kernel died” | za mało pamięci – zwiększ *Memory* w Docker Desktop (Settings → Resources) |
| `Illegal instruction` w części 3 | bardzo stary procesor x86 bez instrukcji AVX2 (sprzed około 2013 r.) – pracuj w parze |

---

## Dla prowadzących

### Dane w obrazie

| Katalog | Zawartość | Źródło |
|---|---|---|
| `/opt/workshop/data/trio` | trio matka–ojciec–syn: referencja b37 (fragment chr20) z indeksem BWA, BAM, FASTQ, FASTQ jako Parquet | publiczny kubełek `gs://gatk-tutorials/workshop_1906/2-germline` |
| `/opt/workshop/part3` | GIAB HG002 v4.2.1 (GRCh38), GENCODE 47, cache Ensembl 116 (chr22), FASTA chr22 | `part3/data/real_sources.json` (adresy i sumy SHA-256) |
| `/opt/workshop/part3/ailist` | zbiory AIList ex-rna (~10 mln mapowań direct RNA) i ex-anno (~1,2 mln elementów GENCODE) – benchmark równoległości | archiwum `databio.zip` z [dokumentacji polars-bio](https://biodatageeks.org/polars-bio/supplement/), suma SHA-256 w `docker/prepare_ailist.sh` |
| `/opt/workshop/materials` | notatniki, `dags/`, `img/`, ten plik – kopiowane przy starcie do `~/work/omics-2026` (`docker/hooks/50-copy-materials.sh`) | katalog `26Z/` tego repozytorium |

Wersje narzędzi i bibliotek: `/opt/workshop/VERSIONS.txt` w kontenerze.

### Tagi obrazu

| Tag | Zawartość |
|---|---|
| `tgambin65716/omics-bigdata:2026.10`, `:latest` | `linux/amd64` + `linux/arm64`; `docker pull` wybiera architekturę |
| `tgambin65716/omics-bigdata:2026.10-amd64`, `:2026.10-arm64` | jedna architektura (diagnostyka) |

### Budowanie i publikacja

```
cd 26Z
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile \
  -t tgambin65716/omics-bigdata:2026.10 -t tgambin65716/omics-bigdata:latest --push .
```

Etap `data` (pobieranie i przygotowanie danych) wykonuje się raz, natywnie na maszynie budującej. Przy budowaniu `linux/amd64` w emulacji na Apple Silicon kontrola importu polars-bio/vepyr jest pomijana (emulacja nie ma AVX2).

Dwie zmienne środowiskowe obrazu są konieczne na arm64 (Apple Silicon):
* `GLIBC_TUNABLES=glibc.rtld.optional_static_tls=65536` – bez tego polars-bio i vepyr nie dają się zaimportować w jednym procesie (`cannot allocate memory in static TLS block`);
* `JAVA_TOOL_OPTIONS=-Djdk.lang.processReaperUseDefaultStackSize=true` – zwiększona rezerwa TLS zabiera miejsce na bardzo małym stosie wątku „process reaper” JVM, przez co Spark i Cromwell zawieszały się (`StackOverflowError`). Stąd linia `Picked up JAVA_TOOL_OPTIONS` przy każdym uruchomieniu Javy.
