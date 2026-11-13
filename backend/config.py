import os

from dotenv import load_dotenv

# Procura o .env subindo a partir da pasta atual, então funciona rodando de backend/ ou da raiz
load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "8"))
    SALON_EMAIL_DOMAIN = os.getenv("SALON_EMAIL_DOMAIN", "salaobelle.com.br").lower()

    # Dados do salão que aparecem nos e-mails de confirmação
    SALON_NAME = os.getenv("SALON_NAME", "Salão Belle")
    SALON_ADDRESS = os.getenv("SALON_ADDRESS", "")
    SALON_PHONE = os.getenv("SALON_PHONE", "")

    # SMTP. Com SMTP_HOST vazio a API não envia e-mail, só registra no log.
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SECURITY = os.getenv("SMTP_SECURITY", "starttls").lower()  # starttls, ssl ou none
    MAIL_FROM = os.getenv("MAIL_FROM", "") or os.getenv("SMTP_USER", "") or "nao-responda@salaobelle.com.br"
