# NexoEdu — Centro de microdados do ensino superior

Projeto acadêmico de GraphRAG/KAG com **FalkorDB**, Python e Streamlit. Usa os microdados do Censo da Educação Superior 2024 organizados no repositório indicado pelo grupo.

**Abra primeiro:** este README. O VS Code serve para editar os arquivos. O sistema roda como aplicação web; o FalkorDB é o servidor do banco de grafos, não substitui o editor.

## 1. Começar no Windows — caminho recomendado

1. Instale e abra o **Docker Desktop**, com suporte a contêineres Linux/WSL2. Aguarde o Docker ficar ativo.
2. Extraia o ZIP inteiro em uma pasta, por exemplo `C:\Projetos\ensino-superior-graph`.
3. Abra essa pasta no VS Code e abra o terminal, ou execute `INICIAR_WINDOWS.bat`.
4. No terminal, faça:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

5. Aguarde a construção terminar e abra **http://localhost:8501**.
6. Na lateral, clique **Importar → Importar amostra da Paraíba**. Aguarde a mensagem de conclusão. A primeira execução baixa o modelo de embeddings multilíngue; não exige chave de API.
7. Vá a **Explorar dados**, informe `João Pessoa` no município e clique **Aplicar filtros**. A amostra deve retornar **67 ofertas e 2.039 matrículas**. Esses são números da amostra, não totais de João Pessoa.
8. Vá a **Consultar**, faça a pergunta e, para calcular números, preencha os filtros. Sem LLM, a pergunta direciona a busca, mas não preenche os filtros automaticamente.

| Endereço/porta | Para que serve |
|---|---|
| http://localhost:8501 | Interface do projeto |
| http://localhost:3000 | FalkorDB Browser para explorar o banco |
| localhost:6379 | Conexão do cliente Python com o banco; não é página web |

No FalkorDB Browser, conecte ao servidor local e selecione `ensino_2024_amostra`. Se o Browser estiver dentro do contêiner, o servidor é `localhost:6379`. A interface Streamlit já vem configurada para acessar o serviço `falkordb` pela rede Docker.

Para parar e preservar os dados:

```powershell
docker compose down
```

Não use `down -v` se quiser preservar o banco e o cache: essa opção remove os volumes. O Compose expõe as portas apenas na máquina local. É uma instalação acadêmica local, sem autenticação de aplicação ou configuração de publicação.

## 2. O que já está implementado

- Importador em streaming dos CSVs LPG do repositório, incluindo cabeçalhos tipados; IDs numéricos são preservados como texto.
- Resolução de entidades pelo ID da fonte, com namespace de ano, índices e constraints de unicidade/obrigatoriedade.
- Validação de relações sem destino, ponteiros Git LFS, fingerprint do conjunto e bloqueio de mistura de escopos/modelos.
- Índice de propriedade, full-text e vetorial nativos do FalkorDB; `vecf32` para vetores.
- Embeddings multilíngues locais de 384 dimensões. Modo lexical por hashing opcional para teste sem download.
- Busca textual/vetorial, prioridade para nomes exatos e fusão por Reciprocal Rank Fusion; travessia de até dois saltos.
- PageRank do subgrafo recuperado para ordenar os caminhos e dimensionar os nós.
- Agregações Cypher parametrizadas de ofertas, matrículas, ingressantes e concluintes, com filtros.
- Upload de PDF textual/TXT: divisão em trechos, NER por dicionário do domínio, resolução de nomes não ambíguos e RE da relação `MENCIONA`.
- Grafo interativo, fontes, caminhos, IDs consultados, consultas Cypher e exportação CSV/JSON.
- Resposta determinística sem chave de IA; planejamento de filtros e redação por LLM opcionais.
- Testes de unidade/integração e roteiro de avaliação comparando estratégias.

## 3. Dados incluídos e repositório completo

