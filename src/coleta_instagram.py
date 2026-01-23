import json
import time
import os
import pickle
import platform
import csv
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÃO DO DRIVER ---
def iniciar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=options)

# --- DETECTOR DE BLOQUEIO (HUMAN-IN-THE-LOOP) 🚨 ---
def verificar_bloqueios(driver):
    try:
        url_atual = driver.current_url.lower()
        if "challenge" in url_atual or "login" in url_atual or "checkpoint" in url_atual:
            print("\n" + "█"*50)
            print("🚨 BLOQUEIO DETECTADO NO INSTAGRAM!")
            print("O Instagram deslogou a conta ou pediu verificação (SMS/Código).")
            print("👉 AÇÃO: Vá ao navegador e resolva a verificação.")
            input("👉 DEPOIS: Aperte [ENTER] aqui para continuar...")
            time.sleep(3)
            return True
            
        # Verifica se apareceu a tela "Página não encontrada" (bloqueio ou perfil não existe)
        if "Página não encontrada" in driver.title:
            return False

    except Exception as e: pass
    return False

# --- LÓGICA POR PERFIL ---
def processar_perfil(driver, perfil_alvo):
    dados_finais = {
        "username": perfil_alvo,
        "scraped_at": datetime.now().isoformat(),
        "posts": []
    }

    try:
        url_perfil = f"https://www.instagram.com/{perfil_alvo}/"
        print(f"🔄 Acessando Perfil: {url_perfil}")
        driver.get(url_perfil)
        time.sleep(5) # Espera carregar o perfil

        verificar_bloqueios(driver)

        # 1. Encontra o primeiro post (A tag <a> que leva para /p/ ou /reel/)
        posts_na_tela = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
        
        if len(posts_na_tela) == 0:
            print(f"⚠️ AVISO: Nenhum post encontrado em @{perfil_alvo}.")
            print("🛑 PAUSANDO: Se a página não carregou, dê F5. Se o perfil for privado, o robô não vai conseguir ler.")
            input("Aperte [ENTER] para tentar de novo...")
            time.sleep(3)
            posts_na_tela = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
            if len(posts_na_tela) == 0: return None

        print("👆 Abrindo primeiro post...")
        driver.execute_script("arguments[0].click();", posts_na_tela[0])
        time.sleep(3)

        # 2. Loop de Posts
        quantidade_posts = 5
        
        for i in range(quantidade_posts):
            print(f"   📸 Extraindo post {i+1}/{quantidade_posts}...")
            
            post_data = {
                "descricao": "",
                "likes": 0,
                "comentarios_coletados": [],
                "url": driver.current_url
            }

            try:
                # Extrai a legenda (Descrição)
                try:
                    desc_el = driver.find_element(By.XPATH, "//h1")
                    post_data["descricao"] = desc_el.text
                except: pass

                # Extrai as curtidas
                try:
                    likes_el = driver.find_element(By.XPATH, "//section//span[contains(text(), 'curtidas') or contains(text(), 'likes')]")
                    texto_likes = likes_el.text.split(' ')[0].replace('.', '').replace(',', '')
                    post_data["likes"] = int(texto_likes)
                except: pass

                # Coleta Comentários (Simples)
                try:
                    comentarios_el = driver.find_elements(By.XPATH, "//ul//li")
                    for c_el in comentarios_el[:10]:
                        texto_c = c_el.text
                        linhas = texto_c.split('\n')
                        if len(linhas) >= 2:
                            post_data["comentarios_coletados"].append({
                                "autor": linhas[0],
                                "texto": linhas[1]
                            })
                except: pass

                print(f"      ✅ Likes: {post_data['likes']} | Comentários: {len(post_data['comentarios_coletados'])}")
                dados_finais["posts"].append(post_data)

            except Exception as e:
                print(f"      ⚠️ Erro na leitura do post: {e}")

            # 3. Próximo Post (Clica na setinha para a direita)
            if i < quantidade_posts - 1:
                try:
                    ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
                    time.sleep(3)
                except: break
        
        return dados_finais

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return None

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    driver = iniciar_driver()
    try:
        print("🍪 Injetando Cookies do Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(2)
        
        diretorio_src = os.path.dirname(os.path.abspath(__file__))
        caminho_cookie = os.path.join(diretorio_src, "config", "instagram", "logins_instagram", "instagram_cookies.pkl")
        
        try:
            cookies = pickle.load(open(caminho_cookie, "rb"))
            for cookie in cookies: driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(4)
        except: print("⚠️ AVISO: Sem cookies. Rodando deslogado (Alto risco de bloqueio).")

        pasta_data = os.path.join(diretorio_src, "..", "data")
        caminho_csv = os.path.join(pasta_data, "famosos_instagram.csv")
        
        if os.path.exists(caminho_csv):
            with open(caminho_csv, "r", encoding="utf-8") as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    perfil = linha["nome_do_perfil"].strip()
                    if perfil:
                        print(f"\n📌 PROCESSANDO: {perfil}")
                        resultado = processar_perfil(driver, perfil)
                        if resultado:
                            caminho_json = os.path.join(pasta_data, f"instagram_{perfil}_data.json")
                            with open(caminho_json, 'w', encoding='utf-8') as f:
                                json.dump(resultado, f, ensure_ascii=False, indent=4)
                            print("✨ JSON Salvo!")
                            time.sleep(random.randint(15, 25))
    finally:
        driver.quit()
        print("\n🏁 Fim.")