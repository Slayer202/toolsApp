import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
