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

def converter_data_tiktok(texto):
    """Busca agressivamente padrões de data no texto (ex: 2d, 3w, 02-25, 2023-10-25)"""
    if not texto: return datetime.now()
    texto = texto.lower().strip()
    hoje = datetime.now()
    
    try:
        match_ano = re.search(r'(\d{4})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})', texto)
        if match_ano:
            return datetime(int(match_ano.group(1)), int(match_ano.group(2)), int(match_ano.group(3)))

        match_mes = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})', texto)
        if match_mes:
            n1, n2 = int(match_mes.group(1)), int(match_mes.group(2))
            mes, dia = (n1, n2) if n1 <= 12 else (n2, n1)
            return datetime(hoje.year, mes, dia)

        match_relativo = re.search(r'(\d+)\s*(d|w|dia|sem)', texto)
        if match_relativo:
            qtd = int(match_relativo.group(1))
            unidade = match_relativo.group(2)
            if 'w' in unidade or 'sem' in unidade: return hoje - timedelta(weeks=qtd)
            else: return hoje - timedelta(days=qtd)
        
        if re.search(r'\d+\s*(h|m|s)', texto) or 'agora' in texto: return hoje
            
    except Exception as e:
        print(f"      ⚠️ Erro ao converter data '{texto}': {e}")
    return hoje

def converter_numero(texto):
    if not texto: return 0
    texto = texto.upper().replace(',', '.').replace('VISUALIZAÇÕES', '').strip()
    multiplicador = 1
    if 'K' in texto: multiplicador = 1000
    elif 'M' in texto: multiplicador = 1000000
    elif 'B' in texto: multiplicador = 1000000000
    try:
        return int(float(texto.replace('K','').replace('M','').replace('B','')) * multiplicador)
    except:
        return 0

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
        if "verify" in url_atual or "challenge" in url_atual:
            print("\n" + "█"*50)
            print("🚨 DETECTADO PELA URL: O TikTok pediu verificação!")
            input("👉 Resolva o Captcha e aperte [ENTER] para continuar...")
            return True
        try:
            texto_visivel = driver.find_element(By.TAG_NAME, "body").text.lower()
            if any(ind in texto_visivel for ind in ["verify to continue", "arraste o controle", "verificação"]):
                print("\n" + "█"*50)
                print("🚨 DETECTADO PELO TEXTO: O TikTok pediu verificação!")
                input("👉 Resolva o Captcha e aperte [ENTER] para continuar...")
                return True
        except: pass
    except: pass
    return False

def extrair_comentarios(driver, max_comentarios=50):
    comentarios_coletados = []
    xpath_busca = "//div[contains(@class, 'Comment') and contains(@class, 'Item')]"
    
    try:
        print(f"      💬 Carregando até {max_comentarios} comentários...")
        time.sleep(2) 
        
        tentativas_scroll = 0
        while tentativas_scroll < 10:
            elementos = driver.find_elements(By.XPATH, xpath_busca)
            if not elementos:
                xpath_busca = "//div[contains(@class, 'Comment') and contains(@class, 'Content')]"
                elementos = driver.find_elements(By.XPATH, xpath_busca)
                
            if len(elementos) >= (max_comentarios + 5): break
                
            if elementos:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elementos[-1])
                    time.sleep(2.0)
                except: pass
            tentativas_scroll += 1

        index_atual = 0
        falhas_consecutivas = 0
        
        while len(comentarios_coletados) < max_comentarios and falhas_consecutivas < 5:
            elementos_frescos = driver.find_elements(By.XPATH, xpath_busca)
            if index_atual >= len(elementos_frescos): break 

            el = elementos_frescos[index_atual]
            
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.3)
                texto_bloco = el.text.strip()
                if not texto_bloco:
                    index_atual += 1
                    continue
                    
                texto_comentario = ""
                autor_comentario = "Desconhecido"
                
                try: texto_comentario = el.find_element(By.TAG_NAME, "p").text.strip()
                except: pass

                linhas = [L.strip() for L in texto_bloco.split('\n') if L.strip()]
                if linhas:
                    autor_comentario = linhas[0].split('·')[0].strip()

                if not texto_comentario and len(linhas) >= 2:
                    texto_comentario = linhas[1]

                if texto_comentario:
                    comentarios_coletados.append({"autor": autor_comentario, "texto": texto_comentario})
                    falhas_consecutivas = 0 
                index_atual += 1 

            except:
                falhas_consecutivas += 1
                time.sleep(0.5)

    except Exception as e: print(f"      ⚠️ Erro geral na extração: {e}")
    return comentarios_coletados

