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

# --- EXTRATOR DE DATA (BEM MAIS SIMPLES QUE O TIKTOK) ---
def extrair_data_instagram(driver):
    """Pega a data exata escondida na tag <time> do Instagram"""
    try:
        elemento_tempo = driver.find_element(By.TAG_NAME, "time")
        data_iso = elemento_tempo.get_attribute("datetime")
        # O formato ISO é: "2023-10-25T14:30:00.000Z". Vamos pegar só a parte "YYYY-MM-DD"
        if data_iso:
            return datetime.strptime(data_iso[:10], "%Y-%m-%d")
    except:
        pass
    return datetime.now() # Fallback se der erro

# --- O "CAÇADOR DE LIKES" DEFINITIVO 🎯 ---
def extrair_numero_likes(texto):
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
        if '.' in numeros and multiplicador > 1:
            return int(float(numeros) * multiplicador)
        return int(numeros.replace('.', ''))
    except: return 0

def caçar_likes(driver):
    try:
        try:
            elemento_link = driver.find_element(By.XPATH, "//a[contains(@href, '/liked_by/')]")
            return extrair_numero_likes(elemento_link.text)
        except: pass

        try:
            elementos = driver.find_elements(By.XPATH, "//*[contains(text(), 'curtida') or contains(text(), 'like')]")
            for el in elementos:
                if any(char.isdigit() for char in el.text):
                    return extrair_numero_likes(el.text)
        except: pass

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

# --- EXTRATOR DE COMENTÁRIOS ANTI-STALE ---
def extrair_comentarios_instagram(driver, max_comentarios=50):
    comentarios_coletados = []
    
    try:
        print(f"      💬 Carregando até {max_comentarios} comentários...")
        time.sleep(2)
        
        # 1. AQUECIMENTO DA TELA E CAÇA AO BOTÃO "+"
        tentativas_scroll = 0
        while tentativas_scroll < 10:
            titulos_h3 = driver.find_elements(By.TAG_NAME, "h3")
            
            if len(titulos_h3) >= (max_comentarios + 3):
                break
                
            # Rola até o último comentário da lista atual
            if titulos_h3:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", titulos_h3[-1])
                    time.sleep(1.0)
                except: pass
            
            # --- O PULO DO GATO: CLICAR NO BOTÃO DE CARREGAR MAIS ---
            try:
                # Armadilha dupla: Busca pela classe que você achou OU pelos textos ocultos de acessibilidade
                xpath_botao = (
                    "//svg[contains(@class, 'x5n08af')]/ancestor::button | "
                    "//svg[@aria-label='Carregar mais comentários']/ancestor::button | "
                    "//svg[@aria-label='Load more comments']/ancestor::button | "
                    "//button[contains(., 'Carregar mais')]"
                )
                
                botoes_mais = driver.find_elements(By.XPATH, xpath_botao)
                
                if botoes_mais:
                    # O botão "Carregar mais" fica lá embaixo, então pegamos o último [-1] encontrado
                    botao_alvo = botoes_mais[-1]
                    
                    # Força a rolagem até ele antes de clicar
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_alvo)
                    time.sleep(0.5)
                    
                    # Clica via JavaScript (Ignora pop-ups invisíveis que possam estar na frente)
                    driver.execute_script("arguments[0].click();", botao_alvo)
                    print("         ➕ Botão 'Carregar mais' clicado!")
                    time.sleep(2.0) # Tempo vital pro servidor do Instagram devolver a nova lista
            except Exception as e:
                pass # Se não achar o botão, ignora e tenta fazer o scroll normal na próxima volta
                
            tentativas_scroll += 1

        # 2. A COLETA COM RESISTÊNCIA
        index_atual = 0
        falhas_consecutivas = 0
        
        while len(comentarios_coletados) < max_comentarios and falhas_consecutivas < 5:
            titulos_frescos = driver.find_elements(By.TAG_NAME, "h3")
            
            if index_atual >= len(titulos_frescos):
                break 

            h3 = titulos_frescos[index_atual]
            
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", h3)
                time.sleep(0.3)
                
                autor = h3.text.strip()
                if autor:
                    bloco_pai = h3.find_element(By.XPATH, "./../../..")
                    texto_bloco = bloco_pai.text.split('\n')
                    
                    if len(texto_bloco) >= 2:
                        comentarios_coletados.append({
                            "autor": autor,
                            "texto": texto_bloco[1]
                        })
                        falhas_consecutivas = 0 
                
                index_atual += 1 

            except Exception as e:
                # Se der StaleElement, respira e tenta de novo a mesma posição na lista fresca
                falhas_consecutivas += 1
                time.sleep(0.5)

    except Exception as e:
        print(f"      ⚠️ Erro geral na extração de comentários: {e}")

    return comentarios_coletados


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
        time.sleep(5) 

        verificar_bloqueios(driver)

        posts_na_tela = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
        if len(posts_na_tela) == 0:
            print(f"⚠️ AVISO: Nenhum post encontrado em @{perfil_alvo}.")
            return None

        print("👆 Abrindo primeiro post...")
        driver.execute_script("arguments[0].click();", posts_na_tela[0])
        time.sleep(4)

        # Define o limite de tempo (Ex: 60 dias atrás)
        dias_limite = 60
        data_limite = datetime.now() - timedelta(days=dias_limite)
        print(f"   📅 O robô vai coletar tudo publicado APÓS: {data_limite.strftime('%d/%m/%Y')}")

        contador_post = 0

        while True:
            contador_post += 1
            print(f"   📸 Extraindo post {contador_post}...")
            
            post_data = {
                "descricao": "",
                "data_publicacao": "",
                "likes": 0,
                "comentarios_coletados": [],
                "url": driver.current_url
            }

            # --- EXTRATOR DE DATA DA TELA ---
            data_do_post = extrair_data_instagram(driver)
            post_data["data_publicacao"] = data_do_post.strftime('%d/%m/%Y')
            print(f"      🕒 Data: {post_data['data_publicacao']}")

            # --- TRAVA DE TEMPO ---
            # Ignora os 3 primeiros que podem ser fixados
            if data_do_post < data_limite and contador_post > 3:
                print(f"      🛑 Limite de {dias_limite} dias alcançado! Parando a coleta neste perfil.")
                break

            # 1. PEGAR LIKES
            post_data["likes"] = caçar_likes(driver)

            # 2. PEGAR LEGENDA
            try: post_data["descricao"] = driver.find_element(By.TAG_NAME, "h1").text
            except: pass

            # 3. PEGAR COMENTÁRIOS (com a nossa função blindada de 50)
            post_data["comentarios_coletados"] = extrair_comentarios_instagram(driver, max_comentarios=50)

            print(f"      ✅ Likes: {post_data['likes']} | Comentários: {len(post_data['comentarios_coletados'])}")
            dados_finais["posts"].append(post_data)

            # 4. Próximo Post
            try:
                ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
                time.sleep(3)
            except: 
                break # Se não conseguir passar pro lado, a lista acabou
        
        return dados_finais

    except Exception as e:
        print(f"❌ Erro geral no perfil {perfil_alvo}: {e}")
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
                            time.sleep(random.randint(10, 20)) # Pausa pro Insta não surtar
    finally:
        driver.quit()
        print("\n🏁 Fim da execução.")