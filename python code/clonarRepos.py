import pandas as pd
import os
import subprocess
import time

CSV_PATH = "github_java_repos.csv"
BASE_DIR = "repos"

os.makedirs(BASE_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)

for _, row in df.iterrows():
    repo_name = row["name"]
    repo_url = f"https://github.com/{repo_name}.git"
    
    repo_folder = repo_name.replace("/", "_")
    repo_path = os.path.join(BASE_DIR, repo_folder)

    if os.path.exists(repo_path):
        print(f"⏩ Já existe: {repo_name}")
        continue

    print(f"⬇️ Clonando {repo_name}...")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, repo_path],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"❌ Erro ao clonar {repo_name}")
    
    time.sleep(0.5)