O ZIP inclui **300 ofertas reais localizadas na Paraíba**, selecionadas de forma determinística por hash do ID, com as entidades alcançáveis pelas relações de saída: 970 nós e 3.101 arestas. Há sedes de instituições em outros estados, pois uma IES pode oferecer cursos na Paraíba a partir de outra sede.

A amostra é parcial, não probabilística, e não deve ser usada para estimar totais populacionais. O manifesto está em `data/sample/lpg/sample_manifest.json`. A procedência e os hashes estão em `docs/FONTES.md` e `data/sample/SHA256SUMS.json`.

Fonte: https://github.com/elieltondias/GraphRAG-KAG-Educacional

Revisão fixada: `2dadee4abf4f358b9b274e84ca08b67a15351a66`.

O repositório possui microdados brutos, dicionário e CSVs LPG prontos. O projeto importa **os CSVs de `lpg/nos` e `lpg/arestas`**, preservando os indicadores originais. Não consulta o GitHub durante cada pergunta. Os arquivos brutos não são necessários para executar a amostra.

### Importar a base completa no Docker

Os CSVs LPG completos já estão incluídos nesta cópia do repositório, em `lpg/`. A importação lê esses arquivos localmente; não é necessário baixar nada. Para a base completa, reserve inicialmente cerca de 16 GB de RAM e monitore o uso; isso é uma recomendação de planejamento, não um benchmark medido.

```powershell
docker compose exec app python -m src.cli ingest --path lpg --scope completa --graph ensino_2024_completo
```

O comando `python -m src.cli download` continua disponível caso você queira uma cópia isolada do repositório de dados em outra pasta; ele exige internet, Git e Git LFS.

Depois, altere `.env` para:

```dotenv
GRAPH_NAME=ensino_2024_completo
```

E recrie o serviço da aplicação:

```powershell
docker compose up -d --force-recreate app
```

A base completa fica em outro grafo. A amostra permanece separada. Não importe um dataset diferente no mesmo grafo: o fingerprint bloqueia essa operação.

Os embeddings são gerados para entidades pesquisáveis, não para cada uma das centenas de milhares de ofertas. Os indicadores das ofertas são recuperados por Cypher. A importação completa não foi executada nesta entrega; ver relatório de validação.

## 4. Rodar Python diretamente, editando pelo VS Code

Requer Python 3.12. O banco pode continuar no Docker:

```powershell
docker compose up -d falkordb
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Não é necessário ativar a venv. Se usar Linux/macOS, troque o caminho do Python por `.venv/bin/python`.

Para importar pelo terminal:

```powershell
.\.venv\Scripts\python.exe -m src.cli ingest
.\.venv\Scripts\python.exe -m src.cli ask "Cursos em João Pessoa" --structured --municipio "João Pessoa" --out consulta.json
```

## 5. Sem download de modelo: linha de base lexical

Se não puder baixar o modelo, altere os dois valores abaixo no `.env` antes da importação:

```dotenv
EMBEDDING_MODE=hash
GRAPH_NAME=ensino_2024_hash
```

Recrie a aplicação (`docker compose up -d --force-recreate app`) e importe a amostra. O hashing usa cosseno em vetores lexicais; **não é embedding semântico**. É uma opção de demonstração/depuração, não substitui o experimento com o modelo multilíngue. Não misture esses vetores com os semânticos no mesmo grafo.

## 6. LLM opcional

Sem LLM, as consultas exibem fatos e cálculos determinísticos. Para interpretar perguntas em filtros e redigir uma resposta, configure um servidor compatível com a API Chat Completions:

```dotenv
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=nome-do-modelo-instalado
LLM_API_KEY=
```

O endereço acima é um exemplo para um servidor local no Windows/Docker Desktop; instale e disponibilize o modelo no servidor escolhido. Para Python fora do Docker, use `http://localhost:11434/v1`. Um provedor externo pode exigir chave e cobrança. Nenhum modelo de linguagem nem chave estão incluídos.

