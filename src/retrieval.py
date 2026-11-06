import json
import re
from dataclasses import dataclass, asdict
import networkx as nx
from src.embeddings import Embedder, normalize, tokens

@dataclass
class Filters:
    uf: str = ''
    municipio: str = ''
    curso: str = ''
    ies: str = ''
    modalidade: int = 0

BASE = '''MATCH (o:OfertaCurso)-[:OFERTA_DE]->(c:Curso)
MATCH (o)-[:OFERTADA_POR]->(i:IES)
OPTIONAL MATCH (o)-[:LOCALIZADA_EM]->(m:Municipio)-[:PERTENCE_A_UF]->(u:UF)
WITH o,c,i,m,u
WHERE ($uf='' OR u.SG_UF=$uf)
AND ($municipio='' OR m.name_norm CONTAINS $municipio)
AND ($curso='' OR c.name_norm CONTAINS $curso)
AND ($ies='' OR i.name_norm CONTAINS $ies OR toLower(i.SG_IES)=$ies)
AND ($modalidade=0 OR o.TP_MODALIDADE_ENSINO=$modalidade)
'''

DETAIL = BASE + '''RETURN o.id AS oferta_id,c.name AS curso,i.name AS ies,
m.name AS municipio,u.SG_UF AS uf,o.TP_MODALIDADE_ENSINO AS modalidade,
o.QT_MAT AS matriculas,o.QT_ING AS ingressantes,o.QT_CONC AS concluintes,
o.source_file AS source_file ORDER BY matriculas DESC,oferta_id LIMIT 100'''
TOTAL = BASE + '''RETURN count(DISTINCT o) AS ofertas,count(DISTINCT c) AS cursos,
count(DISTINCT i) AS instituicoes,sum(coalesce(o.QT_MAT,0)) AS matriculas,
sum(coalesce(o.QT_ING,0)) AS ingressantes,sum(coalesce(o.QT_CONC,0)) AS concluintes'''

VECTOR = "CALL db.idx.vector.queryNodes('Entity','embedding',$k,vecf32($vector)) YIELD node,score RETURN node.id AS id,node.name AS name,score ORDER BY score ASC"
EXACT = "MATCH (n:Entity {name_norm:$name}) RETURN n.id AS id,n.name AS name ORDER BY n.id LIMIT 12"
LEXICAL = "CALL db.idx.fulltext.queryNodes('Entity',$text) YIELD node,score RETURN node.id AS id,node.name AS name,score ORDER BY score DESC LIMIT 12"
PATHS = '''MATCH p=(a:Entity {id:$id})-[*1..2]-(b:Entity)
WHERE a.id<>b.id RETURN p LIMIT 60'''
OFFER_PATH = '''MATCH p=(o:OfertaCurso {id:$id})-[:OFERTA_DE]->(c:Curso)-[:OFERTADO_POR]->(i:IES)
RETURN p LIMIT 1'''


def rrf(rankings, k=60):
    scores = {}
    for rows in rankings:
        for rank, row in enumerate(rows,1):
            scores[row['id']] = scores.get(row['id'],0) + 1/(k+rank)
    return sorted(scores, key=lambda i:(-scores[i],i))

def filter_params(filters):
    p = asdict(filters)
    p['uf'] = p['uf'].strip().upper()
    for key in ['municipio','curso','ies']:
        p[key] = normalize(p[key].strip())
    if p['uf'] and not re.fullmatch('[A-Z]{2}',p['uf']):
        raise ValueError('UF deve ter duas letras.')
    if p['modalidade'] not in {0,1,2}:
        raise ValueError('Modalidade inválida.')
    return p

