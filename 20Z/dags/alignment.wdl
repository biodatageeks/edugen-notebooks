version 1.0

workflow alignment_pipeline {
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
    }

    # Etap 1: Uruchomienie BWA MEM
    call BwaMem {
        input:
            ref_fasta = ref_fasta,
            ref_fasta_amb = ref_fasta_amb,
            ref_fasta_ann = ref_fasta_ann,
            ref_fasta_bwt = ref_fasta_bwt,
            ref_fasta_pac = ref_fasta_pac,
            ref_fasta_sa = ref_fasta_sa,
            fastq = mother_fastq
    }

    # Etap 2: Konwersja SAM do BAM
    call SamToBam {
        input:
            sam_file = BwaMem.sam_file
    }

    # Określenie pliku wynikowego całego potoku
    output {
        File bam_file = SamToBam.bam_file
        File bai_file = SamToBam.bai_file
    }
}

# Informacje do uruchomienia etapu BWA MEM
task BwaMem {
    # Określenie plików wejściowych dla etapu BWA MEM
    input {
        File ref_fasta
        File ref_fasta_amb
        File ref_fasta_ann
        File ref_fasta_bwt
        File ref_fasta_pac
        File ref_fasta_sa
        File fastq
    }

    # Uruchomienie programu
    command {
        bwa mem -p ~{ref_fasta} ~{fastq} > mother.sam
    }

    # Określenie pliku wynikowego dla etapu BWA MEM
    output {
        File sam_file = "mother.sam"
    }
}

# Task for converting SAM to BAM
task SamToBam {
    # Określenie plików wejściowych dla etapu konwersji
    input {
        File sam_file
    }

    # Wykonanie komendy konwersji
    command {
        samtools view -b ~{sam_file} | samtools addreplacerg -r '@RG\tID:mother\tSM:mother' - | samtools sort -o mother.bam
        samtools index mother.bam 
    }

    # Określenie pliku wynikowego dla etapu konwersji
    output {
        File bam_file = "mother.bam"
        File bai_file = "mother.bam.bai"
    }
}
