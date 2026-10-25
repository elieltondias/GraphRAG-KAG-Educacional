# Relatório de validação do LPG

- **Dataset:** Censo da Educação Superior 2024
- **Grafo:** `/home/elielton/Projects/GraphRAG-KAG-Educacional/lpg`
- **Gerado em:** 2026-10-25T15:26:51.924359+00:00
- **Status:** **APROVADO**
- **Verificações:** 156
- **Aprovadas:** 156
- **Falhas:** 0

## Contagens

| Item | Quantidade |
|---|---:|
| Nó `Regiao` (`nos/geografia/regiao.csv`) | 5 |
| Nó `UF` (`nos/geografia/uf.csv`) | 27 |
| Nó `Municipio` (`nos/geografia/municipio.csv`) | 3.551 |
| Nó `IES` (`nos/institucional/ies.csv`) | 2.561 |
| Nó `Mantenedora` (`nos/institucional/mantenedora.csv`) | 1.755 |
| Nó `Curso` (`nos/academico/curso.csv`) | 46.150 |
| Nó `OfertaCurso` (`nos/academico/oferta_curso.csv`) | 720.349 |
| Nó `CineAreaGeral` (`nos/classificacoes/cine_area_geral.csv`) | 11 |
| Nó `CineAreaEspecifica` (`nos/classificacoes/cine_area_especifica.csv`) | 39 |
| Nó `CineAreaDetalhada` (`nos/classificacoes/cine_area_detalhada.csv`) | 89 |
| Nó `CineRotulo` (`nos/classificacoes/cine_rotulo.csv`) | 353 |
| Nó `GrauAcademico` (`nos/classificacoes/grau_academico.csv`) | 4 |
| Nó `ModalidadeEnsino` (`nos/classificacoes/modalidade_ensino.csv`) | 2 |
| Nó `NivelAcademico` (`nos/classificacoes/nivel_academico.csv`) | 2 |
| Nó `OrganizacaoAcademica` (`nos/classificacoes/organizacao_academica.csv`) | 5 |
| Nó `Rede` (`nos/classificacoes/rede.csv`) | 2 |
| Nó `CategoriaAdministrativa` (`nos/classificacoes/categoria_administrativa.csv`) | 6 |
| Nó `DimensaoGeografica` (`nos/classificacoes/dimensao_geografica.csv`) | 4 |
| Aresta `PERTENCE_A_REGIAO` (`arestas/geografia/uf_pertence_regiao.csv`) | 27 |
| Aresta `PERTENCE_A_UF` (`arestas/geografia/municipio_pertence_uf.csv`) | 3.551 |
| Aresta `SEDIADA_EM` (`arestas/institucional/ies_sediada_em_municipio.csv`) | 2.561 |
| Aresta `MANTIDA_POR` (`arestas/institucional/ies_mantida_por_mantenedora.csv`) | 2.561 |
| Aresta `TEM_ORGANIZACAO_ACADEMICA` (`arestas/institucional/ies_tem_organizacao_academica.csv`) | 2.561 |
| Aresta `TEM_CATEGORIA_ADMINISTRATIVA` (`arestas/institucional/ies_tem_categoria_administrativa.csv`) | 2.561 |
| Aresta `PERTENCE_A_REDE` (`arestas/institucional/ies_pertence_rede.csv`) | 2.561 |
| Aresta `OFERTADO_POR` (`arestas/academico/curso_ofertado_por_ies.csv`) | 46.150 |
| Aresta `TEM_GRAU_ACADEMICO` (`arestas/academico/curso_tem_grau_academico.csv`) | 46.150 |
| Aresta `TEM_NIVEL_ACADEMICO` (`arestas/academico/curso_tem_nivel_academico.csv`) | 46.150 |
| Aresta `CLASSIFICADO_EM` (`arestas/academico/curso_classificado_em_cine_rotulo.csv`) | 46.150 |
| Aresta `OFERTA_DE` (`arestas/academico/oferta_curso_oferta_de.csv`) | 720.349 |
| Aresta `OFERTADA_POR` (`arestas/academico/oferta_curso_ofertada_por_ies.csv`) | 720.349 |
| Aresta `LOCALIZADA_EM` (`arestas/academico/oferta_curso_localizada_em_municipio.csv`) | 708.571 |
| Aresta `TEM_MODALIDADE_ENSINO` (`arestas/academico/oferta_curso_tem_modalidade_ensino.csv`) | 720.349 |
| Aresta `TEM_DIMENSAO_GEOGRAFICA` (`arestas/academico/oferta_curso_tem_dimensao_geografica.csv`) | 720.349 |
| Aresta `PERTENCE_A_AREA_DETALHADA` (`arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv`) | 353 |
| Aresta `PERTENCE_A_AREA_ESPECIFICA` (`arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv`) | 89 |
| Aresta `PERTENCE_A_AREA_GERAL` (`arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv`) | 39 |

