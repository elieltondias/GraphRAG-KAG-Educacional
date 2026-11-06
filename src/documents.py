import hashlib
import io
import re
from collections import defaultdict
from pypdf import PdfReader
from src.embeddings import Embedder, normalize


def chunks(text, size=1100):
    text = re.sub(r'\s+',' ',text).strip()
    start = 0
    while start < len(text):
        end = min(start+size,len(text))
        if end < len(text):
            cut = text.rfind(' ',start+size//2,end)
            if cut > start:
                end = cut
        yield text[start:end].strip()
        start = end
        while start < len(text) and text[start].isspace():
            start += 1


def resolve_mentions(text, catalog):
    aliases = defaultdict(set)
    for row in catalog:
        for alias in [row['name'],row.get('alias')]:
            key = normalize(alias or '').strip()
            if len(key)>=3:
                aliases[key].add(row['id'])
    normalized = normalize(text)
    mentions = set()
    ambiguous = []
    for alias,ids in aliases.items():
        if re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',normalized):
            if len(ids)==1:
                mentions.update(ids)
            else:
                ambiguous.append(alias)
    return sorted(mentions), sorted(ambiguous)


def ingest_document(store, name, content):
    meta = store.metadata()
    embedder = Embedder(store.settings.embedding,store.settings.model)
    if meta.get('status')!='pronto' or meta.get('embedding_model')!=embedder.identity:
        raise ValueError('Importe os microdados com o mesmo modelo antes dos documentos.')
    if len(content)>15*1024*1024:
        raise ValueError('Limite de 15 MB por documento.')
    if name.lower().endswith('.pdf'):
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages)>100:
            raise ValueError('Limite de 100 páginas.')
        pages = [(i+1,p.extract_text() or '') for i,p in enumerate(reader.pages)]
    else:
        pages = [(1,content.decode('utf-8-sig'))]
    if not any(text.strip() for _,text in pages):
        raise ValueError('Documento sem texto. PDFs digitalizados precisam de OCR antes da importação.')
    digest = hashlib.sha256(content).hexdigest()
    doc_id = 'doc:'+digest
    props = {'id':doc_id,'kind':'Documento','name':name,'name_norm':normalize(name),'source_file':name,'sha256':digest}
    store.upsert_nodes('Documento',[{'id':doc_id,'props':props}])
    catalog = store.query("MATCH (n:Entity) WHERE n.kind IN ['IES','Curso','Municipio','UF','Regiao'] RETURN n.id AS id,n.name AS name,n.SG_IES AS alias")
    count = mentions_count = 0
    ambiguities = set()
    for page,text in pages:
        for part,chunk in enumerate(chunks(text)):
            chunk_id = f'{doc_id}:p{page}:{part}'
            mentions,ambiguous = resolve_mentions(chunk,catalog)
            ambiguities.update(ambiguous)
            props = {'id':chunk_id,'kind':'Trecho','name':f'{name} · página {page} · trecho {part+1}',
                     'name_norm':normalize(name),'text':chunk,'search_text':normalize(chunk),'source_file':name,'page':page}
            store.upsert_nodes('Trecho',[{'id':chunk_id,'props':props}])
            store.upsert_edges('CONTEM',[{'source':doc_id,'target':chunk_id}])
            if mentions:
                store.upsert_edges('MENCIONA',[{'source':chunk_id,'target':i} for i in mentions])
            store.vectors([{'id':chunk_id,'vector':embedder.encode([chunk])[0]}])
            count += 1
            mentions_count += len(mentions)
    store.wait_ready()
    return {'documento':name,'sha256':digest,'trechos':count,'mencoes':mentions_count,'ambiguidades_nao_vinculadas':sorted(ambiguities),
            'metodo':'NER por dicionário e RE de menção; não infere relações factuais por coocorrência.'}
