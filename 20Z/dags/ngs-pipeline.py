import json

from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

import subprocess
from pyspark.sql import SparkSession
from pyseqtender import SeqTenderAlignment
from pyseqtender import SeqTenderAnnotation

default_args = {
    'owner': 'airflow',
}
@dag(default_args=default_args, schedule_interval=None, start_date=days_ago(2))
def ngs_pipeline():
    
    bucket = f"gs://edugen-lab-agaszmurlo"
    @task()
    def mapping():
        
        spark = SparkSession \
        .builder \
        .config('spark.driver.memory','1g') \
        .config('spark.executor.memory', '2g') \
        .getOrCreate()

        reads_file_path = f"{bucket}/fastq/mother.fastq"
        ref_path = "/mnt/data/mapping/ref/ref.fasta"
        command = f'bwa mem -p {ref_path} - | samtools fixmate -m - - | samtools sort  | samtools markdup -r -S - -  | samtools addreplacerg  -r "ID:S1" -r "SM:S1"  -r "PL:ILLUMINA" - | samtools view -b -'    
        seq_aligner = SeqTenderAlignment(spark, reads_file_path, command)
        alignments_rdd = seq_aligner.pipe_reads()
        bam_file_path = f"{bucket}/bam/mother10.bam"
        seq_aligner.save_reads(bam_file_path, alignments_rdd)
        spark.stop()
        return bam_file_path
    
    @task()
    def variant_calling(bam_file):
        vcf_file = f"{bucket}/vcf/mother10.vcf"
        command=f"""
        gatk-hpt-caller-k8s.sh \
          --conf "spark.executor.memory=1g" \
          --conf "spark.driver.memory=1g" \
          --conf "spark.executor.instances=2" \
          --conf "spark.hadoop.fs.gs.block.size=8388608" \
          -R /mnt/data/mapping/ref/ref.fasta \
          -I {bucket}/bam/mother10.bam \
          -O {vcf_file}
        """
        subprocess.run(command, shell=True)
        return vcf_file

    @task()
    def annotation(vcf_file):
        
        spark = SparkSession \
        .builder \
        .config('spark.driver.memory','1g') \
        .config('spark.executor.memory', '2g') \
        .getOrCreate()
        seq_anno = SeqTenderAnnotation(spark)
        
        vcf_path=f"{bucket}/vcf/mother_dec.vcf"
        cache_dir = "/mnt/data/annotation/102.0"
        vep_version="102"
        command = f"""vep --dir {cache_dir} --pick_allele --format vcf --no_stats --force_overwrite  --uniprot  -cache --vcf -offline --assembly GRCh37
                -o stdout """.replace("\n   ", "")

        annotated = seq_anno.pipe_variants(vcf_path, command)
        var_anno_path = f"{bucket}/vcf/mother_anno.vcf"
        seq_anno.save_variants (var_anno_path, annotated)
        spark.stop()
        return var_anno_path
    
    bam_file = mapping()
    vcf = variant_calling(bam_file)
    ann_vcf = annotation(vcf)

ngs_dag = ngs_pipeline()