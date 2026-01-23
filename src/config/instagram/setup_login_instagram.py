import pickle
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def salvar_cookies_instagram():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("📸 Abrindo Instagram para Login...")
        driver.get("https://www.instagram.com/accounts/login/")
        
        print("\n" + "█"*60)
        print("🚨 FAÇA O LOGIN MANUALMENTE NO NAVEGADOR 🚨")
        print("1. Digite seu usuário e senha.")
        print("2. Se pedir código 2FA, digite.")
        print("3. Se aparecer 'Salvar Informações', clique em 'Agora não'.")
        input("👉 DEPOIS QUE ESTIVER NA TELA INICIAL (FEED), APERTE [ENTER] AQUI...")
        print("█"*60 + "\n")
        
        # --- Lógica de Caminhos ---
        pasta_atual = os.path.dirname(os.path.abspath(__file__))
        pasta_destinos = os.path.join(pasta_atual, "logins_instagram")
        
        if not os.path.exists(pasta_destinos):
            os.makedirs(pasta_destinos)
            
        caminho_cookie = os.path.join(pasta_destinos, "instagram_cookies.pkl")
        
        # Salva os cookies do navegador
        pickle.dump(driver.get_cookies(), open(caminho_cookie, "wb"))
        
        print(f"✅ SUCESSO! Cookies do Instagram salvos em:\n{caminho_cookie}")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    salvar_cookies_instagram()