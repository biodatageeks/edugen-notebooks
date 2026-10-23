version 1.0

# Import zadań z wcześniejszego potoku - wywołujemy je jako align.BwaMem i align.SamToBam
import "alignment.wdl" as align

workflow sharded_variant_calling {
    # Określenie plików wejściowych dla całego potoku
    input {
        File ref_fasta
        File ref_dict
        File ref_fasta_fai
        File ref_fasta_amb
        File ref_fasta_ann
        File ref_fasta_bwt
        File ref_fasta_pac
        File ref_fasta_sa
        File mother_fastq
        # Liczba fragmentów (shardów), na które dzielimy genom
        Int scatter_count = 4
    }

    # Etap 1: Uruchomienie BWA MEM (zadanie z alignment.wdl)
    call align.BwaMem {
        input:
            ref_fasta = ref_fasta,
            ref_fasta_amb = ref_fasta_amb,
            ref_fasta_ann = ref_fasta_ann,
            ref_fasta_bwt = ref_fasta_bwt,
            ref_fasta_pac = ref_fasta_pac,
            ref_fasta_sa = ref_fasta_sa,
            fastq = mother_fastq
    }

    # Etap 2: Konwersja SAM do BAM (zadanie z alignment.wdl)
    call align.SamToBam {
        input:
            sam_file = BwaMem.sam_file
    }

    # Etap 3: Podział genomu referencyjnego na scatter_count fragmentów
    call SplitIntervals {
        input:
            ref_fasta_fai = ref_fasta_fai,
            scatter_count = scatter_count
    }

    # Etap 4 (scatter): Wykrywanie wariantów osobno w każdym fragmencie genomu
    scatter (interval_file in SplitIntervals.interval_files) {
        call HaplotypeCallerShard {
            input:
                ref_fasta = ref_fasta,
                ref_fasta_fai = ref_fasta_fai,
                ref_dict = ref_dict,
                bam_file = SamToBam.bam_file,
                bai_file = SamToBam.bai_file,
                intervals = interval_file
        }
    }

    # Etap 5 (gather): Scalenie plików VCF ze wszystkich shardów
    # Poza blokiem scatter HaplotypeCallerShard.vcf_file ma typ Array[File]
    call MergeVcfs {
        input:
            vcf_files = HaplotypeCallerShard.vcf_file
    }

    # Określenie plików wynikowych całego potoku
    output {
        Array[File] interval_files = SplitIntervals.interval_files
        Array[File] shard_vcfs = HaplotypeCallerShard.vcf_file
        File merged_vcf = MergeVcfs.merged_vcf
    }
}

# Podział każdego kontigu na scatter_count równych części
task SplitIntervals {
    input {
        File ref_fasta_fai
        Int scatter_count
    }

    # Plik .fai zawiera w kolumnie 1 nazwę kontigu, a w kolumnie 2 jego długość.
    # i-ta część każdego kontigu trafia do pliku intervals/shard_00i.bed
    # (format BED: kontig, początek liczony od 0, koniec)
    command <<<
        mkdir intervals
        awk -v n=~{scatter_count} '{
            size = int($2 / n) + 1
            for (i = 0; i < n; i++) {
                start = i * size
                end = (i + 1) * size
                if (end > $2) end = $2
                out = sprintf("intervals/shard_%03d.bed", i)
                if (start < end) printf "%s\t%d\t%d\n", $1, start, end > out
            }
        }' ~{ref_fasta_fai}
    >>>

    # glob() zwraca tablicę wszystkich plików pasujących do wzorca
    output {
        Array[File] interval_files = glob("intervals/*.bed")
    }
}

# Wykrywanie wariantów tylko w regionach z jednego pliku BED
task HaplotypeCallerShard {
    input {
        File ref_fasta
        File ref_fasta_fai
        File ref_dict
        File bam_file
        File bai_file
        File intervals
    }

    # Nazwa shardu na podstawie nazwy pliku BED, np. shard_000
    String shard_name = basename(intervals, ".bed")

    command <<<
        gatk --java-options "-Xmx1g" HaplotypeCaller \
            -R ~{ref_fasta} \
            -I ~{bam_file} \
            -L ~{intervals} \
            -O ~{shard_name}.vcf
    >>>

    output {
        File vcf_file = "~{shard_name}.vcf"
    }
}

# Scalenie plików VCF z poszczególnych shardów w jeden plik
task MergeVcfs {
    input {
        Array[File] vcf_files
    }

    # ~{sep=" -I " vcf_files} wstawia wszystkie pliki z tablicy oddzielone tekstem " -I "
    command <<<
        gatk --java-options "-Xmx1g" MergeVcfs \
            -I ~{sep=" -I " vcf_files} \
            -O merged.vcf
    >>>

    output {
        File merged_vcf = "merged.vcf"
    }
}
