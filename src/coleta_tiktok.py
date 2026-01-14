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
from webdriver_manager.chrome import ChromeDriverManager

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
    sistema = platform.system()
    options = Options()
    if sistema == "Linux":
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--no-sandbox")
    
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=options)

# --- DETECTOR DE BLOQUEIO REFINADO ---
def verificar_bloqueios(driver):
    """
    Verifica se há Captcha ou se a página quebrou.
    Retorna True se houve intervenção manual.
    """
    try:
        # 1. Verifica URL suspeita
        url_atual = driver.current_url.lower()
        if "verify" in url_atual or "challenge" in url_atual:
            print("\n" + "█"*50)
            print("🚨 DETECTADO PELA URL: O TikTok pediu verificação!")
            print("👉 AÇÃO: Resolva o Captcha no navegador.")
            input("👉 DEPOIS: Aperte [ENTER] aqui para continuar...")
            time.sleep(3)
            return True

        # 2. Verifica Texto VISÍVEL (não o código fonte oculto)
        try:
            # Pega apenas o texto que o usuário vê
            texto_visivel = driver.find_element(By.TAG_NAME, "body").text.lower()
            indicadores = ["verify to continue", "arraste o controle", "rotate the image", "verificação de segurança"]
            
            if any(ind in texto_visivel for ind in indicadores):
                print("\n" + "█"*50)
                print("🚨 DETECTADO PELO TEXTO: O TikTok pediu verificação!")
                print("👉 AÇÃO: Resolva o Captcha no navegador.")
                input("👉 DEPOIS: Aperte [ENTER] aqui para continuar...")
                time.sleep(3)
                return True
        except: pass

    except Exception as e:
        print(f"⚠️ Erro leve na verificação: {e}")
    
    return False

def extrair_comentarios(driver, max_comentarios=10):
    comentarios_coletados = []
    
    try:
        print(f"      💬 Buscando comentários...")
        
        # Busca os elementos
        xpath_busca = "//div[contains(@class, 'Comment') and contains(@class, 'Item')]"
        time.sleep(2) 
        elementos = driver.find_elements(By.XPATH, xpath_busca)
        
        if len(elementos) == 0:
            xpath_busca = "//div[contains(@class, 'Comment') and contains(@class, 'Content')]"
            elementos = driver.find_elements(By.XPATH, xpath_busca)

        if len(elementos) == 0:
            return []

        for i, el in enumerate(elementos[:max_comentarios]):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                
                # Pega TODO o texto visível dentro do quadrado do comentário
                texto_completo = el.text
                
                # Se estiver vazio, tenta forçar via JS (backup)
                if not texto_completo:
                    texto_completo = driver.execute_script("return arguments[0].innerText;", el)

                # Separa por linhas e remove vazias
                linhas = texto_completo.split('\n')
                linhas = [L.strip() for L in linhas if L.strip()] 

                autor = "Desconhecido"
                texto = ""

                if len(linhas) >= 2:
                    # Lógica: Linha 1 = Autor | Última Linha = Texto
                    autor = linhas[0]
                    texto = linhas[-1]
                    
                    # Ajuste para casos onde a última linha é data (ex: "2h")
                    if len(texto) < 3 and len(linhas) > 2: 
                        texto = linhas[-2]

                elif len(linhas) == 1:
                    # Se só tem uma linha, tentamos ver se é diferente do <p> interno
                    try:
                        p_texto = el.find_element(By.TAG_NAME, 'p').text
                        texto = p_texto
                        if linhas[0] != p_texto:
                            autor = linhas[0]
                    except:
                        texto = linhas[0]

                # Limpeza de sufixos comuns (ex: "João · Criador")
                if "·" in autor:
                    autor = autor.split('·')[0].strip()

                if texto: 
                    comentarios_coletados.append({
                        "autor": autor,
                        "texto": texto
                    })
            except Exception as e:
                continue

    except Exception as e:
        print(f"      ⚠️ Erro: {e}")

    return comentarios_coletados

