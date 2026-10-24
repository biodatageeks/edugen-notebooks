"""Pinned public GIAB input and Ensembl chr22 cache. No patient uploads or credentials."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import gzip,hashlib,json,urllib.request,shutil

def sha256(path):
 with open(path,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def download(url,path,expected):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and sha256(path)==expected: return path
 partial=path.with_name(path.name+'.part')
 with urllib.request.urlopen(url,timeout=120) as r,partial.open('wb') as w: shutil.copyfileobj(r,w)
 if sha256(partial)!=expected: raise RuntimeError(f'Niezgodna suma kontrolna: {path.name}')
 partial.replace(path)
 return path

def prepare_fasta(folder,source):
 import pysam
 folder=Path(folder)
 compressed=download(source['url'],folder/'GRCh38_chr22.fa.gz',source['sha256'])
 fasta=folder/'GRCh38_chr22.fa'
 if not fasta.exists() or sha256(fasta)!=source['fasta_sha256']:
  partial=fasta.with_name(fasta.name+'.part')
  with gzip.open(compressed,'rb') as r,partial.open('wb') as w: shutil.copyfileobj(r,w)
  if sha256(partial)!=source['fasta_sha256']:
   raise RuntimeError('Niezgodna suma kontrolna rozpakowanego FASTA.')
  partial.replace(fasta)
 pysam.faidx(str(fasta))
 with pysam.FastaFile(str(fasta)) as reference:
  if reference.references!=[source['contig']] or reference.lengths!=[source['length']]:
   raise RuntimeError('FASTA nie zawiera oczekiwanej sekwencji chr22 / GRCh38.')
 return fasta

def prepare(root):
 import pysam
 from vcf_header import align_header_with_index
 root=Path(root); manifest=json.loads((root/'data/real_sources.json').read_text())
 folder=root/'real_data'; folder.mkdir(exist_ok=True)
 source=manifest['vcf']; vcf=folder/'HG002.vcf.gz'
 print('Dane GIAB: pobranie 156 MB (raz), następnie wybór chr22.',flush=True)
 download(source['url'],vcf,source['sha256'])
 download(source['url']+'.tbi',str(vcf)+'.tbi',source['index_sha256'])
 vcf=align_header_with_index(vcf)
 chr22=folder/'HG002_chr22.vcf.gz'
 with pysam.VariantFile(str(vcf)) as src, pysam.VariantFile(str(chr22),'wz',header=src.header) as out:
  n=0
  for record in src.fetch('chr22'): out.write(record); n+=1
 assert n==manifest['chr22_records'],f'Nieoczekiwana liczba rekordów: {n}'
 pysam.tabix_index(str(chr22),preset='vcf',force=True)
 chr22=align_header_with_index(chr22)
 cache=root/'vepyr_cache'; total=sum(x['size'] for x in manifest['cache']['files'])
 print(f'Cache Ensembl 116 / GRCh38, tylko chr22: {total/1e6:.0f} MB (raz).',flush=True)
 def fetch(f): return download(f['url'],cache/f['path'],f['sha256'])
 with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(fetch,manifest['cache']['files']))
 import vepyr
 identity=vepyr.cache_contig_identity(str(cache),'chr22',expected_cache_version='116')
 print('Sekwencja referencyjna GRCh38 chr22: 12 MB FASTA po kompresji (raz).',flush=True)
 reference_fasta=prepare_fasta(folder,manifest['reference_fasta'])
 (folder/'preparation.json').write_text(json.dumps({'records':n,'cache_identity':identity,'input_sha256':sha256(chr22),'reference_fasta_sha256':sha256(reference_fasta)},indent=2))
 print(f'Gotowe: {n:,} rekordów chr22, vepyr {vepyr.__version__}.',flush=True)
 return vcf,chr22,cache,reference_fasta
