import os

from dotenv import load_dotenv

# Procura o .env subindo a partir da pasta atual, então funciona rodando de backend/ ou da raiz
load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "8"))
    SALON_EMAIL_DOMAIN = os.getenv("SALON_EMAIL_DOMAIN", "salaobelle.com.br").lower()
