import os
import uuid
from dataclasses import replace
from pathlib import Path
import pytest
from src.config import Settings
from src.store import Store
from src.ingest import ingest_lpg
from src.documents import ingest_document
from src.retrieval import retrieve, structured, Filters, deterministic_answer

pytestmark=pytest.mark.skipif(os.getenv('RUN_INTEGRATION')!='1',reason='Use RUN_INTEGRATION=1 com FalkorDB ativo')
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def store():
    settings=replace(Settings(),graph='teste_'+uuid.uuid4().hex,embedding='hash')
    store=Store(settings)
    ingest_lpg(store,ROOT/'data/sample/lpg','amostra',progress=lambda _:None)
    yield store
    store.graph.delete()


def test_real_counts_and_idempotency(store):
    facts=structured(store,Filters())
    assert facts['totals']['ofertas']==300
    assert facts['totals']['cursos']==270
    assert facts['totals']['instituicoes']==50
    before=store.stats()
    ingest_lpg(store,ROOT/'data/sample/lpg','amostra',progress=lambda _:None)
    assert store.stats()==before
    assert store.query('MATCH ()-[r]->() RETURN count(r) AS n')[0]['n']==3101


def test_hybrid_multi_hop_and_provenance(store):
    result=retrieve(store,'Cursos em João Pessoa',Filters(municipio='João Pessoa'))
    assert result['facts']['totals']['ofertas']==67
    assert result['facts']['totals']['matriculas']==2039
    assert result['graph']['edges'] and result['evidence']
    assert any(e['path'].count('→')+e['path'].count('←')>=2 for e in result['evidence'])
    assert all(n['source'] for n in result['graph']['nodes'])
    assert all(n['pagerank']>0 for n in result['graph']['nodes'])
    assert 'Amostra' in deterministic_answer(result)
    assert any('db.idx.vector.queryNodes' in q['cypher'] for q in result['trace'])
    assert any('db.idx.fulltext.queryNodes' in q['cypher'] for q in result['trace'])


def test_query_injection_does_not_mutate(store):
    rows=structured(store,Filters(curso="') DETACH DELETE n //"))
    assert rows['totals']['ofertas']==0
    assert structured(store,Filters())['totals']['ofertas']==300


def test_constraints_enforced(store):
    from redis.exceptions import ResponseError
    with pytest.raises(ResponseError):
        store.query("CREATE (:Entity {id:'2024:uf_25'})",write=True)
    with pytest.raises(ResponseError):
        store.query("CREATE (:Entity {kind:'SemID'})",write=True)


def test_documents_mentions_and_text_retrievable(store):
    content='João Pessoa é mencionado neste documento didático de teste.'.encode()
    first=ingest_document(store,'teste.txt',content)
    second=ingest_document(store,'teste.txt',content)
    assert first['sha256']==second['sha256']
    assert first['mencoes']==1
    result=retrieve(store,'documento didático João Pessoa',mode='lexical')
    assert any(e['snippets'] for e in result['evidence'])
    assert store.query('MATCH (n:Trecho) RETURN count(n) AS n')[0]['n']==1


def test_scope_or_embedding_mismatch_rejected(store):
    with pytest.raises(ValueError):
        ingest_lpg(store,ROOT/'data/sample/lpg','completa',progress=lambda _:None)


def test_vector_ranking_uses_distance_ascending():
    from src.retrieval import VECTOR
    s=Store(replace(Settings(),graph='vetor_'+uuid.uuid4().hex,embedding='hash'))
    try:
        s.schema()
        vectors={'igual':[1.0]+[0.0]*383,'ortogonal':[0.0,1.0]+[0.0]*382,'oposto':[-1.0]+[0.0]*383}
        s.upsert_nodes('Teste',[{'id':k,'props':{'id':k,'name':k,'kind':'Teste'}} for k in vectors])
        s.vectors([{'id':k,'vector':v} for k,v in vectors.items()])
        s.wait_ready()
        rows=s.query(VECTOR,{'vector':vectors['igual'],'k':3})
        assert [r['id'] for r in rows]==['igual','ortogonal','oposto']
        assert rows[0]['score']==pytest.approx(0,abs=1e-6)
    finally:
        s.graph.delete()
