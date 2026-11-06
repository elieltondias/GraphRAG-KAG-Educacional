# Validação executada

Data: 2 de novembro de 2026. Ambiente Linux, Python 3.12; módulo real FalkorDB 4.22.1 iniciado a partir do pacote falkordblite 0.11.0. O projeto entregue usa o cliente FalkorDB e Docker Compose; não depende de falkordblite para executar no computador do usuário.

## Testes operacionais

**20 testes passaram** na última execução: 10 testes de funções de domínio, 7 de integração com servidor real e 3 de guardas da integração LLM com resposta simulada. Saída: TESTES_EXECUTADOS.txt.

Cobertura exercitada: IDs e tipos, booleanos inválidos, identificadores, normalização, hashing, nomes ambíguos, fronteiras de palavra, RRF, filtros parametrizados, preservação de texto em trechos, contagens reais, reimportação idempotente, travessia de dois saltos, PageRank, procedência, tentativas de injeção, constraints, ordenação por distância vetorial, menções documentais, incompatibilidade de escopo, plano de filtros do LLM, citação inventada e abstenção sem evidência.

A amostra importou 970 nós e 3.101 relações. A reimportação preservou essas contagens. Foram confirmadas 300 ofertas, 270 cursos e 50 instituições. João Pessoa retornou 67 ofertas e soma de 2.039 matrículas.

## Interface

O AppTest do Streamlit carregou Consultar, Explorar dados, Importar e Sobre o projeto sem exceções. Uma pergunta com filtro de João Pessoa foi submetida e retornou as 67 ofertas esperadas. O HTML do grafo foi gerado sem erro. Registro em UI_VALIDACAO.json.

Isso é validação automatizada do comportamento da aplicação, não uma inspeção visual em todos os navegadores/tamanhos de tela.

## Embeddings semânticos e documentos

O modelo sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 foi baixado e executado, produzindo vetores de 384 dimensões. A amostra foi importada com o modelo real. O texto de exemplo gerou um documento, um trecho e três vínculos de menção; a recuperação documental retornou o trecho como evidência.

A última geração/importação semântica levou aproximadamente 8,65 segundos no ambiente de teste, já com o modelo em cache. Esse valor não inclui o primeiro download e não é uma previsão para outra máquina ou a carga nacional.

## Ensaio de recuperação

Foram usadas cinco consultas de entidade conhecida, descritas em scripts/evaluate.py, antes de importar o documento de exemplo. As variantes lexical e híbrida incluem resolução de nomes exatos; a variante vector usa somente o índice vetorial para escolher sementes. Resultado médio de Recall de entidades nas quatro sementes:

| Estratégia | Recall@4 médio | Latência mediana (s) |
|---|---:|---:|
| lexical | 1.00 | 0.2096 |
| vector | 0.60 | 0.1195 |
| hybrid | 1.00 | 0.1093 |

Os registros completos estão em AVALIACAO_SEMANTICA.json. O ensaio é pequeno e favorece correspondências de nomes exatos. A estratégia híbrida empatou com a lexical; não foi demonstrada superioridade geral da recuperação híbrida. Não se deve interpretar esse Recall como exatidão de respostas ou como taxa de redução de alucinações.

## Não validado nesta entrega

- Construção e execução das imagens pelo Docker Desktop: não havia Docker disponível neste ambiente. O YAML foi lido/validado estruturalmente; a tag oficial v4.22.1 foi confirmada no registro e o diretório de persistência foi conferido na documentação oficial.
- Importação nacional completa: o repositório foi obtido e inspecionado; somente a amostra foi carregada no banco para validação.
- Provedor LLM externo autenticado ou modelo local de linguagem: a integração é configurável, mas os testes de guardas usam respostas simuladas. Não há alegação de qualidade de geração real sem esse experimento.
- Publicação na internet, múltiplos usuários, capacidade máxima, tolerância a falhas e comparação estatística de alucinações.

## Antes da apresentação

Executar o Compose no computador da defesa, importar a amostra, conferir os números de controle e abrir o grafo. Se usar LLM, configurar o provedor e avaliar perguntas numéricas, multissalto e sem resposta. Se apresentar totais nacionais, importar e validar a base completa antes. Revisar o rascunho do artigo e adequá-lo ao template solicitado pelo professor.
