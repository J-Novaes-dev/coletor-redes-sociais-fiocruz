import instaloader
import json
import csv
import os
import time
import random
from datetime import datetime

# --- 1. CONFIGURAÇÃO E LOGIN ---

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

usuario_sessao = "carolbrito2110"

# --- NOVA LÓGICA DE CAMINHO (PROFISSIONAL) ---
# src/
diretorio_src = os.path.dirname(os.path.abspath(__file__))
# src/config/instagram/logins_instagram/session-usuario
caminho_sessao = os.path.join(diretorio_src, "config", "instagram", "logins_instagram", f"session-{usuario_sessao}")

try:
    print(f"🔐 Buscando credenciais em: {caminho_sessao}")
    L.load_session_from_file(usuario_sessao, filename=caminho_sessao)
    print("✅ Login carregado com sucesso!")
except FileNotFoundError:
    print("❌ ERRO CRÍTICO: Arquivo de sessão não encontrado.")
    print(f"Esperado em: {caminho_sessao}")
    print("Dica: Vá em 'src/config/instagram/' e rode o 'setup_login_instagram.py'.")
    exit()

# --- 2. FUNÇÃO DE EXTRAÇÃO ---

def extrair_dados_perfil(username):
    print(f"🔄 Iniciando coleta para o perfil: {username}...")
    
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        dados_coletados = {
            "platform": "instagram",
            "scraped_at": datetime.now().isoformat(),
            "profile_info": {
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "is_verified": profile.is_verified,
                "followers_count": profile.followers,
                "following_count": profile.followees,
                "external_url": profile.external_url,
                "profile_image_url": profile.profile_pic_url
            },
            "posts": []
        }

        print("📥 Baixando posts...")
        count_posts = 0
        max_posts = 5  # Mantenha baixo para evitar bloqueios
        
        posts = profile.get_posts()
        
        for post in posts:
            if count_posts >= max_posts:
                break

            # Pausa aleatória entre posts
            tempo_pausa = random.randint(5, 15) 
            print(f"   ⏳ Lendo post... aguardando {tempo_pausa}s")
            time.sleep(tempo_pausa)

            content_type = "image"
            if post.is_video: content_type = "video"
            elif post.typename == "GraphSidecar": content_type = "carousel"

            # Coleta de Comentários (Limitada)
            comentarios = []
            max_comments = 20
            count_comments = 0

            try:
                for comentario in post.get_comments():
                    if count_comments >= max_comments: break
                    comentarios.append({
                        "username": comentario.owner.username,
                        "text": comentario.text,
                        "created_at": comentario.created_at_utc.isoformat()
                    })
                    count_comments += 1
            except Exception as e:
                print(f"   ⚠️ Erro leve nos comentários: {e}")

            post_data = {
                "post_id": post.shortcode,
                "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                "publish_date": post.date_utc.isoformat(),
                "content_type": content_type,
                "caption": post.caption if post.caption else "",
                "hashtags": post.caption_hashtags,
                "metrics": {
                    "likes_count": post.likes,
                    "comments_count": post.comments,
                    "views_count": post.video_view_count if post.is_video else 0
                },
                "comments": comentarios
            }
            
            dados_coletados["posts"].append(post_data)
            count_posts += 1
            print(f"   ✅ Post {post.shortcode} coletado com {len(comentarios)} comentários")

        return dados_coletados

    except Exception as e:
        mensagem_erro = str(e)
        print(f"❌ Ocorreu um erro no perfil {username}: {mensagem_erro}")
        
        # --- FREIO DE EMERGÊNCIA 🚨 ---
        # Se o erro for de bloqueio, retorna um código especial para parar tudo
        if "401" in mensagem_erro or "429" in mensagem_erro or "Redirected to login" in mensagem_erro:
            return "BLOQUEIO_DETECTADO"
            
        return None


# --- 3. EXECUÇÃO EM LOTE ---

if __name__ == "__main__":
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    pasta_data = os.path.join(diretorio_atual, "..", "data")
    caminho_csv = os.path.join(pasta_data, "famosos_instagram.csv")

    if not os.path.exists(pasta_data): os.makedirs(pasta_data)

    if not os.path.exists(caminho_csv):
        print(f"❌ ARQUIVO CSV NÃO ENCONTRADO EM: {caminho_csv}")
    else:
        with open(caminho_csv, "r", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            
            if "nome_do_perfil" not in leitor.fieldnames:
                print("❌ ERRO NO CSV: A primeira linha deve ser 'nome_do_perfil'.")
            else:
                for linha in leitor:
                    perfil_alvo = linha["nome_do_perfil"].strip()
                    if not perfil_alvo: continue

                    print("\n==============================")
                    print(f"📌 PROCESSANDO: {perfil_alvo}")
                    print("==============================")

                    resultado = extrair_dados_perfil(perfil_alvo)

                    # --- VERIFICAÇÃO DO FREIO DE EMERGÊNCIA ---
                    if resultado == "BLOQUEIO_DETECTADO":
                        print("\n" + "█"*50)
                        print("🚨 ALERTA MÁXIMO: INSTAGRAM BLOQUEOU TEMPORARIAMENTE 🚨")
                        print("Motivo: Muitas requisições (Erro 401/429).")
                        print("Ação: O script foi interrompido para proteger a conta.")
                        print("Recomendação: Espere 2 a 4 horas antes de tentar de novo.")
                        print("█"*50 + "\n")
                        break # Encerra o loop e o programa

                    if resultado:
                        caminho_json = os.path.join(pasta_data, f"instagram_{perfil_alvo}_data.json")
                        with open(caminho_json, 'w', encoding='utf-8') as f:
                            json.dump(resultado, f, ensure_ascii=False, indent=4)
                        print(f"✨ SUCESSO! Dados salvos em: {caminho_json}")
                    
                        tempo_descanso = random.randint(30, 60)
                        print(f"💤 Descansando {tempo_descanso}s antes do próximo perfil...")
                        time.sleep(tempo_descanso)
                    else:
                        print(f"⚠️ Pulanado {perfil_alvo} devido a erro.")