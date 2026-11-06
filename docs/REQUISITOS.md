# Mapeamento do enunciado

O PDF enviado especifica originalmente Neo4j. O grupo informou que o professor recomendou FalkorDB. Esta entrega adota FalkorDB; comandos e bibliotecas Neo4j não são reutilizados como se fossem compatíveis.

| Requisito do PDF | Implementação / evidência | Observação |
|---|---|---|
| Domínio e dataset | Censo Superior 2024; 300 ofertas PB para execução inicial; importador da base completa | Amostra não estima população |
| Modelo LPG | Preservação dos rótulos e relações do repositório, mais Entity/Documento/Trecho | docs/ARQUITETURA.md |
| Constraints e índices | UNIQUE/MANDATORY em Entity.id; índices de propriedade, full-text e vector | store.py; comandos próprios FalkorDB |
| Text-to-Graph NER/RE | Extrator por dicionário de entidades e relação MENCIONA com página/fonte | Não é extrator geral de fatos ou novas entidades |
| Entity resolution | ID canônico da fonte; normalização de alias; ambiguidades não vinculadas | Testes de nomes iguais e acentos |
| Busca híbrida | Full-text + embeddings multilíngues + RRF | Hash opcional é apenas baseline lexical |
| Cypher gerado por LLM | LLM gera filtros JSON e templates produzem Cypher parametrizado | Adaptação deliberada; não há execução livre do texto do modelo |
| Dois ou mais saltos | Caminhos de até dois saltos; oferta → curso → IES | Caminhos efetivamente usados são exibidos |
| Algoritmo de grafo | PageRank do subgrafo usado na ordenação e na visualização | Não mede importância nacional |
| LLM com grounding | Contexto de caminhos, trechos e agregações; citações verificadas sintaticamente | Requer provedor configurado; veracidade ainda exige avaliação |
| Interface funcional | Streamlit com consulta, importação, exploração e documentação | Acesso local na 8501 |
| Grafo interativo | PyVis com JS incluído, zoom, arraste, fontes no hover | Renderiza somente o contexto recuperado |
| Rastreabilidade | IDs, fonte, página, consultas, parâmetros, filtros e JSON exportável | Cobertura não é probabilidade |
| Redução de alucinações comprovada | Guardas de esquema/citação e protocolo de avaliação incluídos | Estudo com julgamentos humanos ainda deve ser executado; não há alegação de redução percentual |
| Código completo e README | ZIP e instruções Windows/Docker/Python | Grupo deve criar seu repositório e conceder acesso ao docente |
| Artigo técnico e defesa | Texto inicial e roteiro em docs/ | Revisar autores, template SBC/IEEE e resultados finais antes da entrega |

Não há alegação de “nível de produção”. Para publicar seria necessário acrescentar autenticação, isolamento de usuários, backups testados, limites operacionais e validação de segurança/infraestrutura apropriados ao ambiente escolhido.
