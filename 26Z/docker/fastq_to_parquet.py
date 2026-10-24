"""FASTQ -> Parquet dla części Spark: jeden plik na próbkę, kolumny sample_id, name, seq, qual."""
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def read_fastq(path):
    names, seqs, quals = [], [], []
    with open(path) as stream:
        while True:
            header = stream.readline()
            if not header:
                break
            seq = stream.readline().rstrip('\n')
            stream.readline()
            qual = stream.readline().rstrip('\n')
            names.append(header[1:].rstrip('\n'))
            seqs.append(seq)
            quals.append(qual)
    return names, seqs, quals


def main(out_dir, *fastq_files):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fastq in map(Path, fastq_files):
        sample = fastq.stem
        names, seqs, quals = read_fastq(fastq)
        table = pa.table({'sample_id': [sample] * len(names), 'name': names,
                          'seq': seqs, 'qual': quals})
        pq.write_table(table, out / f'{sample}.parquet', compression='zstd',
                       row_group_size=50_000)
        print(f'{sample}: {table.num_rows} odczytów')


if __name__ == '__main__':
    main(*sys.argv[1:])
