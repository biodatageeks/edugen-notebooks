# syntax=docker/dockerfile:1.7
# Obraz warsztatu "Big Data w genomice" (OMICS Data Science, ICM UW, 2026)
#   cz. 1 Apache Spark  ·  cz. 2 WDL + Cromwell  ·  cz. 3 polars-bio + vepyr
# Multi-arch: linux/amd64 (Linux, Windows/WSL, Mac Intel) i linux/arm64 (Mac Apple Silicon).
# Budowanie (kontekst = katalog 26Z):
#   docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile -t tgambin65716/omics-bigdata:2026.10 .

ARG BASE_IMAGE=quay.io/jupyter/minimal-notebook:ubuntu-24.04@sha256:2ccdd864bb67fb955d23d95b7656aea4e109fd07f51e4c61544c69d9336eefc8
ARG PY_PINS="polars-bio==0.36.0 polars==1.37.1 pyarrow==23.0.1 datafusion==53.0.0 vepyr==0.9.0 pysam==0.23.3"

# ---------------------------------------------------------------------------------------------
# Etap "data": pobranie i przygotowanie danych. Pliki nie zależą od architektury, więc etap
# uruchamiamy natywnie na maszynie budującej (bez emulacji) i kopiujemy do obu wariantów.
# ---------------------------------------------------------------------------------------------
FROM --platform=$BUILDPLATFORM ${BASE_IMAGE} AS data
ARG PY_PINS
# aarch64: polars-bio i vepyr (biblioteki natywne w Ruście) w jednym procesie wyczerpują domyślną
# rezerwę statycznego TLS glibc ("cannot allocate memory in static TLS block"); zwiększamy ją.
ENV GLIBC_TUNABLES=glibc.rtld.optional_static_tls=65536
USER root
RUN apt-get update && apt-get install -y --no-install-recommends bwa samtools tabix && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /opt/workshop/data && chown -R ${NB_UID}:${NB_GID} /opt/workshop
USER ${NB_UID}
RUN pip install --no-cache-dir ${PY_PINS} matplotlib psutil

COPY --chown=${NB_UID}:${NB_GID} docker/prepare_trio.sh docker/fastq_to_parquet.py /opt/workshop/build/
RUN bash /opt/workshop/build/prepare_trio.sh /opt/workshop/data/trio && \
    python /opt/workshop/build/fastq_to_parquet.py /opt/workshop/data/trio/fastq_parquet \
        /opt/workshop/data/trio/fastq/mother.fq /opt/workshop/data/trio/fastq/father.fq /opt/workshop/data/trio/fastq/son.fq

# Do przygotowania danych części 3 kopiujemy tylko manifest i skrypty, z których korzysta;
# pozostały kod części 3 dochodzi w obrazie docelowym (zmiany w nim nie wymuszają ponownego pobierania).
COPY --chown=${NB_UID}:${NB_GID} part3/data /opt/workshop/part3/data
COPY --chown=${NB_UID}:${NB_GID} part3/scripts/colab_helpers.py part3/scripts/prepare_real_data.py part3/scripts/prepare_intervals.py part3/scripts/vcf_header.py part3/scripts/analysis_tasks.py /opt/workshop/part3/scripts/
COPY --chown=${NB_UID}:${NB_GID} docker/prepare_part3.py /opt/workshop/build/
RUN python /opt/workshop/build/prepare_part3.py /opt/workshop/part3
COPY --chown=${NB_UID}:${NB_GID} docker/prepare_ailist.sh /opt/workshop/build/
RUN bash /opt/workshop/build/prepare_ailist.sh /opt/workshop/part3/ailist

# ---------------------------------------------------------------------------------------------
# Obraz docelowy
# ---------------------------------------------------------------------------------------------
FROM ${BASE_IMAGE}
ARG PY_PINS
ARG TARGETARCH
ARG GATK_VERSION=4.6.2.0
ARG CROMWELL_VERSION=87
ARG FASTQC_VERSION=0.12.1
ARG MULTIQC_VERSION=1.25.1
ARG PYSPARK_VERSION=4.0.4
# aarch64: polars-bio i vepyr (biblioteki natywne w Ruście) w jednym procesie wyczerpują domyślną
# rezerwę statycznego TLS glibc ("cannot allocate memory in static TLS block"); zwiększamy ją.
ENV GLIBC_TUNABLES=glibc.rtld.optional_static_tls=65536

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Java 17 (GATK 4.6, Spark 4, Cromwell) i narzędzia NGS z repozytorium Ubuntu: te same wersje
# na amd64 i arm64, bez kompilacji (bwa ze źródeł nie kompiluje się na ARM).
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless bwa samtools bcftools tabix bedtools perl procps less && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/lib/jvm/java-17-openjdk-${TARGETARCH} /usr/lib/jvm/java-17
# Wątek "process reaper" JVM ma bardzo mały stos; przy zwiększonej rezerwie TLS (GLIBC_TUNABLES wyżej)
# kończy się StackOverflowError i zawiesza Sparka/Cromwella. Wymuszamy domyślny rozmiar stosu.
ENV JAVA_HOME=/usr/lib/jvm/java-17 \
    JAVA_TOOL_OPTIONS=-Djdk.lang.processReaperUseDefaultStackSize=true

