import re
import time
from falkordb import FalkorDB
from redis.exceptions import ResponseError
from src.config import Settings
from src.embeddings import DIMENSION

def identifier(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        raise ValueError(f'Identificador inválido: {value!r}')
    return value

class Store:
    def __init__(self, settings=None, client=None):
        self.settings = settings or Settings()
        self.client = client or FalkorDB(host=self.settings.host, port=self.settings.port,
                                       password=self.settings.password or None,
                                       socket_connect_timeout=5, socket_timeout=180)
        self.graph = self.client.select_graph(self.settings.graph)
        self.trace = []

    def query(self, cypher, params=None, write=False):
        result = (self.graph.query if write else self.graph.ro_query)(cypher, params or {}, timeout=120000)
        if not write:
            self.trace.append({'cypher': cypher, 'params': params or {}})
        names = [h[1] for h in result.header]
        return [dict(zip(names, row)) for row in result.result_set]

    def schema(self):
        queries = [
            'CREATE INDEX FOR (n:Entity) ON (n.id)',
            'CREATE INDEX FOR (n:Entity) ON (n.name_norm)',
            "CALL db.idx.fulltext.createNodeIndex('Entity', 'search_text')",
            f"CREATE VECTOR INDEX FOR (n:Entity) ON (n.embedding) OPTIONS {{dimension:{DIMENSION}, similarityFunction:'cosine'}}",
        ]
        for q in queries:
            try:
                self.query(q, write=True)
            except ResponseError as e:
                if 'already indexed' not in str(e).lower() and 'already exists' not in str(e).lower():
                    raise
        existing = self.query('CALL db.constraints()')
        for kind in ['UNIQUE', 'MANDATORY']:
            if not any(r.get('type') == kind and r.get('label') == 'Entity' and r.get('properties') == ['id'] for r in existing):
                self.client.execute_command('GRAPH.CONSTRAINT', 'CREATE', self.settings.graph, kind, 'NODE', 'Entity', 'PROPERTIES', 1, 'id')
        self.wait_ready()

    def wait_ready(self):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            constraints = self.query('CALL db.constraints()')
            indexes = self.query('CALL db.indexes()')
            states = [str(r.get('status', '')).upper() for r in constraints + indexes]
            if any(s == 'FAILED' for s in states):
                raise RuntimeError('Falha ao construir índice/constraint. Veja db.indexes e db.constraints.')
            if all(s in {'OPERATIONAL', 'ONLINE'} for s in states):
                return
            time.sleep(0.2)
        raise TimeoutError('Índices/constraints ainda não estão prontos.')

    def metadata(self):
        try:
            rows = self.query('MATCH (m:Metadata {id:$id}) RETURN properties(m) AS data', {'id':'dataset'})
            return rows[0]['data'] if rows else {}
        except ResponseError as e:
            if 'does not exist' in str(e).lower() or 'empty key' in str(e).lower():
                return {}
            raise

    def set_metadata(self, data):
        self.query('MERGE (m:Metadata {id:$id}) SET m += $data', {'id':'dataset', 'data':data}, write=True)

    def upsert_nodes(self, label, rows):
        label = identifier(label)
        self.query(f'UNWIND $rows AS row MERGE (n:Entity:{label} {{id:row.id}}) SET n += row.props', {'rows':rows}, write=True)

    def upsert_edges(self, kind, rows):
        kind = identifier(kind)
        result = self.query(f'UNWIND $rows AS row MATCH (a:Entity {{id:row.source}}), (b:Entity {{id:row.target}}) MERGE (a)-[r:{kind}]->(b) RETURN count(r) AS matched', {'rows':rows}, write=True)
        if result[0]['matched'] != len(rows):
            raise ValueError(f'Relações {kind} com origem/destino ausente. Importação incompleta.')

    def vectors(self, rows):
        self.query('UNWIND $rows AS row MATCH (n:Entity {id:row.id}) SET n.embedding=vecf32(row.vector)', {'rows':rows}, write=True)

    def stats(self):
        return self.query('MATCH (n:Entity) RETURN n.kind AS tipo, count(n) AS quantidade ORDER BY quantidade DESC')