def processar_perfil(driver, perfil_alvo):
    dados_finais = {
        "username": perfil_alvo,
        "scraped_at": datetime.now().isoformat(),
        "videos": []
    }

    try:
        url_perfil = f"https://www.tiktok.com/@{perfil_alvo}"
        print(f"🔄 Acessando Perfil: {url_perfil}")
        driver.get(url_perfil)
        time.sleep(4) 

        # 1. Verifica Captcha logo na entrada
        verificar_bloqueios(driver)

        # 2. Verifica Vídeos
        videos_na_tela = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="user-post-item"]')
        
        # --- PAUSA DE SEGURANÇA (Se não achar vídeos) ---
        if len(videos_na_tela) == 0:
            print(f"\n⚠️ AVISO: Não encontrei vídeos em @{perfil_alvo}.")
            print("   Motivos: Captcha não detectado, internet lenta ou perfil vazio.")
            
            # Aqui está a "Segunda Chance" que você concordou em manter
            print("🛑 PAUSANDO PARA AJUDA HUMANA.")
            print("👉 AÇÃO: Se a página não carregou, dê F5. Se tem Captcha, resolva.")
            input("👉 DEPOIS: Aperte [ENTER] para o robô tentar buscar os vídeos de novo...")
            
            time.sleep(3)
            # Tenta buscar de novo após sua ajuda
            videos_na_tela = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="user-post-item"]')
            
            if len(videos_na_tela) == 0:
                print(f"❌ Ainda sem vídeos. Pulando @{perfil_alvo}...")
                return None
        # -----------------------------------------------

        print("👆 Abrindo primeiro vídeo...")
        try:
            videos_na_tela[0].click()
            time.sleep(3)
        except Exception as e:
            print(f"❌ Erro ao clicar: {e}")
            return None

        quantidade_videos = 5
        for i in range(quantidade_videos):
            print(f"   🎥 Extraindo vídeo {i+1}/{quantidade_videos}...")
            video_data = {"descricao": "", "stats": {"likes": 0, "comments": 0, "shares": 0}, "comentarios_coletados": [], "url": driver.current_url}

            try:
                try: driver.find_element(By.CSS_SELECTOR, '[data-e2e="modal-close-inner-button"]').click()
                except: pass

                try: video_data["descricao"] = driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-video-desc"]').text
                except: pass
                try: video_data["stats"]["likes"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-like-count"]').text)
                except: pass
                try: video_data["stats"]["comments"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="browse-comment-count"]').text)
                except: pass
                try: video_data["stats"]["shares"] = converter_numero(driver.find_element(By.CSS_SELECTOR, '[data-e2e="share-count"]').text)
                except: pass

                if video_data["stats"]["comments"] > 0:
                    video_data["comentarios_coletados"] = extrair_comentarios(driver, max_comentarios=10)

                print(f"      ✅ Likes: {video_data['stats']['likes']} | Comentários: {len(video_data['comentarios_coletados'])}")
                dados_finais["videos"].append(video_data)
            except Exception as e:
                print(f"      ⚠️ Erro no vídeo: {e}")

            if i < quantidade_videos - 1:
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
        print("🍪 Injetando Cookies...")
        driver.get("https://www.tiktok.com/")
        diretorio_src = os.path.dirname(os.path.abspath(__file__))
        caminho_cookie = os.path.join(diretorio_src, "config", "tiktok", "logins_tiktok", "tiktok_cookies.pkl")
        
        try:
            cookies = pickle.load(open(caminho_cookie, "rb"))
            for cookie in cookies: driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(3)
        except: print("⚠️ Visitante (Sem cookies).")

        pasta_data = os.path.join(diretorio_src, "..", "data")
        caminho_csv = os.path.join(pasta_data, "famosos_tiktok.csv")
        
        if os.path.exists(caminho_csv):
            with open(caminho_csv, "r", encoding="utf-8") as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    perfil = linha["nome_do_perfil"].strip()
                    if perfil:
                        print(f"\n📌 PROCESSANDO: {perfil}")
                        resultado = processar_perfil(driver, perfil)
                        if resultado:
                            caminho_json = os.path.join(pasta_data, f"tiktok_{perfil}_data.json")
                            with open(caminho_json, 'w', encoding='utf-8') as f:
                                json.dump(resultado, f, ensure_ascii=False, indent=4)
                            print("✨ JSON Salvo!")
                            time.sleep(random.randint(5, 10))
    finally:
        driver.quit()
        print("\n🏁 Fim.")