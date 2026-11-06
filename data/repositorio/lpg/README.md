# LPG — Censo da Educação Superior 2024

Grafo de propriedades rotulado (**Labeled Property Graph — LPG**) construído a partir dos microdados do **Censo da Educação Superior 2024** do INEP/MEC.

O grafo preserva os dados originais e adiciona uma camada de navegação por instituições, cursos, geografia e classificações CINE.

## Resumo

| Item | Quantidade |
|---|---:|
| Ofertas de curso (`OfertaCurso`) | 720.349 |
| Cursos distintos (`Curso`) | 46.150 |
| IES (`IES`) | 2.561 |
| Mantenedoras (`Mantenedora`) | 1.755 |
| Municípios (`Municipio`) | 3.551 |
| UFs (`UF`) | 27 |
| Regiões (`Regiao`) | 5 |
| Nós totais | 774.915 |
| Arestas totais | 3.791.431 |

O ano de referência é **2024**. O dataset de origem não foi alterado.

## Fonte

- `microdados_censo_da_educacao_superior_2024/dados/MICRODADOS_CADASTRO_CURSOS_2024.CSV`
  - 720.349 linhas, 223 colunas, separador `;`, codificação Latin-1.
- `microdados_censo_da_educacao_superior_2024/dados/MICRODADOS_ED_SUP_IES_2024.CSV`
  - 2.561 linhas, 84 colunas.
- `microdados_censo_da_educacao_superior_2024/Anexos/ANEXO I - Dicionário de Dados/dicionário_dados_educação_superior.xlsx`
  - dicionário oficial das variáveis.

## Estrutura de pastas

```text
lpg/
├── README.md
├── manifest.json
├── schema/
│   ├── modelo.md
│   ├── dicionario_variaveis.csv
│   ├── categorias.csv
│   └── mapeamento_variaveis.csv
├── nos/
│   ├── geografia/
│   │   ├── regiao.csv
│   │   ├── uf.csv
│   │   └── municipio.csv
│   ├── institucional/
│   │   ├── ies.csv
│   │   └── mantenedora.csv
│   ├── academico/
│   │   ├── curso.csv
│   │   └── oferta_curso.csv
│   └── classificacoes/
│       ├── cine_area_geral.csv
│       ├── cine_area_especifica.csv
│       ├── cine_area_detalhada.csv
│       ├── cine_rotulo.csv
│       ├── grau_academico.csv
│       ├── modalidade_ensino.csv
│       ├── nivel_academico.csv
│       ├── organizacao_academica.csv
│       ├── rede.csv
│       ├── categoria_administrativa.csv
│       └── dimensao_geografica.csv
├── arestas/
│   ├── geografia/
│   │   ├── uf_pertence_regiao.csv
│   │   └── municipio_pertence_uf.csv
│   ├── institucional/
│   │   ├── ies_sediada_em_municipio.csv
│   │   ├── ies_mantida_por_mantenedora.csv
│   │   ├── ies_tem_organizacao_academica.csv
│   │   ├── ies_tem_categoria_administrativa.csv
│   │   └── ies_pertence_rede.csv
│   ├── academico/
│   │   ├── curso_ofertado_por_ies.csv
│   │   ├── curso_tem_grau_academico.csv
│   │   ├── curso_tem_nivel_academico.csv
│   │   ├── curso_classificado_em_cine_rotulo.csv
│   │   ├── oferta_curso_oferta_de.csv
│   │   ├── oferta_curso_ofertada_por_ies.csv
│   │   ├── oferta_curso_localizada_em_municipio.csv
│   │   ├── oferta_curso_tem_modalidade_ensino.csv
│   │   └── oferta_curso_tem_dimensao_geografica.csv
│   └── classificacoes/
│       ├── cine_rotulo_pertence_area_detalhada.csv
│       ├── cine_area_detalhada_pertence_area_especifica.csv
│       └── cine_area_especifica_pertence_area_geral.csv
├── scripts/
│   ├── construir_lpg.py
│   ├── validar_lpg.py
│   ├── converter_para_generico.py
│   ├── lpg_dominio.py
│   ├── lpg_io.py
│   └── importar_neo4j.sh
├── tests/
│   ├── test_dominio.py
│   └── test_integracao.py
└── validacao/
    └── relatorio_validacao.md
```

