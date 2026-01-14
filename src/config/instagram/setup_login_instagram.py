import instaloader
import os

usuario = "carolbrito2110"

print(f"📸 Iniciando login INSTAGRAM para: {usuario}")
print("Digite sua senha quando solicitado...")

L = instaloader.Instaloader()

try:
    L.interactive_login(usuario)
    
    # --- NOVA LÓGICA DE CAMINHOS ---
    # Pega a pasta onde este script está (src/config/instagram)
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Define a subpasta de armazenamento
    pasta_destinos = os.path.join(pasta_atual, "logins_instagram")
    
    # Cria a pasta se não existir
    if not os.path.exists(pasta_destinos):
        os.makedirs(pasta_destinos)
        
    # Define o caminho final do arquivo
    caminho_arquivo = os.path.join(pasta_destinos, f"session-{usuario}")
    
    L.save_session_to_file(filename=caminho_arquivo)
    
    print(f"\n✅ SUCESSO! Sessão salva em:\n{caminho_arquivo}")

except Exception as e:
    print(f"\n❌ Erro: {e}")