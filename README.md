# 🕵️‍♂️ Coletor de Dados de Redes Sociais (Instagram & TikTok)

Projeto de extração de dados automatizada (*Web Scraping*) desenvolvido para fins de pesquisa acadêmica (Fiocruz/Data Science). O objetivo é coletar métricas públicas, metadados de posts e comentários para análise de engajamento e combate a fake news.

## 📂 Estrutura do Projeto

O projeto está organizado da seguinte forma:

```text
Projeto_Bolsa_Coleta/
├── data/                          # 📂 Entrada (CSVs) e Saída (JSONs)
│   ├── famosos_instagram.csv      # Lista de perfis para o Instagram
│   ├── famosos_tiktok.csv         # Lista de perfis para o TikTok
│   └── *.json                     # Arquivos coletados
├── src/                           # 📂 Códigos Fonte
│   ├── config/                    # ⚙️ Configurações e Autenticação
│   │   ├── instagram/             # Módulo Instagram
│   │   │   ├── logins_instagram/  # (Automático) Onde os cookies do Insta são salvos
│   │   │   └── setup_login_instagram.py
│   │   └── tiktok/                # Módulo TikTok
│   │   │   ├── logins_tiktok/     # (Automático) Onde os cookies do TikTok são salvos
│   │   │   └── setup_login_tiktok.py
│   ├── coleta_instagram.py        # Robô principal do Instagram (Selenium)
│   └── coleta_tiktok.py           # Robô principal do TikTok (Selenium)
├── requirements.txt               # Dependências do Python
└── README.md                      # Documentação
```

## 🛠️ Pré-requisitos

* **Python 3.8+** instalado.
* **Google Chrome** instalado.
* Uma conta no Instagram e no TikTok para autenticação (para evitar bloqueios).

## 🚀 Instalação

1.  Clone este repositório ou baixe os arquivos.
2.  No terminal, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração Inicial (Faça apenas na 1ª vez)

Ambas as redes exigem uma autenticação inicial que salva os "cookies" do navegador para as próximas execuções.

> **Importante:** Execute os comandos abaixo estando na raiz da pasta `src`.

### 1. Configurar Instagram 📸
1.  Abra o terminal na pasta `src`.
2.  Execute o script de configuração:
    ```bash
    python config/instagram/setup_login_instagram.py
    ```
3.  Uma janela do Chrome abrirá. Faça o login na sua conta do Instagram.
4.  Após a página do Feed carregar, volte ao terminal e aperte **ENTER**.
    * *Isso salvará seus cookies em `src/config/instagram/logins_instagram/`.*

### 2. Configurar TikTok 🎵
1.  Ainda na pasta `src`, execute o script de setup:
    ```bash
    python config/tiktok/setup_login_tiktok.py
    ```
2.  Uma janela do Chrome abrirá. **Faça o login manualmente** no TikTok (QR Code, Google, etc).
3.  Após logar, volte ao terminal e aperte **ENTER**.
    * *Isso salvará seus cookies em `src/config/tiktok/logins_tiktok/`.*

---

## ▶️ Como Usar

### 1. Preparar as Listas (Input)
Na pasta `data/`, edite os arquivos CSV. A primeira linha **deve** ser o cabeçalho `nome_do_perfil`.

Exemplo (`data/famosos_instagram.csv`):
```csv
nome_do_perfil
neymarjr
anitta
```

### 2. Rodar o Coletor do Instagram ou TikTok
No terminal, dentro da pasta `src`:
```bash
python coleta_instagram.py
```
ou
```bash
python coleta_tiktok.py
```
* **O que eles fazem:** Simulam um navegador real, injetam os cookies de login, clicam nos vídeos/fotos e extraem descrições, likes e comentários.
* **Segurança (Human-in-the-loop):** Se os sites pedirem Captcha ou Verificação de Segurança, o robô irá pausar, emitir um alerta sonoro e aguardar a intervenção humana para continuar.

### 3. Análise de Sentimento

No terminal, instale o Hugging Face:

```bash
python -m pip install huggingface_hub
```

Acesse https://huggingface.co/settings/tokens
clique em New token
Crie um token com permissão Read 
Copie o token gerado e cole na variável "api_key" dentro de analise_sentimento.py

Para rodar, no terminal, dentro da pasta `src`:
```bash
python analise_sentimento.py
```
---

## ⚠️ Notas Importantes & Troubleshooting

* **Página Não Encontrada:** Se o script parar sem erro aparente, a conta alvo pode ser privada ou não existir.
* **Atualização do Chrome:** O código usa o `webdriver_manager`, então o Chrome será atualizado automaticamente em segundo plano.
* **Privacidade:** Os dados coletados são públicos. Este projeto deve ser usado estritamente para fins acadêmicos e éticos.

## 📝 Autoria
Projeto desenvolvido por Lara e João Victor para bolsa de pesquisa em Data Science.