# GATK (bez pakietu Spark, którego nie używamy), FastQC, Cromwell + womtool
RUN cd /tmp && \
    curl -fsSL --retry 3 -o gatk.zip https://github.com/broadinstitute/gatk/releases/download/${GATK_VERSION}/gatk-${GATK_VERSION}.zip && \
    unzip -q gatk.zip && rm gatk.zip && \
    mv gatk-${GATK_VERSION} /opt/gatk && rm -f /opt/gatk/gatk-package-*-spark.jar && \
    ln -s /opt/gatk/gatk /usr/local/bin/gatk && \
    curl -fsSL --retry 3 -o fastqc.zip https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v${FASTQC_VERSION}.zip && \
    unzip -q fastqc.zip && rm fastqc.zip && chmod +x FastQC/fastqc && mv FastQC /opt/FastQC && \
    ln -s /opt/FastQC/fastqc /usr/local/bin/fastqc && \
    mkdir -p /opt/cromwell && \
    curl -fsSL --retry 3 -o /opt/cromwell/cromwell-${CROMWELL_VERSION}.jar https://github.com/broadinstitute/cromwell/releases/download/${CROMWELL_VERSION}/cromwell-${CROMWELL_VERSION}.jar && \
    curl -fsSL --retry 3 -o /opt/cromwell/womtool-${CROMWELL_VERSION}.jar https://github.com/broadinstitute/cromwell/releases/download/${CROMWELL_VERSION}/womtool-${CROMWELL_VERSION}.jar && \
    printf '#!/bin/bash\nexec java ${CROMWELL_JAVA_OPTS} -jar /opt/cromwell/cromwell-%s.jar "$@"\n' ${CROMWELL_VERSION} > /usr/local/bin/cromwell && \
    printf '#!/bin/bash\nexec java -jar /opt/cromwell/womtool-%s.jar "$@"\n' ${CROMWELL_VERSION} > /usr/local/bin/womtool && \
    chmod +x /usr/local/bin/cromwell /usr/local/bin/womtool
ENV CROMWELL_JAR=/opt/cromwell/cromwell-${CROMWELL_VERSION}.jar \
    WOMTOOL_JAR=/opt/cromwell/womtool-${CROMWELL_VERSION}.jar

# MultiQC we własnym venv: ma własne wymagania co do polars, niezależne od polars-bio
RUN python -m venv /opt/multiqc && \
    /opt/multiqc/bin/pip install --no-cache-dir multiqc==${MULTIQC_VERSION} && \
    ln -s /opt/multiqc/bin/multiqc /usr/local/bin/multiqc

# Jeden kernel Pythona (bez osobnego venv) ze wszystkimi bibliotekami warsztatu
USER ${NB_UID}
# Kontrola importu tylko na procesorze z AVX2 (polars, polars-bio i vepyr dla x86_64 go wymagają);
# przy budowaniu amd64 w emulacji na Apple Silicon (bez AVX) pomijamy ją.
RUN pip install --no-cache-dir ${PY_PINS} pyspark==${PYSPARK_VERSION} pandas matplotlib psutil && \
    if [ "$(uname -m)" = aarch64 ] || grep -q avx2 /proc/cpuinfo; then \
        python -c "import pyspark, polars_bio, vepyr, pysam, polars, pandas, matplotlib; print('python deps OK')"; \
    else echo "brak AVX2 (emulacja) – pomijam kontrolę importu"; fi

# Dane (trio GATK + część 3) i kod pomocniczy części 3
COPY --from=data --chown=${NB_UID}:${NB_GID} /opt/workshop /opt/workshop
COPY --chown=${NB_UID}:${NB_GID} part3/scripts /opt/workshop/part3/scripts
COPY --chown=${NB_UID}:${NB_GID} part3/reference /opt/workshop/part3/reference
ENV WORKSHOP_DATA=/opt/workshop/data \
    WORKSHOP_PART3=/opt/workshop/part3

# Materiały: kopiowane przy starcie do ~/work/omics-2026 (hook), bez nadpisywania zmian uczestnika
COPY --chown=${NB_UID}:${NB_GID} *.ipynb README.md /opt/workshop/materials/
COPY --chown=${NB_UID}:${NB_GID} img /opt/workshop/materials/img
COPY --chown=${NB_UID}:${NB_GID} dags /opt/workshop/materials/dags
USER root
COPY docker/hooks/50-copy-materials.sh /usr/local/bin/before-notebook.d/50-copy-materials.sh
COPY docker/workshop-check /usr/local/bin/workshop-check
RUN chmod +x /usr/local/bin/before-notebook.d/50-copy-materials.sh /usr/local/bin/workshop-check && \
    { echo "image built: $(date -u +%F)"; java -version 2>&1 | grep version; \
      bwa 2>&1 | grep Version; samtools --version | head -1; bcftools --version | head -1; \
      bedtools --version; /opt/gatk/gatk --version 2>/dev/null | head -1; fastqc --version; \
      multiqc --version; echo "cromwell ${CROMWELL_VERSION}"; \
      su ${NB_USER} -c "/opt/conda/bin/pip freeze"; } > /opt/workshop/VERSIONS.txt 2>&1
USER ${NB_UID}

EXPOSE 8888 4040
WORKDIR /home/${NB_USER}/work
CMD ["start-notebook.py", "--IdentityProvider.token=", "--ServerApp.root_dir=/home/jovyan/work"]
