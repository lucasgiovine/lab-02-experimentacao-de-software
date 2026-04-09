import requests
import subprocess
import os
import time
import pandas as pd
from datetime import datetime
from multiprocessing import Pool, cpu_count

# =========================
# CONFIGURAÇÕES
# =========================
GITHUB_TOKEN = os.getenv("")  # ⚠️ coloque no sistema
CK_JAR_PATH = "ck.jar"
REPOS_DIR = r"C:\Users\themo\OneDrive\Desktop\trab githuuubbbbb\repositorios"
MAX_REPOS = 1000
REPOS_POR_PAGINA = 100
OUTPUT_CSV = "resultados.csv"

os.makedirs(REPOS_DIR, exist_ok=True)

queries = [
    "language:Java stars:>50000",
    "language:Java stars:10000..50000",
    "language:Java stars:5000..10000",
    "language:Java stars:1000..5000",
    "language:Java stars:500..1000"
]
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else None
}


def buscar_repos():
    repos_dict = {}

    for q in queries:
        print(f"\n🔎 Buscando: {q}")
        pagina = 1

        while True:
            url = (
                f"https://api.github.com/search/repositories"
                f"?q={q}&sort=stars&order=desc"
                f"&page={pagina}&per_page={REPOS_POR_PAGINA}"
            )

            response = requests.get(url, headers=HEADERS)

            if response.status_code != 200:
                print("Erro API:", response.status_code)
                time.sleep(5)
                continue

            data = response.json()

            if "items" not in data or not data["items"]:
                break

            for item in data["items"]:
                repos_dict[item["full_name"]] = {
                "nome": item["full_name"],
                "clone_url": item["clone_url"],
                "stars": item["stargazers_count"],
                "created_at": item["created_at"],
                "releases": item.get("releases_url", "").replace("{/id}", "")
            }

            print(f"Página {pagina} → Total: {len(repos_dict)}")

            if len(repos_dict) >= MAX_REPOS:
                break

            pagina += 1
            time.sleep(1)

        if len(repos_dict) >= MAX_REPOS:
            break

    repos = sorted(repos_dict.values(), key=lambda x: x["stars"], reverse=True)
    return repos[:MAX_REPOS]

def clonar_repo(repo):
    nome_repo = repo["nome"]
    nome_pasta = nome_repo.replace("/", "_")
    caminho = os.path.join(REPOS_DIR, nome_pasta)

    print(f"Clonando: {nome_repo}")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo["clone_url"], caminho],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return caminho
    except:
        print(f"Erro ao clonar: {nome_repo}")
        return None


def rodar_ck(pasta_repo):
    nome = os.path.basename(pasta_repo)
    pasta_temp = f"temp_{nome}"

    os.makedirs(pasta_temp, exist_ok=True)

    # se já tem resultado, não roda de novo
    if os.path.exists(os.path.join(pasta_temp, "class.csv")):
        return pasta_temp

    print(f"Rodando CK: {nome}")

    try:
        subprocess.run([
            "java", "-jar", os.path.abspath(CK_JAR_PATH),
            os.path.abspath(pasta_repo),
            "false", "0", "true"
        ],
        stdout=None,  
        stderr=None,
        check=True)

    except subprocess.CalledProcessError:
        print(f"Erro no CK: {nome}")
        return None

    arquivos = ["class.csv", "method.csv", "field.csv"]

    for arq in arquivos:
        if os.path.exists(arq):
            os.replace(arq, os.path.join(pasta_temp, arq))

    if not os.path.exists(os.path.join(pasta_temp, "class.csv")):
        print(f"CK não gerou class.csv: {nome}")
        return None

    return pasta_temp


def extrair_metricas(repo, pasta_temp):
    try:
        caminho_csv = os.path.join(pasta_temp, "class.csv")

        if not os.path.exists(caminho_csv):
            return None

        df = pd.read_csv(caminho_csv)

        cbo = df["cbo"].mean()
        dit = df["dit"].mean()
        lcom = df["lcom"].mean()

        idade = (
            datetime.now() - datetime.fromisoformat(
                repo["created_at"].replace("Z", "")
            )
        ).days / 365

        return {
            "repo": repo["nome"],
            "stars": repo["stars"],
            "idade": idade,
            "cbo": cbo,
            "dit": dit,
            "lcom": lcom
        }

    except:
        return None


def contar_releases(repo):
    url = repo["releases"]

    if not url:
        return 0

    try:
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            return 0

        data = response.json()
        return len(data)

    except:
        return 0

def processar_repo(repo):
    nome = repo["nome"]
    nome_pasta = nome.replace("/", "_")

    print(f"{nome}")

    caminho_repo = os.path.join(REPOS_DIR, nome_pasta)
    pasta_temp = f"temp_{nome_pasta}"

    if os.path.exists(os.path.join(pasta_temp, "class.csv")):
        print(f"CK já pronto: {nome}")
        dados = extrair_metricas(repo, pasta_temp)
    else:
        pasta = clonar_repo(repo)
        if not pasta:
            return None

        temp = rodar_ck(pasta)
        if not temp:
            return None

        dados = extrair_metricas(repo, temp)

    if not dados:
        return None

    try:
        pasta = os.path.join(REPOS_DIR, nome_pasta)
        dados["loc"] = calcular_loc(pasta)

        dados["releases"] = contar_releases(repo)

    except:
        pass

    return dados

def salvar_resultado(resultado):
    df = pd.DataFrame([resultado])

    if not os.path.exists(OUTPUT_CSV):
        df.to_csv(OUTPUT_CSV, index=False)
    else:
        df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False)


def calcular_loc(pasta_repo):
    total = 0

    for root, _, files in os.walk(pasta_repo):
        for file in files:
            if file.endswith(".java"):
                caminho = os.path.join(root, file)
                try:
                    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                        total += sum(1 for _ in f)
                except:
                    pass

    return total

def main():
    repos = buscar_repos()

    repos_processados = carregar_repos_processados()

    repos = [r for r in repos if r["nome"] not in repos_processados]

    print(f"\nJá processados: {len(repos_processados)}")
    print(f"Restantes: {len(repos)}")

    num_processos = max(2, cpu_count() // 2)

    with Pool(processes=num_processos) as pool:
        for resultado in pool.imap_unordered(processar_repo, repos):
            if resultado:
                salvar_resultado(resultado)

    print("\nArquivo atualizado:", OUTPUT_CSV)

if __name__ == "__main__":
    main()