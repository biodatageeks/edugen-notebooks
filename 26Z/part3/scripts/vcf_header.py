"""Keep indexed VCF header contigs aligned with actual indexed sequences."""
from pathlib import Path
import gzip, hashlib, json, re

def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def align_header_with_index(source):
    """Remove unused contig declarations, preserving every variant record.

    DataFusion's indexed reader can schedule all header contigs. A VCF may
    legitimately declare empty contigs absent from its tabix index; some reader
    versions fail on those regions. Reheadering and reindexing the working copy
    avoids relying on predicate pushdown to hide that mismatch.
    """
    import pysam
    import pysam.bcftools
    source = Path(source)
    with pysam.TabixFile(str(source)) as tabix:
        indexed = list(tabix.contigs)
    with pysam.VariantFile(str(source)) as vcf:
        declared = list(vcf.header.contigs)
    if set(declared) == set(indexed):
        return source
    if not indexed or not set(indexed).issubset(declared):
        raise ValueError('Nieprawidłowy indeks lub brak deklaracji chromosomów w VCF.')
    target = source.with_name(source.name.removesuffix('.vcf.gz') + '.indexed.vcf.gz')
    index = Path(str(target) + '.tbi')
    metadata = Path(str(target) + '.json')
    source_hash = digest(source)
    if target.exists() and index.exists() and metadata.exists():
        saved = json.loads(metadata.read_text())
        if (saved.get('source_sha256') == source_hash
                and saved.get('output_sha256') == digest(target)
                and saved.get('index_sha256') == digest(index)):
            return target
    print(f'Przygotowanie nagłówka VCF: {len(declared)} deklaracji → {len(indexed)} sekwencji obecnych w indeksie.', flush=True)
    header_lines = []
    allowed = set(indexed)
    with gzip.open(source, 'rt') as f:
        for line in f:
            if not line.startswith('#'):
                break
            match = re.match(r'##contig=<ID=([^,>]+)', line)
            if match and match.group(1) not in allowed:
                continue
            header_lines.append(line)
    header_path = target.with_suffix('.header.txt')
    partial = target.with_name(target.name + '.preparing.vcf.gz')
    partial_index = Path(str(partial) + '.tbi')
    try:
        header_path.write_text(''.join(header_lines))
        # bcftools copies the record body; it does not re-annotate or filter it.
        pysam.bcftools.reheader('-h', str(header_path), '-o', str(partial), str(source), catch_stdout=False)
        pysam.tabix_index(str(partial), preset='vcf', force=True)
        with pysam.VariantFile(str(partial)) as vcf, pysam.TabixFile(str(partial)) as tabix:
            assert set(vcf.header.contigs) == set(tabix.contigs) == allowed
        partial.replace(target)
        partial_index.replace(index)
        metadata.write_text(json.dumps({
            'source_sha256': source_hash, 'output_sha256': digest(target),
            'index_sha256': digest(index), 'indexed_contigs': indexed,
            'removed_contigs': [c for c in declared if c not in allowed],
        }, indent=2))
    finally:
        for scratch in [header_path, partial, partial_index]:
            scratch.unlink(missing_ok=True)
    return target
