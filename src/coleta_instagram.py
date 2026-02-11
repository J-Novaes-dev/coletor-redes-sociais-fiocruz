import json
import time
import os
import pickle
import platform
import csv
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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

# --- DETECTOR DE BLOQUEIO ---
def verificar_bloqueios(driver):
    try:
        url_atual = driver.current_url.lower()
        if "challenge" in url_atual or "login" in url_atual or "checkpoint" in url_atual:
            print("\n" + "█"*50)
            print("🚨 BLOQUEIO DETECTADO NO INSTAGRAM!")
            print("👉 AÇÃO: Vá ao navegador e resolva a verificação.")
            input("👉 DEPOIS: Aperte [ENTER] aqui para continuar...")
            time.sleep(3)
            return True
        if "Página não encontrada" in driver.title: return False
    except: pass
    return False

# --- O "CAÇADOR DE LIKES" DEFINITIVO 🎯 ---
def extrair_numero_likes(texto):
    """Converte textos como '1,2 mil', '1.200' ou 'outras 34 pessoas' em números inteiros"""
    if not texto: return 0
    texto = texto.lower().replace(',', '.').strip()
    
    # Caso 1: "outras 34 pessoas" (Likes ocultos)
    if 'outra' in texto or 'pessoa' in texto:
        numeros = re.sub(r'[^0-9]', '', texto)
        return int(numeros) + 1 if numeros else 0
        
    # Caso 2: Padrões "mil" e "mi"
    multiplicador = 1
    if 'mil' in texto or 'k' in texto: multiplicador = 1000
    elif 'mi' in texto or 'm' in texto: multiplicador = 1000000

    numeros = re.sub(r'[^0-9.]', '', texto)
    try:
        if '.' in numeros and multiplicador > 1:
            return int(float(numeros) * multiplicador)
        return int(numeros.replace('.', ''))
    except: return 0

def caçar_likes(driver):
    """Busca o número de likes usando as âncoras mais estáveis do Instagram"""
    try:
        # TENTATIVA 1: O Link Direto (O mais preciso para fotos)
        # O link que abre a lista de quem curtiu SEMPRE tem '/liked_by/' no endereço.
        try:
            elemento_link = driver.find_element(By.XPATH, "//a[contains(@href, '/liked_by/')]")
            return extrair_numero_likes(elemento_link.text)
        except: pass

        # TENTATIVA 2: Busca por texto exato (Para vídeos/Reels onde a palavra "curtidas" ou "likes" aparece)
        try:
            elementos = driver.find_elements(By.XPATH, "//*[contains(text(), 'curtida') or contains(text(), 'like')]")
            for el in elementos:
                if any(char.isdigit() for char in el.text):
                    return extrair_numero_likes(el.text)
        except: pass

        # TENTATIVA 3: Acessibilidade (Aria-Label)
        # Procura qualquer elemento que o leitor de tela leia como "X curtidas"
        try:
            elementos_aria = driver.find_elements(By.XPATH, "//*[@aria-label]")
            for el in elementos_aria:
                aria = el.get_attribute("aria-label").lower()
                if 'curtida' in aria or 'like' in aria:
                    if any(char.isdigit() for char in aria):
                        return extrair_numero_likes(aria)
        except: pass

    except: pass
    return 0

# --- LÓGICA POR PERFIL ---
def processar_perfil(driver, perfil_alvo):
    MAX_POSTS = 5
    MAX_COMENTARIOS = 15

    dados_finais = {
        "username": perfil_alvo,
        "scraped_at": datetime.now().isoformat(),
        "posts": []
    }

    try:
        url_perfil = f"https://www.instagram.com/{perfil_alvo}/"
        print(f"🔄 Acessando Perfil: {url_perfil}")
        driver.get(url_perfil)
        time.sleep(5) 

        verificar_bloqueios(driver)

        posts_na_tela = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
        if len(posts_na_tela) == 0:
            print(f"⚠️ AVISO: Nenhum post encontrado em @{perfil_alvo}.")
            return None

        print("👆 Abrindo primeiro post...")
        driver.execute_script("arguments[0].click();", posts_na_tela[0])
        time.sleep(4)

        for i in range(MAX_POSTS):
            print(f"   📸 Extraindo post {i+1}/{MAX_POSTS}...")
            
            post_data = {
                "descricao": "",
                "likes": 0,
                "comentarios_coletados": [],
                "url": driver.current_url
            }

            # 1. PEGAR LIKES (Usa a nova função ultra assertiva)
            post_data["likes"] = caçar_likes(driver)

            # 2. PEGAR LEGENDA (Tag H1)
            try: post_data["descricao"] = driver.find_element(By.TAG_NAME, "h1").text
            except: pass

            # 3. PEGAR COMENTÁRIOS (Tag H3)
            print("      💬 Buscando comentários...")
            try:
                titulos_comentarios = driver.find_elements(By.TAG_NAME, "h3")
                coletados = 0
                for h3 in titulos_comentarios:
                    if coletados >= MAX_COMENTARIOS: break
                    try:
                        autor = h3.text
                        if not autor: continue

                        bloco_pai = h3.find_element(By.XPATH, "./../../..")
                        texto_bloco = bloco_pai.text.split('\n')
                        
                        if len(texto_bloco) >= 2:
                            post_data["comentarios_coletados"].append({
                                "autor": autor,
                                "texto": texto_bloco[1]
                            })
                            coletados += 1
                    except: continue
            except: pass

            print(f"      ✅ Sucesso! Likes: {post_data['likes']} | Comentários: {len(post_data['comentarios_coletados'])}/{MAX_COMENTARIOS}")
            dados_finais["posts"].append(post_data)

            # 4. Próximo Post
            if i < MAX_POSTS - 1:
                try:
                    ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
                    time.sleep(4)
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
            print("   ✅ Cookies injetados! (4s de pausa)")
            time.sleep(4)
        except: print("⚠️ AVISO: Sem cookies.")

        pasta_data = os.path.join(diretorio_src, "..", "data")
        caminho_csv = os.path.join(pasta_data, "famosos_instagram.csv")
        
        if os.path.exists(caminho_csv):
            with open(caminho_csv, "r", encoding="utf-8") as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    perfil = linha["nome_do_perfil"].strip()
                    if perfil:
                        print("\n" + "="*40)
                        print(f"📌 INICIANDO PERFIL: {perfil}")
                        print("="*40)
                        
                        resultado = processar_perfil(driver, perfil)
                        
                        if resultado:
                            caminho_json = os.path.join(pasta_data, f"instagram_{perfil}_data.json")
                            with open(caminho_json, 'w', encoding='utf-8') as f:
                                json.dump(resultado, f, ensure_ascii=False, indent=4)
                            print(f"✨ ARQUIVO SALVO: instagram_{perfil}_data.json")
                            time.sleep(random.randint(15, 25))
    finally:
        driver.quit()
        print("\n🏁 Fim da execução.")