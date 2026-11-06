# NexoEdu: consulta rastreável a microdados do ensino superior com grafos de conhecimento

**Rascunho técnico para revisão do grupo.** Inserir autores/afiliação e adequar ao template SBC ou IEEE solicitado. Não apresentar experimentos pendentes como concluídos.

## Resumo

Este trabalho apresenta um protótipo de centro lógico de microdados do ensino superior que combina um grafo de propriedades no FalkorDB, recuperação textual e vetorial e consultas estruturadas. O sistema organiza entidades de instituições, cursos, ofertas e geografia do Censo da Educação Superior 2024. Uma amostra de 300 ofertas localizadas na Paraíba permite reprodução inicial. A interface expõe caminhos, consultas e fontes para apoiar inspeção humana. Respostas podem ser obtidas por agregações determinísticas ou por um modelo de linguagem configurável. A implementação inclui controles de identidade, escopo e citações, mas a mensuração da redução de alucinações exige avaliação humana adicional.

**Palavras-chave:** GraphRAG; grafo de conhecimento; ensino superior; microdados; FalkorDB.

## 1. Introdução

Dados educacionais tabulares apresentam relações distribuídas entre códigos de instituição, curso, modalidade e território. Perguntas em linguagem natural podem exigir conexões entre esses elementos, enquanto um modelo de linguagem isolado não oferece garantia de aderência aos registros. A proposta é explicitar tais relações e tornar verificável o contexto fornecido à geração.

O objetivo é implementar e avaliar uma arquitetura de consulta com recuperação híbrida, travessia multissalto e procedência. O escopo compreende um dataset de 2024 por grafo e consultas locais. Não se pretende inferir causalidade, desempenho acadêmico individual ou qualidade de instituições a partir de volume de matrículas.

## 2. Fundamentos

GraphRAG combina recuperação e estrutura de grafos para ampliar o contexto de geração. Nesta implementação, o componente de conhecimento inclui esquema de domínio, regras de identidade e consultas parametrizadas. KAG é empregado como orientação arquitetural de fundamentação em conhecimento explícito, sem alegar implementação integral de um framework externo.

A busca full-text prioriza correspondência lexical; o modelo multilíngue produz embeddings de entidades. RRF funde posições dos rankings, evitando comparar escores de escalas diferentes. PageRank fornece uma ordenação local dos caminhos recuperados.

## 3. Materiais e métodos

A fonte usada é o LPG publicado no repositório elieltondias/GraphRAG-KAG-Educacional, revisão registrada em FONTES.md, derivado dos microdados INEP/MEC 2024. A amostra seleciona 300 ofertas com município na Paraíba pela ordenação do hash dos IDs, preservando o fechamento das relações de saída. O recorte é não probabilístico e não produz estimativas populacionais.

O importador converte cabeçalhos tipados, preserva códigos como texto e aplica IDs canônicos com namespace de ano. FalkorDB mantém índices de propriedade, full-text e vetoriais e constraints de unicidade e existência. As consultas de agregação operam no grão OfertaCurso, separado do conjunto limitado de caminhos visuais.

A recuperação prioriza entidades de nome exato e completa quatro sementes com RRF e até 60 caminhos de comprimento um ou dois por semente. O PageRank é calculado nesse subgrafo. PDFs textuais e TXT produzem trechos e vínculos MENCIONA, por reconhecimento de entidades de dicionário e resolução de alias não ambíguos. Não são extraídos fatos arbitrários de coocorrência.

A integração opcional com LLM converte perguntas em filtros JSON e redige respostas fundamentadas em caminhos, trechos e agregações. O Cypher é produzido por templates parametrizados. Citações são verificadas quanto à existência, mas não semanticamente em todas as afirmações.

## 4. Avaliação reproduzível

A validação operacional cobre tipagem, normalização, integridade, idempotência, constraints, consultas parametrizadas, travessia e procedência. As quantidades de controle da amostra são 970 nós, 3.101 relações, 300 ofertas, 270 cursos e 50 instituições. Um recorte por João Pessoa contém 67 ofertas e soma 2.039 matrículas, sem interpretação populacional.

O script `scripts/evaluate.py` compara recuperação lexical, vetorial e híbrida em cinco consultas de entidades conhecidas. A métrica é Recall de sementes em top-4, com latência observada. Trata-se de um ensaio pequeno de recuperação, não um teste conclusivo de generalização ou alucinação. Resultados executados e limites de validação estão em VALIDACAO.md e nos JSONs de avaliação.

Para avaliar grounding, o grupo deve ampliar o conjunto com perguntas multissalto, numéricas e sem resposta, definir gabaritos verificáveis e comparar: LLM sem contexto, RAG vetorial e GraphRAG/KAG. Dois avaliadores devem classificar afirmações suportadas, incorretas, ausentes e abstenções, com resolução das divergências. Não preencher percentuais antes de executar o estudo.

## 5. Discussão e limitações

A explicitação de fontes permite auditoria, mas não elimina erros de recuperação ou geração. A resolução por dicionário não cobre entidades inéditas. A amostra exclui ofertas sem município e não representa estatisticamente o estado. O PageRank depende do recorte recuperado e não equivale à relevância de uma instituição no Brasil.

A implementação é local e acadêmica; a carga nacional completa, testes de escala e geração por provedor externo autenticado devem ser executados no ambiente final antes de qualquer alegação de desempenho em produção.

## 6. Considerações finais

O protótipo permite inspecionar dados e caminhos de conhecimento do ensino superior, combinando busca híbrida e cálculos estruturados. A contribuição prática é um pipeline reproduzível com rastreabilidade e separação explícita entre amostra, dado carregado e resposta gerada. Trabalhos futuros incluem avaliação humana de grounding, mais anos de microdados e extração de relações documentais com validação de domínio.

## Referências a formatar

1. INEP/MEC. Microdados do Censo da Educação Superior 2024. Fonte declarada no LPG consultado.
2. Dias, Elielton. GraphRAG-KAG-Educacional. GitHub. Revisão em FONTES.md.
3. FalkorDB. Documentação de índices, constraints e cliente Python. URLs em FONTES.md.
4. Sentence Transformers / FastEmbed. Modelo multilíngue e documentação. URLs em FONTES.md.
5. Acrescentar referências primárias sobre GraphRAG, KAG, RRF e PageRank após leitura e verificação pelo grupo.