O campo `LLM_BASE_URL` deve terminar em `/v1` quando essa for a convenção do servidor; o código acrescenta `/chat/completions`. Depois de alterar o `.env`, recrie o serviço `app`.

Marque **Interpretar a pergunta em filtros com LLM** para gerar parâmetros de uma consulta predefinida e **Redigir resposta com LLM** para gerar texto. Os filtros efetivamente usados ficam visíveis. Não executamos Cypher arbitrário produzido pelo modelo. O LLM recebe a pergunta, os resultados e os trechos recuperados; considere isso ao escolher documentos/provedor.

A validação de citações detecta referências inexistentes, mas não garante que uma frase seja verdadeira. A revisão humana continua necessária. Essa integração não foi validada com provedor externo autenticado nesta entrega.

## 7. Documentos e limitações

Em **Importar**, carregue PDF com texto ou TXT UTF-8 de até 15 MB/100 páginas. `data/exemplo_documento.txt` permite testar menções. PDFs escaneados exigem OCR prévio. O extrator reconhece entidades existentes por nome/sigla, com normalização de acentos e fronteiras de palavra. Nomes ambíguos não geram vínculo automático.

O sistema extrai a relação **trecho MENCIONA entidade**, com página e fonte; não infere que uma universidade oferece um curso só porque os dois aparecem no mesmo parágrafo. Não é um NER/RE geral de entidades inéditas.

Os filtros usam a localização da oferta, não a sede da IES. Cursos com o mesmo nome em IES diferentes mantêm IDs diferentes. Campos ausentes permanecem ausentes, exceto somas que tratam métricas nulas como zero. Os resultados refletem o ano de 2024. Não há séries históricas, detecção causal, comparação de qualidade de cursos, suporte multiusuário ou um datacenter físico nesta entrega. Trata-se de um centro lógico de consulta aos microdados.

## 8. Testar e avaliar

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
$env:RUN_INTEGRATION="1"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate.py
```

Os testes de integração criam e removem um grafo de teste com nome exclusivo, sem tocar no grafo de trabalho. Testes usam hashing para serem rápidos e determinísticos. A avaliação usa o modelo configurado no grafo de trabalho. O relatório entregue descreve o que foi realmente executado.

## 9. Organização

| Caminho | Conteúdo |
|---|---|
| `app.py` | Interface Streamlit |
| `src/store.py` | Cliente FalkorDB, schema, constraints e acesso parametrizado |
| `src/ingest.py` | Importação dos CSVs LPG |
| `src/documents.py` | Text-to-Graph por dicionário e menções |
| `src/embeddings.py` | Modelo semântico e baseline hash |
| `src/retrieval.py` | Cypher, RRF, multi-hop, PageRank e cálculos |
| `src/llm.py` | Planejamento por filtros e geração com citações |
| `src/cli.py` | Download, importação e consultas por terminal |
| `docs/` | Arquitetura, requisitos, artigo inicial, defesa e validação |
| `tests/` | Testes reproduzíveis |

## 10. Problemas comuns

- **Docker indisponível:** abra o Docker Desktop e habilite contêineres Linux.
- **Porta ocupada:** pare o outro serviço ou altere a porta externa do Compose e ajuste `.env` se executar Python no host.
- **`unknown command GRAPH.QUERY`:** a conexão está chegando a Redis comum. Use o serviço FalkorDB deste Compose.
- **Falha no download de embeddings:** verifique internet/acesso ao Hugging Face. O programa não substitui silenciosamente o modelo por hashing.
- **Ponteiro Git LFS:** instale Git LFS e rode `git lfs pull` na cópia do repositório.
- **Importação interrompida:** o status fica `importando`; repita a mesma importação. Consultas ficam bloqueadas até concluir.
- **Modelo/escopo/fingerprint diferente:** use novo `GRAPH_NAME`, recrie a aplicação e importe nesse grafo.
- **Browser porta 3000 indisponível:** confira `docker compose logs falkordb`; o banco pode estar ativo na 6379 mesmo com problema no Browser.
