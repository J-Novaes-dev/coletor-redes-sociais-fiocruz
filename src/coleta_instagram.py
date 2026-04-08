import json
import time
import os
import pickle
import platform
import csv
import random
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def iniciar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=options)

def verificar_bloqueios(driver):
    try:
        url_atual = driver.current_url.lower()
        if "challenge" in url_atual or "login" in url_atual or "checkpoint" in url_atual:
            print("\n" + "█"*50)
            print("🚨 BLOQUEIO DETECTADO NO INSTAGRAM!")
            input("👉 Resolva no navegador e aperte [ENTER]...")
            return True
        if "Página não encontrada" in driver.title: return False
    except: pass
    return False

def converter_data_instagram(driver):
    try:
        elemento_tempo = driver.find_element(By.TAG_NAME, "time")
        data_iso = elemento_tempo.get_attribute("datetime")
        if data_iso: return datetime.strptime(data_iso[:10], "%Y-%m-%d")
    except: pass
    return datetime.now() 

def converter_numero(texto):
    if not texto: return 0
    texto = texto.lower().replace(',', '.').strip()
    if 'outra' in texto or 'pessoa' in texto:
        numeros = re.sub(r'[^0-9]', '', texto)
        return int(numeros) + 1 if numeros else 0
        
    multiplicador = 1
    if 'mil' in texto or 'k' in texto: multiplicador = 1000
    elif 'mi' in texto or 'm' in texto: multiplicador = 1000000

    numeros = re.sub(r'[^0-9.]', '', texto)
    try:
        if '.' in numeros and multiplicador > 1: return int(float(numeros) * multiplicador)
        return int(numeros.replace('.', ''))
    except: return 0

def extrair_likes(driver):
    try:
        try:
            el = driver.find_element(By.XPATH, "//a[contains(@href, '/liked_by/')]")
            return converter_numero(el.text)
        except: pass

        try:
            for el in driver.find_elements(By.XPATH, "//*[contains(text(), 'curtida') or contains(text(), 'like')]"):
                if any(char.isdigit() for char in el.text): return converter_numero(el.text)
        except: pass

        try:
            for el in driver.find_elements(By.XPATH, "//*[@aria-label]"):
                aria = el.get_attribute("aria-label").lower()
                if ('curtida' in aria or 'like' in aria) and any(char.isdigit() for char in aria):
                    return converter_numero(aria)
        except: pass
    except: pass
    return 0

def extrair_total_comentarios(driver):
    try:
        for el in driver.find_elements(By.XPATH, "//*[contains(text(), 'comentário') or contains(text(), 'comment')]"):
            if any(char.isdigit() for char in el.text): return converter_numero(el.text)
    except: pass
    try:
        for svg in driver.find_elements(By.XPATH, "//svg[@aria-label='Comentar' or @aria-label='Comment']"):
            texto = svg.find_element(By.XPATH, "./ancestor::div[1]").text.strip()
            if texto and any(char.isdigit() for char in texto): return converter_numero(texto)
    except: pass
    return 0

def extrair_comentarios(driver, max_comentarios=50):
    comentarios_coletados = []
    try:
        print(f"      💬 Carregando até {max_comentarios} comentários...")
        time.sleep(2)
        
        tentativas_scroll = 0
        while tentativas_scroll < 10:
            titulos_h3 = driver.find_elements(By.TAG_NAME, "h3")
            if len(titulos_h3) >= (max_comentarios + 3): break
                
            if titulos_h3:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", titulos_h3[-1])
                    time.sleep(1.0)
                except: pass
            
            try:
                xpath_botao = (
                    "//svg[contains(@class, 'x5n08af')]/ancestor::button | "
                    "//svg[@aria-label='Carregar mais comentários']/ancestor::button | "
                    "//svg[@aria-label='Load more comments']/ancestor::button | "
                    "//button[contains(., 'Carregar mais')]"
                )
                botoes_mais = driver.find_elements(By.XPATH, xpath_botao)
                if botoes_mais:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botoes_mais[-1])
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", botoes_mais[-1])
                    print("         ➕ Botão 'Carregar mais' clicado!")
                    time.sleep(2.0)
            except: pass
            tentativas_scroll += 1

        index_atual = 0
        falhas_consecutivas = 0
        
        while len(comentarios_coletados) < max_comentarios and falhas_consecutivas < 5:
            titulos_frescos = driver.find_elements(By.TAG_NAME, "h3")
            if index_atual >= len(titulos_frescos): break 

            h3 = titulos_frescos[index_atual]
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", h3)
                time.sleep(0.3)
                autor = h3.text.strip()
                if autor:
                    texto_bloco = h3.find_element(By.XPATH, "./../../..").text.split('\n')
                    if len(texto_bloco) >= 2:
                        comentarios_coletados.append({"autor": autor, "texto": texto_bloco[1]})
                        falhas_consecutivas = 0 
                index_atual += 1 
            except:
                falhas_consecutivas += 1
                time.sleep(0.5)

    except Exception as e: print(f"      ⚠️ Erro na extração de comentários: {e}")
    return comentarios_coletados

