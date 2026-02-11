import os
import json
from huggingface_hub import InferenceClient

# Caminho base do projeto (sobe um nível saindo de src)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

api_key = os.environ.get("HF_TOKEN")

# Inicializa cliente HuggingFace
client = InferenceClient(
    provider="hf-inference",
    api_key=api_key,
)

# Percorre todos os arquivos da pasta data
for nome_arquivo in os.listdir(DATA_DIR):

    if nome_arquivo.endswith(".json"):
        caminho_json = os.path.join(DATA_DIR, nome_arquivo)

        print(f"\n Processando arquivo: {nome_arquivo}")

        with open(caminho_json, "r", encoding="utf-8") as file:
            dados = json.load(file)

        # Percorre posts
        for post in dados.get("posts", []):
            comentarios = post.get("comentarios_coletados", [])

            for comentario in comentarios:
                texto = comentario.get("texto", "").strip()

                if texto:
                    try:
                        resultado = client.text_classification(
                            texto,
                            model="tabularisai/multilingual-sentiment-analysis",
                        )

                        print("Texto:", texto)
                        print("Análise:", resultado)
                        print("-" * 50)

                    except Exception as e:
                        print("Erro ao analisar:", texto)
                        print("Erro:", e)
                        print("-" * 50)