O modelo completo, com todas as propriedades e cardinalidades, está em [`schema/modelo.md`](schema/modelo.md).

## Arquitetura dos scripts

- `lpg_dominio.py`: especificações declarativas de nós/arestas, domínios, regras de tipagem, mapeamentos e contagens esperadas.
- `lpg_io.py`: writers CSV, leitura de CSV/XLSX, hashes, schema e manifesto.
- `construir_lpg.py`: orquestra o pipeline de coleta e escrita.
- `validar_lpg.py`: valida o grafo com registry de processadores, estratégias de destino e checks declarativos.
- `converter_para_generico.py`: converte o formato Neo4j para `id,label` / `source,target,type`.

A refatoração usa padrões como **Registry**, **Strategy**, **Null Object**, **Value Object**, **Pipeline** e **tabelas de regras**, reduzindo cadeias de `if/elif` e mantendo a saída byte-idêntica.

## Formato dos CSVs

- Codificação **UTF-8**.
- Separador **vírgula**.
- Quebra de linha **LF**.
- Uma linha de cabeçalho por arquivo.
- Um arquivo por label de nó e um por tipo de aresta.

### Nós

```csv
:ID,:LABEL,CO_IES,NO_IES,...
ies_1,IES,1,UNIVERSIDADE FEDERAL DE MATO GROSSO,...
```

### Arestas

```csv
:START_ID,:END_ID,:TYPE
ies_1,municipio_5103403,SEDIADA_EM
```

### Tipos

- **IDs e códigos** são texto.
- **Métricas `QT_*`** são inteiros (`:long` no cabeçalho).
- **Campos `TP_*` e `NU_ANO_CENSO`** são inteiros (`:int`).
- **Campos `IN_*`** são booleanos (`:boolean`).
- Campos vazios viram `null` na importação do Neo4j quando `--ignore-empty-strings=true` é usado.

Exemplos de IDs:

```text
regiao_1
uf_35
municipio_3550308
ies_417
mantenedora_1
curso_417_5001662
oferta_417_5001662_5300108_2_2
cine_rotulo_0114Q01
```

## Como usar no Neo4j

O formato dos CSVs é o do `neo4j-admin import` (Neo4j 5.x). O script abaixo monta a lista de arquivos automaticamente:

```bash
# banco de destino deve estar parado e ainda não existir
./lpg/scripts/importar_neo4j.sh neo4j
```

O script usa:

```bash
neo4j-admin database import full \
  --verbose \
  --id-type=STRING \
  --ignore-empty-strings=true \
  --nodes=... \
  --relationships=... \
  neo4j
```

Para Neo4j 4.x, troque `neo4j-admin database import full` por `neo4j-admin import`.

### Índices recomendados

```cypher
CREATE INDEX oferta_curso_co_ies IF NOT EXISTS
FOR (n:OfertaCurso) ON (n.CO_IES);

CREATE INDEX oferta_curso_co_curso IF NOT EXISTS
FOR (n:OfertaCurso) ON (n.CO_CURSO);

CREATE INDEX curso_co_curso IF NOT EXISTS
FOR (n:Curso) ON (n.CO_CURSO);

CREATE INDEX ies_co_ies IF NOT EXISTS
FOR (n:IES) ON (n.CO_IES);

CREATE INDEX municipio_co_municipio IF NOT EXISTS
FOR (n:Municipio) ON (n.CO_MUNICIPIO);

CREATE INDEX uf_sg_uf IF NOT EXISTS
FOR (n:UF) ON (n.SG_UF);
```

## Como usar em Python

Com pandas:

```python
import pandas as pd

ofertas = pd.read_csv(
    "lpg/nos/academico/oferta_curso.csv",
    dtype={"CO_IES": str, "CO_CURSO": str, "CO_MUNICIPIO": str},
)

cursos = pd.read_csv(
    "lpg/nos/academico/curso.csv",
    dtype={"CO_IES": str, "CO_CURSO": str},
)
```

Com o formato genérico, para NetworkX:

```bash
python3 lpg/scripts/converter_para_generico.py
```

Isso cria `lpg/generico/` com:

- nós: `id,label,...`
- arestas: `source,target,type`

Exemplo:

```python
import csv
import networkx as nx

G = nx.MultiDiGraph()

with open("lpg/generico/nos/academico/oferta_curso.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        G.add_node(row["id"], label=row["label"], **row)

with open("lpg/generico/arestas/academico/oferta_curso_oferta_de.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        G.add_edge(row["source"], row["target"], type=row["type"])
```

