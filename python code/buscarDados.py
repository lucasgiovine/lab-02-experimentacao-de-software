import requests
import pandas as pd
import time
import os
from dateutil import parser
from datetime import datetime, timezone


GITHUB_TOKEN = "TOKEN"

if not GITHUB_TOKEN:
    raise Exception("Defina a variável de ambiente GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "python-script"
}

BASE_URL = "https://api.github.com"

def safe_get(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 403:
            print("Rate limit atingido. Aguardando...")
            time.sleep(60)
            return safe_get(url, params)

        else:
            print(f"Erro {response.status_code} em {url}")
            return None

    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None


def get_releases_count(repo):
    url = f"{BASE_URL}/repos/{repo}/releases"
    data = safe_get(url)
    return len(data) if data else 0

def get_pr_count(repo):
    url = f"{BASE_URL}/search/issues"
    params = {"q": f"repo:{repo} type:pr"}
    data = safe_get(url, params)
    return data["total_count"] if data else 0

def get_contributors_count(repo):
    url = f"{BASE_URL}/repos/{repo}/contributors"
    data = safe_get(url)
    return len(data) if data else 0

def get_commit_count(repo):
    url = f"{BASE_URL}/repos/{repo}/commits"
    params = {"per_page": 100}
    data = safe_get(url, params)
    return len(data) if data else 0  

def calcular_idade(data_criacao):
    created = parser.parse(data_criacao)
    agora = datetime.now(timezone.utc)
    return round((agora - created).days / 365, 2)


def coletar_repos():
    repos_data = []

    query = "language:Java stars:>100"

    for page in range(1, 11):  
        print(f"Coletando página {page}...")

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": page
        }

        data = safe_get(f"{BASE_URL}/search/repositories", params)

        if not data or "items" not in data:
            print("Erro ao coletar dados")
            continue

        for repo in data["items"]:
            name = repo["full_name"]

            print(f"➡️ Processando {name}")

            repos_data.append({
                "name": repo["full_name"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "watchers": repo["watchers_count"],
                "size_kb": repo["size"],
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "pushed_at": repo["pushed_at"],
                "idade_anos": calcular_idade(repo["created_at"])
            })

            time.sleep(0.7)  

    return pd.DataFrame(repos_data)


if __name__ == "__main__":
    df = coletar_repos()

    print("Salvando CSV...")
    df.to_csv("github_java_repos.csv", index=False)

    print("Finalizado com sucesso!")