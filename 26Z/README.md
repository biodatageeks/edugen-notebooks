# Big Data w genomice · OMICS Data Science 2026

Warsztaty: **niedziela, 25 października 2026, 8 godzin z przerwami**. Prowadzący: Tomasz Gambin i Mateusz Dawidziuk.

| Część | Notatnik | Temat |
|---|---|---|
| 1 | `01_spark_fastq.ipynb` | Apache Spark: przetwarzanie rozproszone na przykładzie plików FASTQ, kubełki (gcloud) |
| 2 | `02_pipelines_wdl.ipynb` | Potoki przetwarzania: WDL i Cromwell, scatter-gather, sharding |
| 3 | `03_polars_bio_vepyr.ipynb` | polars-bio i vepyr: leniwe zapytania, równoległość, streaming, adnotacja wariantów |

Pracujemy na własnych laptopach, w kontenerze Dockera, który działa na macOS (Apple Silicon M1–M4 i Intel), Windows i Linuksie:
* **obraz Dockera** zawiera narzędzia: Spark, Cromwell, GATK, bwa, samtools, gcloud, polars-bio, vepyr, JupyterLab;
* **notatniki** kontener pobiera z tego repozytorium przy pierwszym uruchomieniu i aktualizuje przy każdym kolejnym;
* **dane** (około 1,2 GB) kontener pobiera z publicznych źródeł przy pierwszym uruchomieniu.

Wszystko trafia do folderu **`omics-2026`** w Twoim katalogu domowym.

---

## Przed zajęciami – zrób to dziś (około 30–45 minut)

Obraz (około 3,5 GB) i dane (około 1,2 GB) **pobierz wcześniej** – pobieranie przez 20 osób jednocześnie na sali nie zadziała. Notatniki otworzymy razem na zajęciach.

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

### 4. Sprawdź narzędzia

```
docker run --rm tgambin65716/omics-bigdata:2026.10 workshop-check
```

Test trwa około minuty. Każda linia powinna zaczynać się od `[OK]`, a na końcu powinien pojawić się napis **`Środowisko gotowe.`** Jeśli pojawi się `[BŁĄD]`, prześlij prowadzącym cały wynik tego polecenia jeszcze przed zajęciami.

### 5. Pobierz dane (około 1,2 GB)

Utwórz folder na pliki warsztatu i pobierz do niego dane. **macOS i Linux** (terminal):

```
mkdir "$HOME/omics-2026"
docker run --rm -v "$HOME/omics-2026:/home/jovyan/work" tgambin65716/omics-bigdata:2026.10 workshop-sync
```

**Windows** (PowerShell):

```
mkdir "$HOME/omics-2026"
docker run --rm -v "${HOME}\omics-2026:/home/jovyan/work" tgambin65716/omics-bigdata:2026.10 workshop-sync
```

W terminalu widać kolejne etapy `[dane] ...: OK`; zwykle trwa to **5–15 minut**. Na końcu powinien pojawić się napis **`[dane] Wszystkie dane gotowe`**, a polecenie się zakończy. Jeśli pobieranie się przerwie, uruchom polecenie ponownie – gotowe etapy nie są powtarzane.

W folderze `omics-2026` pojawi się też katalog `edugen-notebooks` z notatnikami – nie musisz go jeszcze otwierać. Na zajęciach kontener sam pobierze ich aktualną wersję.

---

## Uruchomienie

**macOS i Linux** (terminal):

```
docker run --rm -it --name omics -p 127.0.0.1:8888:8888 -p 127.0.0.1:4040:4040 -v "$HOME/omics-2026:/home/jovyan/work" tgambin65716/omics-bigdata:2026.10
```

**Windows** (PowerShell):

```
docker run --rm -it --name omics -p 127.0.0.1:8888:8888 -p 127.0.0.1:4040:4040 -v "${HOME}\omics-2026:/home/jovyan/work" tgambin65716/omics-bigdata:2026.10
```

Na początku kontener pobiera aktualną wersję notatników z repozytorium (i dane, jeśli nie zostały pobrane wcześniej). Następnie otwórz w przeglądarce **http://127.0.0.1:8888** – JupyterLab otworzy się w katalogu z notatnikami (`edugen-notebooks/26Z`). Notatniki uruchamiamy kernelem **Python 3 (ipykernel)** – jest jedynym kernelem w obrazie i wybiera się sam.