def processar_perfil(driver, perfil_alvo):
    dados_finais = {"username": perfil_alvo, "scraped_at": datetime.now().isoformat(), "posts": []}

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

        dias_limite = 60
        data_limite = datetime.now() - timedelta(days=dias_limite)
        print(f"   📅 Coletando APÓS: {data_limite.strftime('%d/%m/%Y')}")

        contador_post = 0
        while True:
            contador_post += 1
            print(f"   📸 Extraindo post {contador_post}...")
            
            post_data = {"descricao": "", "data_publicacao": "", "stats": {"likes": 0, "comments": 0, "shares": 0}, "comentarios_coletados": [], "url": driver.current_url}

            data_do_post = converter_data_instagram(driver)
            post_data["data_publicacao"] = data_do_post.strftime('%d/%m/%Y')
            print(f"      🕒 Data: {post_data['data_publicacao']}")

            if data_do_post < data_limite and contador_post > 3:
                print(f"      🛑 Limite de {dias_limite} dias alcançado!")
                break

            post_data["stats"]["likes"] = extrair_likes(driver)
            post_data["stats"]["comments"] = extrair_total_comentarios(driver)
            try: post_data["descricao"] = driver.find_element(By.TAG_NAME, "h1").text
            except: pass

            post_data["comentarios_coletados"] = extrair_comentarios(driver, max_comentarios=50)

            if post_data["stats"]["comments"] < len(post_data["comentarios_coletados"]):
                post_data["stats"]["comments"] = len(post_data["comentarios_coletados"])

            print(f"      ✅ Likes: {post_data['stats']['likes']} | Comentários (Stats): {post_data['stats']['comments']} | Extraídos: {len(post_data['comentarios_coletados'])}")
            dados_finais["posts"].append(post_data)

            try:
                ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
                time.sleep(3)
            except: break 
        
        return dados_finais

    except Exception as e:
        print(f"❌ Erro no perfil {perfil_alvo}: {e}")
        return None

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
        except: print("⚠️ Sem cookies.")

        # --- NOVA ORGANIZAÇÃO DE PASTAS ---
        pasta_data = os.path.join(diretorio_src, "..", "data")
        pasta_json_instagram = os.path.join(pasta_data, "dados_instagram")
        os.makedirs(pasta_json_instagram, exist_ok=True) # Cria a pasta dados_instagram automaticamente!

        caminho_csv = os.path.join(pasta_data, "famosos_instagram.csv")
        
        if os.path.exists(caminho_csv):
            with open(caminho_csv, "r", encoding="utf-8") as arquivo:
                for linha in csv.DictReader(arquivo):
                    perfil = linha["nome_do_perfil"].strip()
                    if perfil:
                        print(f"\n📌 PROCESSANDO INSTAGRAM: {perfil}")
                        resultado = processar_perfil(driver, perfil)
                        if resultado:
                            # Salva o arquivo dentro da nova subpasta
                            caminho_json = os.path.join(pasta_json_instagram, f"instagram_{perfil}_data.json")
                            with open(caminho_json, 'w', encoding='utf-8') as f:
                                json.dump(resultado, f, ensure_ascii=False, indent=4)
                            print(f"✨ JSON Salvo em: data/dados_instagram/instagram_{perfil}_data.json")
                            time.sleep(random.randint(10, 20))
    finally:
        driver.quit()