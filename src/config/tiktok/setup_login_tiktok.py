import pickle
import os
import platform
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def salvar_cookies():
    sistema = platform.system()
    options = Options()
    if sistema == "Linux":
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--no-sandbox")
    
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("🎵 Abrindo TikTok para Login...")
        driver.get("https://www.tiktok.com/login")
        
        print("\n" + "█"*60)
        print("🚨 FAÇA O LOGIN MANUALMENTE AGORA 🚨")
        input("👉 DEPOIS QUE TIVER LOGADO, VOLTE AQUI E APERTE [ENTER]...")
        print("█"*60 + "\n")
        
        # --- NOVA LÓGICA DE CAMINHOS ---
        pasta_atual = os.path.dirname(os.path.abspath(__file__))
        pasta_destinos = os.path.join(pasta_atual, "logins_tiktok")
        
        if not os.path.exists(pasta_destinos):
            os.makedirs(pasta_destinos)
            
        caminho_cookie = os.path.join(pasta_destinos, "tiktok_cookies.pkl")
        
        pickle.dump(driver.get_cookies(), open(caminho_cookie, "wb"))
        
        print(f"✅ SUCESSO! Cookies salvos em:\n{caminho_cookie}")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    salvar_cookies()