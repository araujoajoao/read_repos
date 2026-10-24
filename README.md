# Read Repos (`repos.py`)

Utilitário de linha de comando (CLI) em Python para inspeção, filtragem, ordenação, análise estatística e exportação de repositórios Git a partir de payloads JSON da API do **Azure DevOps**.

---

## 📌 O que o script faz?

O script [`repos.py`](repos.py) foi projetado para analisar o arquivo exportado da API do Azure DevOps (`repos.json`), oferecendo:

1. **Leitura Resiliente do JSON**:
   - Compatível com a codificação UTF-8 com ou sem BOM (`utf-8-sig`).
   - Suporta tanto a estrutura padrão da API REST (`{"value": [...], "count": N}`) quanto arrays puros de repositórios (`[...]`).
   - Alerta sobre divergências entre a contagem declarada (`count`) e o total de registros contidos (detecção de paginação).

2. **Filtros e Busca**:
   - **Por Projeto**: Filtra repositórios pertencentes a um projeto específico (busca insensível a maiúsculas/minúsculas).
   - **Por Nome**: Localiza repositórios que contenham determinado termo no nome.
   - **Repositórios Vazios**: Permite ignorar repositórios que contenham 0 bytes ou estejam sem branch padrão.

3. **Ordenação Inteligente**:
   - Por **nome** (alfabética, *case-insensitive* para evitar ordenação lexicográfica distorcida).
   - Por **tamanho** (decrescente, do maior para o menor repositório).
   - Por **projeto** (agrupados por projeto e ordenados por nome).

4. **Visualização no Terminal**:
   - **Painel de Métricas**: Total de repositórios, tamanho acumulado em MB, distribuição por projeto e listagem de repositórios vazios.
   - **Tabela Formatada**: Exibição tabular com colunas `#`, `REPOSITÓRIO`, `PROJETO`, `BRANCH` e `TAMANHO` (formatado dinamicamente em KB ou MB).
   - **Modo Pipeline (`--apenas-nomes`)**: Imprime somente os nomes (um por linha) para integração com scripts shell, `xargs`, `git clone`, etc.

5. **Exportação CSV**:
   - Gera relatórios em `.csv` (com suporte a acentuação e Excel via `utf-8-sig`) contendo metadados completos: URLs de clone (Web/SSH), branches, IDs, status de manutenção e tamanhos.

---

## 🚀 Requisitos

- **Python 3.9+** (ou 3.7+ com `from __future__ import annotations`).
- **Sem dependências externas**: Utiliza apenas módulos da biblioteca padrão do Python (`argparse`, `csv`, `json`, `dataclasses`, `pathlib`, `collections`).

---

## 📥 Como obter o arquivo `repos.json`

O arquivo de entrada pode ser obtido através da API REST do Azure DevOps:

```bash
# Exemplo via cURL com Personal Access Token (PAT)
curl -u :<SEU_PAT> \
  "https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=7.0" \
  -o repos.json
```

---

## ⚙️ Parâmetros da Linha de Comando (CLI)

| Parâmetro | Tipo | Descrição | Padrão |
| :--- | :--- | :--- | :--- |
| `-i`, `--input` | `Path` | Caminho do arquivo JSON de entrada | `repos.json` |
| `-p`, `--projeto` | `str` | Filtra pelo nome exato do projeto (*case-insensitive*) | `None` |
| `-b`, `--busca` | `str` | Filtra repositórios que contenham o termo no nome | `None` |
| `--ignorar-vazios` | `flag` | Oculta repositórios vazios (0 bytes / sem branch) | `False` |
| `-s`, `--ordenar` | `choice` | Critério de ordenação: `nome`, `tamanho` ou `projeto` | `nome` |
| `--apenas-nomes` | `flag` | Exibe apenas os nomes dos repositórios, um por linha | `False` |
| `--csv` | `Path` | Caminho do arquivo para exportação em CSV | `None` |

---

## 💡 Exemplos de Uso

### 1. Resumo padrão com tabela
Lê o arquivo `repos.json` local e exibe o resumo completo no terminal:
```bash
python repos.py
```

### 2. Informar outro arquivo JSON
```bash
python repos.py -i caminho/para/meus_repos.json
```

### 3. Filtrar por projeto e ignorar repositórios vazios
```bash
python repos.py --projeto "DevOps-Core" --ignorar-vazios
```

### 4. Buscar repositórios por termo e ordenar pelo maior tamanho
```bash
python repos.py --busca "api" --ordenar tamanho
```

### 5. Exportar resultado filtrado para CSV
```bash
python repos.py --projeto "Pagamentos" --ordenar tamanho --csv relatorio_pagamentos.csv
```

### 6. Pipeline: Clonar todos os repositórios de um projeto
```bash
python repos.py --projeto "MeuProjeto" --ignorar-vazios --apenas-nomes | while read repo; do
  git clone "https://dev.azure.com/{org}/{project}/_git/$repo"
done
```

---

## 📄 Estrutura do Arquivo CSV Exportado

Quando o parâmetro `--csv` é utilizado, as seguintes colunas são geradas:

- `name`: Nome do repositório
- `project_name`: Nome do projeto pai no Azure DevOps
- `default_branch`: Branch padrão (ex: `main`, `master`)
- `size_bytes`: Tamanho em bytes
- `size_mb`: Tamanho convertido para megabytes
- `is_empty`: Booleano (`True`/`False`) indicando se o repositório é vazio
- `is_disabled`: Booleano indicando se o repositório está desativado
- `web_url`: URL de visualização no navegador
- `ssh_url`: URL de clone via SSH
- `id`: Identificador único (UUID) do repositório