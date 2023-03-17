# Ler o arquivo JSON que contém informações sobre todos os repositórios
import json
with open('repos.json') as f:
    repositorios = json.load(f)
# Extrair o nome de cada repositório e adicioná-lo a uma lista
nomes_repositorios = []
for repo in repositorios['value']:
    nomes_repositorios.append(repo['name'])
# Imprimir a lista de nomes dos repositórios
print(nomes_repositorios)

nomes_repositorios_ordenados = sorted(nomes_repositorios)
for nome in nomes_repositorios_ordenados: 
    print(nome)