def graph_context(paths):
    nodes = {}
    edges = {}
    evidence = []
    path_records = []
    for record in paths:
        p = record['p']
        path_nodes = list(p.nodes())
        path_edges = list(p.edges())
        for n in path_nodes:
            props = n.properties
            nodes[n.id] = {'id':str(n.id),'key':props.get('id',''),'name':props.get('name',''),
                           'kind':props.get('kind',''),'source':props.get('source_file','')}
        parts = [path_nodes[0].properties.get('name','?')]
        for e,n in zip(path_edges,path_nodes[1:]):
            edges[e.id] = {'id':str(e.id),'source':str(e.src_node),'target':str(e.dest_node),'type':e.relation}
            direction = '→' if e.src_node == path_nodes[len(parts)//2].id else '←'
            parts.extend([f'{direction} {e.relation}',n.properties.get('name','?')])
        text = ' '.join(parts)
        if text not in evidence:
            evidence.append(text)
            path_records.append({'path':text,'node_ids':[str(n.id) for n in path_nodes],
                'snippets':[{'source':n.properties.get('source_file',''),'page':n.properties.get('page',1),'text':n.properties['text']} for n in path_nodes if n.properties.get('text')]})
    graph = nx.DiGraph()
    for n in nodes.values():
        graph.add_node(n['id'])
    for e in edges.values():
        graph.add_edge(e['source'],e['target'])
    ranks = nx.pagerank(graph) if graph else {}
    for n in nodes.values():
        n['pagerank'] = ranks.get(n['id'],0)
    path_records.sort(key=lambda p:-sum(ranks.get(i,0) for i in p['node_ids']))
    return {'nodes':list(nodes.values()),'edges':list(edges.values()),'paths':[p['path'] for p in path_records],'path_records':path_records}

def structured(store, filters):
    params = filter_params(filters)
    rows = store.query(DETAIL,params)
    totals = {k:int(v or 0) for k,v in store.query(TOTAL,params)[0].items()}
    return {'rows':rows,'totals':totals,'filters':params}

def retrieve(store, question, filters=None, mode='hybrid'):
    if len(question.strip()) < 3 or len(question)>2000:
        raise ValueError('Escreva uma pergunta entre 3 e 2.000 caracteres.')
    metadata = store.metadata()
    if metadata.get('status') != 'pronto':
        raise ValueError('Importe uma base e aguarde a conclusão antes de consultar.')
    embedder = Embedder(store.settings.embedding,store.settings.model)
    if metadata.get('embedding_model') != embedder.identity:
        raise ValueError('O modelo configurado difere do usado na importação.')
    store.trace = []
    terms = tokens(question)[:20]
    lexical = store.query(LEXICAL,{'text':' | '.join(terms)}) if terms and mode != 'vector' else []
    vector = store.query(VECTOR,{'vector':embedder.encode([question])[0],'k':12}) if mode != 'lexical' else []
    exact = store.query(EXACT,{'name':normalize(question.strip())}) if mode != 'vector' else []
    anchors = [r['id'] for r in exact]
    seeds = list(dict.fromkeys(anchors + rrf([lexical,vector])))[:4]
    paths = []
    for seed in seeds:
        paths.extend(store.query(PATHS,{'id':seed}))
    facts = structured(store,filters) if filters is not None else None
    if facts:
        for row in facts['rows'][:8]:
            paths.extend(store.query(OFFER_PATH,{'id':row['oferta_id']}))
    context = graph_context(paths)
    evidence_ids = {n['key'] for n in context['nodes']}
    cited = [{'id':f'E{i+1}',**p} for i,p in enumerate(context['path_records'])]
    coverage = 'suficiente para os filtros' if facts and facts['totals']['ofertas'] else ('exploratória' if cited else 'insuficiente')
    return {'question':question,'scope':metadata.get('scope'),'year':metadata.get('year'),
            'mode':mode,'embedding':embedder.identity,'seeds':seeds,'graph':context,
            'evidence':cited,'facts':facts,'coverage':coverage,'consulted_node_ids':sorted(evidence_ids),
            'confidence_note':'Cobertura das evidências; não é probabilidade de a resposta estar correta.',
            'trace':store.trace.copy()}

def deterministic_answer(result):
    scope = 'Amostra parcial de 2024' if result['scope']=='amostra' else 'Base carregada de 2024'
    facts = result['facts']
    if facts is not None:
        t = facts['totals']
        if not t['ofertas']:
            return f'{scope}: nenhuma oferta encontrada para os filtros informados. Isso não prova ausência na população.'
        return (f"{scope}. Para os filtros exibidos, foram encontradas {t['ofertas']:,} ofertas, "
                f"{t['cursos']:,} cursos distintos e {t['instituicoes']:,} instituições. "
                f"As somas dos registros são {t['matriculas']:,} matrículas, {t['ingressantes']:,} ingressantes "
                f"e {t['concluintes']:,} concluintes. Fonte: consulta Cypher de agregação e tabela de ofertas abaixo. "
                'As quantidades se referem ao recorte carregado; não são uma estimativa nacional.').replace(',','.')
    if not result['evidence']:
        return 'Não há evidências suficientes na base carregada para responder.'
    lines = [f'{scope}. Relações recuperadas para explorar a pergunta:']
    lines.extend(f"[{e['id']}] {e['path']}" for e in result['evidence'][:8])
    lines.append('A busca recupera relações próximas; sem um modelo de linguagem, esta lista não interpreta a pergunta. Use os filtros para calcular números exatos do recorte.')
    return '\n\n'.join(lines)