## Verificações

| Verificação | Esperado | Encontrado | Status | Detalhe |
|---|---|---|---|---|
| Linhas do nó nos/geografia/regiao.csv | 5 | 5 | OK |  |
| Label do arquivo nos/geografia/regiao.csv | Regiao | 5/5 corretos | OK |  |
| Linhas do nó nos/geografia/uf.csv | 27 | 27 | OK |  |
| Label do arquivo nos/geografia/uf.csv | UF | 27/27 corretos | OK |  |
| Linhas do nó nos/geografia/municipio.csv | 3.551 | 3.551 | OK |  |
| Label do arquivo nos/geografia/municipio.csv | Municipio | 3551/3551 corretos | OK |  |
| Linhas do nó nos/institucional/ies.csv | 2.561 | 2.561 | OK |  |
| Label do arquivo nos/institucional/ies.csv | IES | 2561/2561 corretos | OK |  |
| Linhas do nó nos/institucional/mantenedora.csv | 1.755 | 1.755 | OK |  |
| Label do arquivo nos/institucional/mantenedora.csv | Mantenedora | 1755/1755 corretos | OK |  |
| Linhas do nó nos/academico/curso.csv | 46.150 | 46.150 | OK |  |
| Label do arquivo nos/academico/curso.csv | Curso | 46150/46150 corretos | OK |  |
| Linhas do nó nos/academico/oferta_curso.csv | 720.349 | 720.349 | OK |  |
| Label do arquivo nos/academico/oferta_curso.csv | OfertaCurso | 720349/720349 corretos | OK |  |
| Linhas do nó nos/classificacoes/cine_area_geral.csv | 11 | 11 | OK |  |
| Label do arquivo nos/classificacoes/cine_area_geral.csv | CineAreaGeral | 11/11 corretos | OK |  |
| Linhas do nó nos/classificacoes/cine_area_especifica.csv | 39 | 39 | OK |  |
| Label do arquivo nos/classificacoes/cine_area_especifica.csv | CineAreaEspecifica | 39/39 corretos | OK |  |
| Linhas do nó nos/classificacoes/cine_area_detalhada.csv | 89 | 89 | OK |  |
| Label do arquivo nos/classificacoes/cine_area_detalhada.csv | CineAreaDetalhada | 89/89 corretos | OK |  |
| Linhas do nó nos/classificacoes/cine_rotulo.csv | 353 | 353 | OK |  |
| Label do arquivo nos/classificacoes/cine_rotulo.csv | CineRotulo | 353/353 corretos | OK |  |
| Linhas do nó nos/classificacoes/grau_academico.csv | 4 | 4 | OK |  |
| Label do arquivo nos/classificacoes/grau_academico.csv | GrauAcademico | 4/4 corretos | OK |  |
| Linhas do nó nos/classificacoes/modalidade_ensino.csv | 2 | 2 | OK |  |
| Label do arquivo nos/classificacoes/modalidade_ensino.csv | ModalidadeEnsino | 2/2 corretos | OK |  |
| Linhas do nó nos/classificacoes/nivel_academico.csv | 2 | 2 | OK |  |
| Label do arquivo nos/classificacoes/nivel_academico.csv | NivelAcademico | 2/2 corretos | OK |  |
| Linhas do nó nos/classificacoes/organizacao_academica.csv | 5 | 5 | OK |  |
| Label do arquivo nos/classificacoes/organizacao_academica.csv | OrganizacaoAcademica | 5/5 corretos | OK |  |
| Linhas do nó nos/classificacoes/rede.csv | 2 | 2 | OK |  |
| Label do arquivo nos/classificacoes/rede.csv | Rede | 2/2 corretos | OK |  |
| Linhas do nó nos/classificacoes/categoria_administrativa.csv | 6 | 6 | OK |  |
| Label do arquivo nos/classificacoes/categoria_administrativa.csv | CategoriaAdministrativa | 6/6 corretos | OK |  |
| Linhas do nó nos/classificacoes/dimensao_geografica.csv | 4 | 4 | OK |  |
| Label do arquivo nos/classificacoes/dimensao_geografica.csv | DimensaoGeografica | 4/4 corretos | OK |  |
| IDs duplicados entre todos os nós | 0 | 0 | OK |  |
| Labels divergentes | 0 | 0 | OK |  |
| Linhas da aresta arestas/geografia/uf_pertence_regiao.csv | 27 | 27 | OK |  |
| Tipo das arestas arestas/geografia/uf_pertence_regiao.csv | PERTENCE_A_REGIAO | 27/27 corretos | OK |  |
| Integridade referencial arestas/geografia/uf_pertence_regiao.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/geografia/uf_pertence_regiao.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/geografia/uf_pertence_regiao.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/geografia/municipio_pertence_uf.csv | 3.551 | 3.551 | OK |  |
| Tipo das arestas arestas/geografia/municipio_pertence_uf.csv | PERTENCE_A_UF | 3551/3551 corretos | OK |  |
| Integridade referencial arestas/geografia/municipio_pertence_uf.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/geografia/municipio_pertence_uf.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/geografia/municipio_pertence_uf.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/institucional/ies_sediada_em_municipio.csv | 2.561 | 2.561 | OK |  |
| Tipo das arestas arestas/institucional/ies_sediada_em_municipio.csv | SEDIADA_EM | 2561/2561 corretos | OK |  |
| Integridade referencial arestas/institucional/ies_sediada_em_municipio.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/institucional/ies_sediada_em_municipio.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/institucional/ies_sediada_em_municipio.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/institucional/ies_mantida_por_mantenedora.csv | 2.561 | 2.561 | OK |  |
| Tipo das arestas arestas/institucional/ies_mantida_por_mantenedora.csv | MANTIDA_POR | 2561/2561 corretos | OK |  |
| Integridade referencial arestas/institucional/ies_mantida_por_mantenedora.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/institucional/ies_mantida_por_mantenedora.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/institucional/ies_mantida_por_mantenedora.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/institucional/ies_tem_organizacao_academica.csv | 2.561 | 2.561 | OK |  |
| Tipo das arestas arestas/institucional/ies_tem_organizacao_academica.csv | TEM_ORGANIZACAO_ACADEMICA | 2561/2561 corretos | OK |  |
| Integridade referencial arestas/institucional/ies_tem_organizacao_academica.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/institucional/ies_tem_organizacao_academica.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/institucional/ies_tem_organizacao_academica.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/institucional/ies_tem_categoria_administrativa.csv | 2.561 | 2.561 | OK |  |
| Tipo das arestas arestas/institucional/ies_tem_categoria_administrativa.csv | TEM_CATEGORIA_ADMINISTRATIVA | 2561/2561 corretos | OK |  |
| Integridade referencial arestas/institucional/ies_tem_categoria_administrativa.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/institucional/ies_tem_categoria_administrativa.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/institucional/ies_tem_categoria_administrativa.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/institucional/ies_pertence_rede.csv | 2.561 | 2.561 | OK |  |
| Tipo das arestas arestas/institucional/ies_pertence_rede.csv | PERTENCE_A_REDE | 2561/2561 corretos | OK |  |
| Integridade referencial arestas/institucional/ies_pertence_rede.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/institucional/ies_pertence_rede.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/institucional/ies_pertence_rede.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/academico/curso_ofertado_por_ies.csv | 46.150 | 46.150 | OK |  |
| Tipo das arestas arestas/academico/curso_ofertado_por_ies.csv | OFERTADO_POR | 46150/46150 corretos | OK |  |
| Integridade referencial arestas/academico/curso_ofertado_por_ies.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/curso_ofertado_por_ies.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/academico/curso_ofertado_por_ies.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/academico/curso_tem_grau_academico.csv | 46.150 | 46.150 | OK |  |
| Tipo das arestas arestas/academico/curso_tem_grau_academico.csv | TEM_GRAU_ACADEMICO | 46150/46150 corretos | OK |  |
| Integridade referencial arestas/academico/curso_tem_grau_academico.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/curso_tem_grau_academico.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/academico/curso_tem_grau_academico.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/academico/curso_tem_nivel_academico.csv | 46.150 | 46.150 | OK |  |
| Tipo das arestas arestas/academico/curso_tem_nivel_academico.csv | TEM_NIVEL_ACADEMICO | 46150/46150 corretos | OK |  |
| Integridade referencial arestas/academico/curso_tem_nivel_academico.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/curso_tem_nivel_academico.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/academico/curso_tem_nivel_academico.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/academico/curso_classificado_em_cine_rotulo.csv | 46.150 | 46.150 | OK |  |
| Tipo das arestas arestas/academico/curso_classificado_em_cine_rotulo.csv | CLASSIFICADO_EM | 46150/46150 corretos | OK |  |
| Integridade referencial arestas/academico/curso_classificado_em_cine_rotulo.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/curso_classificado_em_cine_rotulo.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/academico/curso_classificado_em_cine_rotulo.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/academico/oferta_curso_oferta_de.csv | 720.349 | 720.349 | OK |  |
| Tipo das arestas arestas/academico/oferta_curso_oferta_de.csv | OFERTA_DE | 720349/720349 corretos | OK |  |
| Integridade referencial arestas/academico/oferta_curso_oferta_de.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/oferta_curso_oferta_de.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Linhas da aresta arestas/academico/oferta_curso_ofertada_por_ies.csv | 720.349 | 720.349 | OK |  |
| Tipo das arestas arestas/academico/oferta_curso_ofertada_por_ies.csv | OFERTADA_POR | 720349/720349 corretos | OK |  |
| Integridade referencial arestas/academico/oferta_curso_ofertada_por_ies.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/oferta_curso_ofertada_por_ies.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Linhas da aresta arestas/academico/oferta_curso_localizada_em_municipio.csv | 708.571 | 708.571 | OK |  |
| Tipo das arestas arestas/academico/oferta_curso_localizada_em_municipio.csv | LOCALIZADA_EM | 708571/708571 corretos | OK |  |
| Integridade referencial arestas/academico/oferta_curso_localizada_em_municipio.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/oferta_curso_localizada_em_municipio.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Linhas da aresta arestas/academico/oferta_curso_tem_modalidade_ensino.csv | 720.349 | 720.349 | OK |  |
| Tipo das arestas arestas/academico/oferta_curso_tem_modalidade_ensino.csv | TEM_MODALIDADE_ENSINO | 720349/720349 corretos | OK |  |
| Integridade referencial arestas/academico/oferta_curso_tem_modalidade_ensino.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/oferta_curso_tem_modalidade_ensino.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Linhas da aresta arestas/academico/oferta_curso_tem_dimensao_geografica.csv | 720.349 | 720.349 | OK |  |
| Tipo das arestas arestas/academico/oferta_curso_tem_dimensao_geografica.csv | TEM_DIMENSAO_GEOGRAFICA | 720349/720349 corretos | OK |  |
| Integridade referencial arestas/academico/oferta_curso_tem_dimensao_geografica.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/academico/oferta_curso_tem_dimensao_geografica.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Linhas da aresta arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv | 353 | 353 | OK |  |
| Tipo das arestas arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv | PERTENCE_A_AREA_DETALHADA | 353/353 corretos | OK |  |
| Integridade referencial arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/classificacoes/cine_rotulo_pertence_area_detalhada.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv | 89 | 89 | OK |  |
| Tipo das arestas arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv | PERTENCE_A_AREA_ESPECIFICA | 89/89 corretos | OK |  |
| Integridade referencial arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/classificacoes/cine_area_detalhada_pertence_area_especifica.csv | 0 divergências | 0 divergências | OK |  |
| Linhas da aresta arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv | 39 | 39 | OK |  |
| Tipo das arestas arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv | PERTENCE_A_AREA_GERAL | 39/39 corretos | OK |  |
| Integridade referencial arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv | 0 erros | 0 erros | OK |  |
| Origem única arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv | 0 duplicadas | 0 duplicadas | OK |  |
| Destino exato arestas/classificacoes/cine_area_especifica_pertence_area_geral.csv | 0 divergências | 0 divergências | OK |  |
| LOCALIZADA_EM cobre exatamente as ofertas com município | conjuntos iguais | 708.571 arestas; 708.571 ofertas com município | OK |  |
| TEM_GRAU_ACADEMICO -> grau_NA cobre exatamente os cursos sem grau | conjuntos iguais | 378 arestas; 378 cursos sem grau | OK |  |
| Arestas 1:1 das ofertas (curso, IES, modalidade, dimensão) | 0 divergências | 0 divergências em 720.349 ofertas | OK |  |
| Total de QT_ING | 5.010.613 | 5.010.613 | OK |  |
| Total de QT_ING_FEM | 2.994.997 | 2.994.997 | OK |  |
| Total de QT_ING_MASC | 2.015.616 | 2.015.616 | OK |  |
| Total de QT_MAT | 10.227.266 | 10.227.266 | OK |  |
| Total de QT_MAT_FEM | 6.088.602 | 6.088.602 | OK |  |
| Total de QT_MAT_MASC | 4.138.664 | 4.138.664 | OK |  |
| Total de QT_CONC | 1.333.988 | 1.333.988 | OK |  |
| Total de QT_CONC_FEM | 793.161 | 793.161 | OK |  |
| Total de QT_CONC_MASC | 540.827 | 540.827 | OK |  |
| Total de QT_VG_TOTAL | 23.665.419 | 23.665.419 | OK |  |
| QT_ING_FEM + QT_ING_MASC = QT_ING | 5.010.613 | 5.010.613 | OK |  |
| QT_MAT_FEM + QT_MAT_MASC = QT_MAT | 10.227.266 | 10.227.266 | OK |  |
| QT_CONC_FEM + QT_CONC_MASC = QT_CONC | 1.333.988 | 1.333.988 | OK |  |
| Ofertas com município | 708.571 | 708.571 | OK |  |
| Ofertas sem município | 11.778 | 11.778 | OK |  |
| Ofertas sem município com IN_CAPITAL preenchido | 0 | 0 | OK |  |
| Ofertas com município e IN_CAPITAL vazio | 0 | 0 | OK |  |
| Cursos sem TP_GRAU_ACADEMICO | 378 | 378 | OK |  |
| Distribuição ofertas_por_dimensao | {'1': 34824, '2': 673756, '3': 11319, '4': 450} | {'1': 34824, '2': 673756, '3': 11319, '4': 450} | OK |  |
| Distribuição ofertas_por_modalidade | {'1': 34824, '2': 685525} | {'1': 34824, '2': 685525} | OK |  |
| Distribuição cursos_por_grau | {'1': 27453, '2': 7789, '3': 10530, 'NA': 378} | {'1': 27453, '2': 7789, '3': 10530, 'NA': 378} | OK |  |
| Distribuição cursos_por_nivel | {'1': 46146, '2': 4} | {'1': 46146, '2': 4} | OK |  |
| Distribuição ies_por_rede | {'1': 317, '2': 2244} | {'1': 317, '2': 2244} | OK |  |
| Distribuição ies_por_categoria | {'1': 122, '2': 139, '3': 28, '4': 1486, '5': 758, '7': 28} | {'1': 122, '2': 139, '3': 28, '4': 1486, '5': 758, '7': 28} | OK |  |
| Distribuição ies_por_organizacao | {'1': 206, '2': 417, '3': 1897, '4': 39, '5': 2} | {'1': 206, '2': 417, '3': 1897, '4': 39, '5': 2} | OK |  |

## Observações

- Todas as verificações de contagem, integridade referencial, cardinalidade, hierarquia CINE e totais de controle passaram.
- As arestas 1:1 das ofertas foram conferidas linha a linha.
- A aresta `LOCALIZADA_EM` foi comparada com o conjunto de ofertas que possuem `CO_MUNICIPIO` preenchido.
- As arestas de grau foram conferidas contra os cursos com `TP_GRAU_ACADEMICO` vazio (nó `GrauAcademico` “Não aplicável”).
