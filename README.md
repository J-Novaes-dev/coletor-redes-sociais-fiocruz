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
│   │   │   ├── logins_instagram/  # (Automático) Onde as sessões são salvas
│   │   │   └── setup_login_instagram.py
│   │   └── tiktok/                # Módulo TikTok
│   │   │   ├── logins_tiktok/     # (Automático) Onde os cookies são salvos
│   │   │   └── setup_login_tiktok.py
│   ├── coleta_instagram.py        # Robô principal do Instagram
│   └── coleta_tiktok.py           # Robô principal do TikTok
├── requirements.txt               # Dependências do Python
└── README.md                      # Documentação
```

## 🛠️ Pré-requisitos

* **Python 3.8+** instalado.
* **Google Chrome** instalado (para o Selenium do TikTok).
* Uma conta no Instagram (para autenticação).
* Uma conta no TikTok (para autenticação via cookies).

## 🚀 Instalação

1.  Clone este repositório ou baixe os arquivos.
2.  No terminal, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração Inicial (Faça apenas na 1ª vez)

Antes de rodar os robôs, é necessário gerar os arquivos de autenticação para evitar bloqueios.

> **Importante:** Execute os comandos abaixo estando na raiz da pasta `src`.

### 1. Configurar Instagram 📸
1.  Abra o terminal na pasta `src`.
2.  Execute o script de configuração:
    ```bash
    python config/instagram/setup_login_instagram.py
    ```
3.  Digite sua senha quando solicitado.
    * *O arquivo de sessão será salvo automaticamente em `src/config/instagram/logins_instagram/`.*

### 2. Configurar TikTok 🎵
1.  Ainda na pasta `src`, execute o script de setup:
    ```bash
    python config/tiktok/setup_login_tiktok.py
    ```
2.  Uma janela do Chrome abrirá. **Faça o login manualmente** no TikTok (QR Code, Google, etc).
3.  Após logar e ver a página inicial, volte ao terminal e aperte **ENTER**.
    * *Isso salvará seus cookies em `src/config/tiktok/logins_tiktok/`.*

---

## ▶️ Como Usar

### 1. Preparar as Listas (Input)
Na pasta `data/`, crie ou edite os arquivos CSV. A primeira linha **deve** ser o cabeçalho `nome_do_perfil`.

Exemplo (`data/famosos_instagram.csv`):
```csv
nome_do_perfil
neymarjr
anitta
cazetv
```

### 2. Rodar o Coletor do Instagram
No terminal, dentro da pasta `src`:
```bash
python coleta_instagram.py
```
* **O que ele faz:** Lê o CSV, coleta perfil, últimos posts, métricas e comentários limitados.
* **Segurança:** Possui "freio de emergência" se detectar bloqueio 401/429.

### 3. Rodar o Coletor do TikTok
No terminal, dentro da pasta `src`:
```bash
python coleta_tiktok.py
```
* **O que ele faz:** Simula um navegador real, injeta cookies de login, clica nos vídeos e extrai likes, visualizações e textos dos comentários.

---

## ⚠️ Notas Importantes & Troubleshooting

* **Soft Ban (Instagram):** Se o script parar com erro `401 Unauthorized` ou `429 Too Many Requests`, o Instagram bloqueou temporariamente seu IP ou conta. **Pare por 2 a 24 horas**.
* **Erro de Seletor (TikTok):** O TikTok muda o código do site frequentemente. Se os comentários vierem zerados, pode ser necessário atualizar os seletores CSS/XPath no código.
* **Privacidade:** Os dados coletados são públicos. Este projeto deve ser usado estritamente para fins acadêmicos e éticos.

## 📝 Autoria
Projeto desenvolvido por Lara e João Victor para bolsa de pesquisa em Data Science.