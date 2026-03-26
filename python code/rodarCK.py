import os
import subprocess
import pandas as pd

CK_JAR = "ck.jar"  # caminho do seu jar
REPOS_DIR = "repos"
RESULTS_DIR = "ck_results"

os.makedirs(RESULTS_DIR, exist_ok=True)

resultados = []

for repo_folder in os.listdir(REPOS_DIR):
    repo_path = os.path.join(REPOS_DIR, repo_folder)

    if not os.path.isdir(repo_path):
        continue

    print(f"🔍 Analisando {repo_folder}...")

    try:
        subprocess.run(
            ["java", "-jar", CK_JAR, repo_path, "true", "0", "false"],
            check=True
        )

        if os.path.exists("class.csv"):
            df = pd.read_csv("class.csv")

            resumo = {
                "name": repo_folder,

                "cbo_mean": df["cbo"].mean(),
                "cbo_std": df["cbo"].std(),

                "dit_mean": df["dit"].mean(),
                "dit_std": df["dit"].std(),

                "lcom_mean": df["lcom"].mean(),
                "lcom_std": df["lcom"].std(),
            }

            resultados.append(resumo)

            os.rename("class.csv", f"{RESULTS_DIR}/{repo_folder}_class.csv")

    except Exception as e:
        print(f"❌ Erro em {repo_folder}: {e}")

df_final = pd.DataFrame(resultados)
df_final.to_csv("ck_summary.csv", index=False)

print("✅ CK finalizado!")