| Opcja | Znaczenie |
|---|---|
| `--name omics` | nazwa kontenera |
| `-p 127.0.0.1:8888:8888` | JupyterLab |
| `-p 127.0.0.1:4040:4040` | Spark UI (część 1): http://127.0.0.1:4040, gdy działa sesja Sparka |
| `-v "$HOME/omics-2026:/home/jovyan/work"` | folder `omics-2026` z Twojego dysku widoczny w kontenerze jako `~/work` |
| `--rm` | po zamknięciu usuwa kontener – **Twoje pliki zostają w folderze `omics-2026`** |

`127.0.0.1` sprawia, że JupyterLab jest dostępny tylko z Twojego komputera, a nie z sieci na sali. Zakończenie pracy: `Ctrl+C` w terminalu, w którym działa kontener.

---

## Twoje pliki: folder `omics-2026`

```
omics-2026/
├── edugen-notebooks/26Z/      notatniki, potoki WDL (dags/), skrypty – kopia tego repozytorium
│   ├── wyniki/                Twoje wyniki z części 1 i 3
│   └── cromwell-executions/   wyniki potoków z części 2
└── data/                      dane warsztatu (pobrane przy pierwszym uruchomieniu)
```

To zwykły folder na Twoim dysku – możesz go otwierać, kopiować i archiwizować jak każde inne pliki (Finder, Eksplorator plików). Wszystko, co zapiszesz w JupyterLabie, od razu jest na dysku.

**Aktualizacje notatników.** Przy każdym uruchomieniu kontener sprawdza, czy prowadzący nie poprawili materiałów (wymaga internetu; bez sieci pracujesz na dotychczasowej wersji). Twoja praca nie jest nadpisywana:

| Sytuacja | Co się dzieje |
|---|---|
| plik przez Ciebie niezmieniony, nowa wersja w repozytorium | plik zostaje zaktualizowany |
| plik przez Ciebie zmieniony (także przez uruchomienie komórek), nowa wersja w repozytorium | Twój plik zostaje bez zmian, nowa wersja pojawia się obok jako `*.nowa.ipynb` |
| kolejna nowa wersja, a plik `*.nowa.ipynb` jest nietknięty | `*.nowa.ipynb` zostaje zastąpiony najnowszą wersją |
| kolejna nowa wersja, a Ty pracujesz już w `*.nowa.ipynb` | Twój `*.nowa.ipynb` zostaje, najnowsza wersja pojawia się jako `*.nowa-<numer>.ipynb` |
| plik przez Ciebie usunięty | wraca w najnowszej wersji (tak można „zresetować” pojedynczy notatnik) |
| Twoje własne pliki i wyniki (`wyniki/`, `cromwell-executions/`, ...) | nigdy nie są zmieniane |

Komunikaty o aktualizacji widać w terminalu na początku (linie `[warsztaty] ...`).

**Jak zacząć od zera?** Zamknij kontener i usuń folder `omics-2026/edugen-notebooks` (dane w `omics-2026/data` mogą zostać – nie będą pobierane ponownie). Przy następnym uruchomieniu notatniki zostaną pobrane od nowa.

---

## Najczęstsze problemy

| Komunikat / objaw | Rozwiązanie |
|---|---|
| `Cannot connect to the Docker daemon` | uruchom Docker Desktop (Linux: `sudo systemctl start docker`) |
| `permission denied ... docker.sock` (Linux) | `sudo usermod -aG docker $USER`, wyloguj się i zaloguj; albo dodaj `sudo` przed `docker` |
| `Nie udało się pobrać repozytorium` albo `[dane] ...: BŁĄD` | brak internetu lub przerwane pobieranie – uruchom kontener ponownie; gotowe etapy nie są powtarzane |
| `port is already allocated` | port jest zajęty – zmień port na komputerze, np. `-p 127.0.0.1:8890:8888`, i otwórz http://127.0.0.1:8890 |
| `The container name "/omics" is already in use` | poprzedni kontener nadal działa lub nie został usunięty: `docker rm -f omics` |
| Linux: `Permission denied` przy zapisie w `omics-2026` | Twój identyfikator użytkownika (`id -u`) jest inny niż 1000 – dodaj do `docker run`: `--user root -e NB_UID=$(id -u) -e NB_GID=100` |
| Windows: błąd WSL 2 lub wirtualizacji | w PowerShellu jako administrator: `wsl --install`; włącz wirtualizację (Intel VT-x / AMD-V) w BIOS/UEFI |
| Windows: wolne działanie | pliki z dysku Windows są udostępniane kontenerowi wolniej – to normalne |
| kernel notatnika się restartuje, „Kernel died” | za mało pamięci – zwiększ *Memory* w Docker Desktop (Settings → Resources) |
| `Illegal instruction` w części 3 | bardzo stary procesor x86 bez instrukcji AVX2 (sprzed około 2013 r.) – pracuj w parze |

