# -*- coding: utf-8 -*-
"""
Utilitário para leitura, filtragem, análise e exportação de repositórios
a partir do JSON da API do Azure DevOps (repos.json).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional


@dataclass(frozen=True)
class Repositorio:
    """Representa os metadados principais de um repositório do Azure DevOps."""

    id: str
    name: str
    project_name: str
    default_branch: str
    size_bytes: int
    web_url: str
    ssh_url: str
    remote_url: str
    is_disabled: bool
    is_in_maintenance: bool
    last_update_time: str

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 2)

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def is_empty(self) -> bool:
        return self.size_bytes == 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Repositorio:
        project = data.get("project") or {}
        branch_raw = data.get("defaultBranch") or ""
        branch_clean = branch_raw.replace("refs/heads/", "") if branch_raw else "(sem branch)"

        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")).strip(),
            project_name=str(project.get("name", "Desconhecido")).strip(),
            default_branch=branch_clean,
            size_bytes=int(data.get("size") or 0),
            web_url=str(data.get("webUrl", "")),
            ssh_url=str(data.get("sshUrl", "")),
            remote_url=str(data.get("remoteUrl", "")),
            is_disabled=bool(data.get("isDisabled", False)),
            is_in_maintenance=bool(data.get("isInMaintenance", False)),
            last_update_time=str(project.get("lastUpdateTime", "")),
        )


def carregar_repositorios(caminho_json: Path) -> tuple[List[Repositorio], Optional[int]]:
    """
    Lê o arquivo JSON de repositórios com codificação UTF-8 segura.

    Returns:
        tuple: (Lista de objetos Repositorio, valor do campo 'count' declarado no JSON)
    """
    if not caminho_json.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: '{caminho_json}'")

    with caminho_json.open("r", encoding="utf-8-sig") as f:
        payload = json.load(f)

    # Suporta tanto o formato {"value": [...], "count": N} quanto uma lista direta [...]
    if isinstance(payload, dict):
        itens_brutos = payload.get("value", [])
        count_declarado = payload.get("count")
    elif isinstance(payload, list):
        itens_brutos = payload
        count_declarado = len(itens_brutos)
    else:
        raise ValueError("Formato JSON inválido: esperado objeto com chave 'value' ou lista.")

    repositorios = [
        Repositorio.from_dict(item)
        for item in itens_brutos
        if isinstance(item, dict) and item.get("name")
    ]
    return repositorios, count_declarado


def filtrar_e_ordenar(
    repositorios: Iterable[Repositorio],
    projeto: Optional[str] = None,
    busca: Optional[str] = None,
    ignorar_vazios: bool = False,
    ordenar_por: str = "nome",
) -> List[Repositorio]:
    """Filtra e ordena a lista de repositórios de forma case-insensitive."""
    resultado = list(repositorios)

    if projeto:
        projeto_lower = projeto.casefold()
        resultado = [r for r in resultado if r.project_name.casefold() == projeto_lower]

    if busca:
        busca_lower = busca.casefold()
        resultado = [r for r in resultado if busca_lower in r.name.casefold()]

    if ignorar_vazios:
        resultado = [r for r in resultado if not r.is_empty]

    if ordenar_por == "tamanho":
        resultado.sort(key=lambda r: (r.size_bytes, r.name.casefold()), reverse=True)
    elif ordenar_por == "projeto":
        resultado.sort(key=lambda r: (r.project_name.casefold(), r.name.casefold()))
    else:
        # Ordenação alfabética case-insensitive (evita que maiúsculas fiquem todas antes das minúsculas)
        resultado.sort(key=lambda r: r.name.casefold())

    return resultado


def exportar_csv(repositorios: Iterable[Repositorio], caminho_csv: Path) -> None:
    """Exporta os metadados completos dos repositórios para um arquivo CSV."""
    campos = [
        "name",
        "project_name",
        "default_branch",
        "size_bytes",
        "size_mb",
        "is_empty",
        "is_disabled",
        "web_url",
        "ssh_url",
        "id",
    ]
    with caminho_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for repo in repositorios:
            writer.writerow(
                {
                    "name": repo.name,
                    "project_name": repo.project_name,
                    "default_branch": repo.default_branch,
                    "size_bytes": repo.size_bytes,
                    "size_mb": repo.size_mb,
                    "is_empty": repo.is_empty,
                    "is_disabled": repo.is_disabled,
                    "web_url": repo.web_url,
                    "ssh_url": repo.ssh_url,
                    "id": repo.id,
                }
            )


def exibir_resumo(repositorios: List[Repositorio], count_declarado: Optional[int]) -> None:
    """Exibe estatísticas gerais e listagem ordenada dos repositórios no terminal."""
    total_carregados = len(repositorios)
    vazios = [r for r in repositorios if r.is_empty]
    contagem_projetos = Counter(r.project_name for r in repositorios)
    tamanho_total_mb = sum(r.size_bytes for r in repositorios) / (1024 * 1024)

    print("=" * 75)
    print(f"RESUMO DOS REPOSITÓRIOS ({total_carregados} carregados)")
    if count_declarado is not None and count_declarado != total_carregados:
        print(
            f"[NOTA] O campo 'count' do JSON indica {count_declarado}, mas há "
            f"{total_carregados} itens presentes na lista 'value' (resposta paginada da API)."
        )
    print(f"Tamanho total acumulado: {tamanho_total_mb:,.2f} MB")
    print("Distribuição por projeto:")
    for proj, qtd in contagem_projetos.most_common():
        print(f"  - {proj}: {qtd} repositório(s)")
    if vazios:
        nomes_vazios = ", ".join(r.name for r in vazios)
        print(f"Repositórios vazios (0 bytes / sem branch): {len(vazios)} ({nomes_vazios})")
    print("=" * 75)

    print(f"\n{'#':>3} | {'REPOSITÓRIO':<52} | {'PROJETO':<16} | {'BRANCH':<12} | {'TAMANHO':>10}")
    print("-" * 103)
    for idx, repo in enumerate(repositorios, start=1):
        tamanho_fmt = (
            f"{repo.size_mb:,.2f} MB"
            if repo.size_bytes >= 1024 * 1024
            else f"{repo.size_kb:,.1f} KB"
        )
        print(
            f"{idx:>3} | {repo.name:<52} | {repo.project_name:<16} | "
            f"{repo.default_branch:<12} | {tamanho_fmt:>10}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lê, filtra, ordena e exporta repositórios do arquivo repos.json."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("repos.json"),
        help="Caminho para o arquivo JSON de entrada (padrão: repos.json).",
    )
    parser.add_argument(
        "-p",
        "--projeto",
        type=str,
        default=None,
        help="Filtra repositórios por nome do projeto.",
    )
    parser.add_argument(
        "-b",
        "--busca",
        type=str,
        default=None,
        help="Filtra repositórios que contenham o termo no nome.",
    )
    parser.add_argument(
        "--ignorar-vazios",
        action="store_true",
        help="Oculta repositórios com tamanho igual a 0 bytes.",
    )
    parser.add_argument(
        "-s",
        "--ordenar",
        choices=["nome", "tamanho", "projeto"],
        default="nome",
        help="Critério de ordenação: 'nome' (padrão, case-insensitive), 'tamanho' ou 'projeto'.",
    )
    parser.add_argument(
        "--apenas-nomes",
        action="store_true",
        help="Imprime apenas os nomes dos repositórios (um por linha).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Caminho opcional para exportar o resultado em CSV (ex: repositorios.csv).",
    )

    args = parser.parse_args()

    repositorios, count_declarado = carregar_repositorios(args.input)
    repos_filtrados = filtrar_e_ordenar(
        repositorios,
        projeto=args.projeto,
        busca=args.busca,
        ignorar_vazios=args.ignorar_vazios,
        ordenar_por=args.ordenar,
    )

    if args.apenas_nomes:
        for repo in repos_filtrados:
            print(repo.name)
    else:
        exibir_resumo(repos_filtrados, count_declarado)

    if args.csv:
        exportar_csv(repos_filtrados, args.csv)
        print(f"\n[OK] Arquivo CSV exportado em: {args.csv.resolve()}")


if __name__ == "__main__":
    main()
