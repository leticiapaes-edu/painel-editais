# Painel de Editais - AEDB

Aplicação em **Streamlit** para visualização de editais de fomento.  
Os dados são carregados automaticamente de uma planilha no **Google Sheets**.

---

## 🚀 Como funciona

- Editais são mantidos em uma planilha Google Sheets pública.  
- O painel exibe os editais com filtros por agência e prazo.  
- Há uma nuvem de palavras dinâmica com base nos **temas**.  
- Feedbacks enviados na lateral são registrados em outra planilha (`feedback_editais`).  

---

## 📂 Estrutura do projeto

- `app.py` → código principal do painel  
- `requirements.txt` → dependências do Python  
- `README.md` → este guia  
- `1.png` → logo da AEDB (exibido na barra lateral)  

---

## 🔑 Configuração de credenciais

Para registrar feedbacks diretamente no **Google Sheets**, é usada uma **Service Account** do Google.

### 1. Criar Service Account
- Vá no [Google Cloud Console](https://console.cloud.google.com/)  
- Crie um projeto e ative:
  - **Google Sheets API**
  - **Google Drive API**
- Crie uma credencial do tipo **Service Account**
- Gere uma chave em formato **JSON**  

### 2. Compartilhar planilhas
- Abra a planilha de editais (leitura) e a planilha de feedbacks (`feedback_editais`)  
- Clique em **Compartilhar**  
- Adicione o e-mail da service account (do campo `client_email` do JSON) como **Editor**  

### 3. Configurar no Streamlit Cloud
- Vá em **Settings → Secrets** no seu app publicado  
- Cole o conteúdo do JSON no formato TOML:

```toml
[gcp_service_account]
type = "service_account"
project_id = "painel-editais"
private_key_id = "xxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nABC123...\n-----END PRIVATE KEY-----\n"
client_email = "painel-editais@streamlit-service.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
