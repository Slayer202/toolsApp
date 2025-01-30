# Activités France

## Description
Une application web pour découvrir et gérer des activités en France.

## Prérequis
- Python 3.12
- pip
- virtualenv

## Installation

1. Clonez le dépôt
```bash
git clone https://github.com/Slayer202/toolsApp.git
cd activites-france
```

2. Créez un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix
venv\Scripts\activate  # Sur Windows
```

3. Installez les dépendances
```bash
pip install -r requirements.txt
```

4. Configurez les variables d'environnement
```bash
cp .env.example .env
# Éditez .env avec vos paramètres
```

5. Initialisez la base de données
```bash
python init_db.py
```

6. Lancez l'application
```bash
flask run
```

## Déploiement
Consultez la documentation de votre hébergeur pour le déploiement spécifique.

## Licence
[À DÉFINIR]