def processar_perfil(driver, perfil_alvo):
    dados_finais = {"username": perfil_alvo, "scraped_at": datetime.now().isoformat(), "videos": []}

    try:
        url_perfil = f"https://www.tiktok.com/@{perfil_alvo}"
        print(f"🔄 Acessando Perfil: {url_perfil}")
        driver.get(url_perfil)
        time.sleep(4) 
        verificar_bloqueios(driver)

        videos_na_tela = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="user-post-item"]')
        if len(videos_na_tela) == 0:
            print(f"⚠️ AVISO: Não encontrei vídeos em @{perfil_alvo}.")
            input("👉 Se a página não carregou, dê F5. Aperte [ENTER] para tentar de novo...")
            time.sleep(3)
            videos_na_tela = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="user-post-item"]')
            if len(videos_na_tela) == 0: return None

        print("👆 Abrindo primeiro vídeo...")
        videos_na_tela[0].click()
        time.sleep(3)

        dias_limite = 60
        data_limite = datetime.now() - timedelta(days=dias_limite)
        print(f"   📅 Coletando APÓS: {data_limite.strftime('%d/%m/%Y')}")

        contador_video = 0
        while True:
            contador_video += 1
            print(f"   🎥 Extraindo vídeo {contador_video}...")
            video_data = {"descricao": "", "data_publicacao": "", "stats": {"likes": 0, "comments": 0, "shares": 0}, "comentarios_coletados": [], "url": driver.current_url}

            try:
                try: driver.find_element(By.CSS_SELECTOR, '[data-e2e="modal-close-inner-button"]').click()
                except: pass

                try:
                    elemento_nome = driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-username"]')
                    texto_bruto = driver.execute_script("return arguments[0].parentNode.innerText;", elemento_nome)
                    data_do_video = converter_data_tiktok(texto_bruto)
                    video_data["data_publicacao"] = data_do_video.strftime('%d/%m/%Y')
                except:
                    data_do_video = datetime.now()
                    video_data["data_publicacao"] = "Desconhecida"
                
                print(f"      🕒 Data: {video_data['data_publicacao']}")
                
                if data_do_video < data_limite and contador_video > 3:
                    print(f"      🛑 Limite de {dias_limite} dias alcançado!")
                    break 

                try: video_data["descricao"] = driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-video-desc"]').text
                except: pass
                try: video_data["stats"]["likes"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-like-count"]').text)
                except: pass
                try: video_data["stats"]["comments"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-comment-count"]').text)
                except: pass
                try: video_data["stats"]["shares"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="share-count"]').text)
                except: pass

                if video_data["stats"]["comments"] > 0:
                    video_data["comentarios_coletados"] = extrair_comentarios(driver, max_comentarios=50)

                print(f"      ✅ Likes: {video_data['stats']['likes']} | Comentários: {len(video_data['comentarios_coletados'])}")
                dados_finais["videos"].append(video_data)
                
            except Exception as e: print(f"      ⚠️ Erro no vídeo: {e}")

            try: driver.find_element(By.CSS_SELECTOR, '[data-e2e="arrow-right"]').click()
            except: ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
            time.sleep(2.5)
        
        return dados_finais

    except Exception as e:
        print(f"❌ Erro geral no perfil {perfil_alvo}: {e}")
        return None

if __name__ == "__main__":
    driver = iniciar_driver()
    try:
        print("🍪 Injetando Cookies do TikTok...")
        driver.get("https://www.tiktok.com/")
        diretorio_src = os.path.dirname(os.path.abspath(__file__))
        caminho_cookie = os.path.join(diretorio_src, "config", "tiktok", "logins_tiktok", "tiktok_cookies.pkl")
        
        try:
            cookies = pickle.load(open(caminho_cookie, "rb"))
            for cookie in cookies: driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(3)
        except: print("⚠️ Sem cookies.")

        # --- NOVA ORGANIZAÇÃO DE PASTAS ---
        pasta_data = os.path.join(diretorio_src, "..", "data")
        pasta_json_tiktok = os.path.join(pasta_data, "dados_tiktok")
        os.makedirs(pasta_json_tiktok, exist_ok=True) # Cria a pasta dados_tiktok automaticamente!

        caminho_csv = os.path.join(pasta_data, "famosos_tiktok.csv")
        
        if os.path.exists(caminho_csv):
            with open(caminho_csv, "r", encoding="utf-8") as arquivo:
                for linha in csv.DictReader(arquivo):
                    perfil = linha["nome_do_perfil"].strip()
                    if perfil:
                        print(f"\n📌 PROCESSANDO TIKTOK: {perfil}")
                        resultado = processar_perfil(driver, perfil)
                        if resultado:
                            # Salva o arquivo dentro da nova subpasta
                            caminho_json = os.path.join(pasta_json_tiktok, f"tiktok_{perfil}_data.json")
                            with open(caminho_json, 'w', encoding='utf-8') as f:
                                json.dump(resultado, f, ensure_ascii=False, indent=4)
                            print(f"✨ JSON Salvo em: data/dados_tiktok/tiktok_{perfil}_data.json")
                            time.sleep(random.randint(5, 10))
    finally:
        driver.quit()