---

## Dla prowadzących

### Jak to działa

* `docker/Dockerfile` – obraz z samymi narzędziami (bez notatników i danych); zmieniamy go rzadko.
* `docker/workshop-sync` – uruchamiany przy każdym starcie kontenera z podmontowanym folderem `~/work` (przed JupyterLabem; bez `-v` nic nie pobiera, `WORKSHOP_SYNC=0` go wyłącza): klonuje to repozytorium (branch `feat/sharding-wdl`, tylko katalog `26Z`, sparse checkout) do `~/work/edugen-notebooks` albo je aktualizuje – logikę aktualizacji (`setup/update_repo.sh`) uruchamia w wersji z najnowszego commita, więc także ją można zmieniać bez przebudowy obrazu – a potem uruchamia **`26Z/setup/on_start.sh` z repozytorium**. Zmienne `WORKSHOP_REPO`, `WORKSHOP_BRANCH`, `WORKSHOP_DIR` pozwalają wskazać inne repozytorium, branch lub katalog.
* `setup/on_start.sh` – przygotowuje dane (`setup/prepare_data.sh` → `~/work/data`), jeśli ich brak albo zmieniła się `DATA_VERSION`. Zmiany w notatnikach, skryptach i danych **wystarczy wypchnąć do repozytorium** – uczestnicy dostaną je przy następnym uruchomieniu kontenera, bez pobierania nowego obrazu.

### Dane

| Katalog (w kontenerze) | Zawartość | Źródło |
|---|---|---|
| `~/work/data/trio` | trio matka–ojciec–syn: referencja b37 (fragment chr20) z indeksem BWA, BAM, FASTQ, FASTQ jako Parquet | publiczny kubełek `gs://gatk-tutorials/workshop_1906/2-germline` (`setup/prepare_trio.sh`) |
| `~/work/data/part3` | GIAB HG002 v4.2.1 (GRCh38), GENCODE 47, cache Ensembl 116 (chr22), FASTA chr22 | `part3/data/real_sources.json` (adresy i sumy SHA-256) |
| `~/work/data/part3/ailist` | zbiory AIList ex-rna (~10 mln mapowań direct RNA) i ex-anno (~1,2 mln elementów GENCODE) – benchmark równoległości | archiwum `databio.zip` z [dokumentacji polars-bio](https://biodatageeks.org/polars-bio/supplement/), suma SHA-256 w `setup/prepare_ailist.sh` |

Wersje narzędzi i bibliotek: `/opt/workshop/VERSIONS.txt` w kontenerze.

### Tagi obrazu

| Tag | Zawartość |
|---|---|
| `tgambin65716/omics-bigdata:2026.10`, `:latest` | `linux/amd64` + `linux/arm64`; `docker pull` wybiera architekturę |
| `tgambin65716/omics-bigdata:2026.10-amd64`, `:2026.10-arm64` | jedna architektura (diagnostyka) |

### Budowanie i publikacja obrazu

```
cd 26Z
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile \
  -t tgambin65716/omics-bigdata:2026.10 -t tgambin65716/omics-bigdata:latest --push .
```

Przy budowaniu `linux/amd64` w emulacji na Apple Silicon kontrola importu polars-bio/vepyr jest pomijana (emulacja nie ma AVX2).

Dwie zmienne środowiskowe obrazu są konieczne na arm64 (Apple Silicon):
* `GLIBC_TUNABLES=glibc.rtld.optional_static_tls=65536` – bez tego polars-bio i vepyr nie dają się zaimportować w jednym procesie (`cannot allocate memory in static TLS block`);
* `JAVA_TOOL_OPTIONS=-Djdk.lang.processReaperUseDefaultStackSize=true` – zwiększona rezerwa TLS zabiera miejsce na bardzo małym stosie wątku „process reaper” JVM, przez co Spark i Cromwell zawieszały się (`StackOverflowError`). Stąd linia `Picked up JAVA_TOOL_OPTIONS` przy każdym uruchomieniu Javy.