## Como reconstruir

O build usa apenas a biblioteca padrão do Python 3 e lê o CSV de 452 MB em streaming.

```bash
python3 lpg/scripts/construir_lpg.py
```

Opções:

```bash
python3 lpg/scripts/construir_lpg.py \
  --base microdados_censo_da_educacao_superior_2024 \
  --saida lpg
```

- `--base`: pasta dos microdados.
- `--saida`: pasta de saída.
- `--cursos`, `--ies`, `--dicionario`: caminhos alternativos.
- `--limite N`: processa apenas N linhas de curso (teste).

O script sobrescreve os arquivos gerados, mas não remove arquivos que não fazem parte do build.

## Como validar

```bash
python3 lpg/scripts/validar_lpg.py
```

O validador confere:

- contagem de todos os nós e arestas;
- unicidade dos IDs;
- integridade referencial de todas as arestas;
- cardinalidade das relações (cada curso com uma IES, um grau, um nível e um rótulo CINE; cada oferta com curso, IES, modalidade e dimensão);
- correspondência entre as propriedades e as arestas;
- hierarquia CINE;
- totais de controle das métricas;
- distribuições das principais categorias.

O resultado é gravado em `lpg/validacao/relatorio_validacao.md`.

## Como testar

```bash
python3 -m unittest discover -s lpg/tests -v
```

Os testes cobrem:

- regras puras de tipagem, formatação, IDs e mapeamentos;
- unicidade e coerência das especificações de nós/arestas;
- build parcial com `--limite 1000`;
- cabeçalhos tipados e contagem do dicionário;
- conversão para o formato genérico.

## Totais de controle

| Métrica | Total |
|---|---:|
| `QT_MAT` | 10.227.266 |
| `QT_MAT_FEM` | 6.088.602 |
| `QT_MAT_MASC` | 4.138.664 |
| `QT_VG_TOTAL` | 23.665.419 |
| `QT_ING` | 5.010.613 |
| `QT_CONC` | 1.333.988 |

Esses valores são somas diretas das 720.349 ofertas e são usados como âncoras de validação.

## Dicionário e schema

- `schema/modelo.md`: diagrama, nós, arestas, propriedades e decisões de modelagem.
- `schema/dicionario_variaveis.csv`: descrição oficial das 223 variáveis de cursos e 84 de IES, com destino no grafo.
- `schema/categorias.csv`: mapeamento código → rótulo para `TP_*` e `IN_*`.
- `schema/mapeamento_variaveis.csv`: variável de origem → nó(s) do grafo.
- `manifest.json`: contagens, tamanhos, SHA-256, totais e distribuições.

## Decisões e limitações

- **Ano único:** o grafo contém apenas 2024. O campo `NU_ANO_CENSO` está presente nos nós.
- **EAD sem município:** 11.778 ofertas não têm `CO_MUNICIPIO` (11.769 de dimensão 3 ou 4 e 9 de dimensão 2); elas não recebem a aresta `LOCALIZADA_EM`. O `TP_DIMENSAO` e o nó `DimensaoGeografica` registram a abrangência.
- **Nove ofertas de dimensão 2 sem município:** também ficam sem `LOCALIZADA_EM`; são casos de local desconhecido no arquivo de origem.
- **Grau acadêmico ausente:** 378 cursos (2.046 ofertas) têm `TP_GRAU_ACADEMICO` vazio e são ligados ao nó `GrauAcademico` com código `NA`.
- **Categorias ausentes:** as categorias administrativas 6, 8 e 9 não aparecem em 2024 e, por isso, não geram nós.
- **Mesorregião/microrregião:** ficam como propriedades da IES; não foram criados nós porque o arquivo de cursos não traz esses campos para todos os municípios de oferta.
- **CINE rótulo:** o código `CO_CINE_ROTULO` vinha entre aspas literais no CSV original; as aspas foram removidas.
- **Métricas brutas:** não há agregação, deduplicação ou cálculo de indicadores derivados. As somas preservam os totais do Censo.
- **Nomes de propriedades:** seguem o dicionário oficial, em maiúsculas, para manter rastreabilidade.

## Citação

Fonte dos dados: **INEP/MEC — Microdados do Censo da Educação Superior 2024**.
