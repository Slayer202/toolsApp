import os
import shutil
from datetime import datetime

# Créer un dossier release s'il n'existe pas
release_dir = "release"
if not os.path.exists(release_dir):
    os.makedirs(release_dir)

# Nom du fichier zip avec la date
zip_name = f"bouge-ton-cul_{datetime.now().strftime('%Y%m%d')}.zip"
zip_path = os.path.join(release_dir, zip_name)

# Liste des fichiers à inclure
files_to_include = [
    'app.py',
    'models.py',
    'extensions.py',
    'init_db.py',
    'requirements.txt',
    'templates',
    'README.md'
]

# Créer un fichier README s'il n'existe pas
if not os.path.exists('README.md'):
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write("""# Bouge Ton Cul - Application de recherche d'activités

## Installation

1. Assurez-vous d'avoir Python 3.8 ou supérieur installé
2. Ouvrez un terminal et naviguez vers le dossier du projet
3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```
4. Initialisez la base de données :
   ```
   python init_db.py
   ```
5. Lancez le serveur :
   ```
   python app.py
   ```
6. Ouvrez votre navigateur et allez sur : http://localhost:8080

## Utilisation

1. Créez un compte en cliquant sur "Inscription"
2. Connectez-vous avec vos identifiants
3. Entrez le nom d'une ville et un rayon de recherche
4. Explorez les activités disponibles !
""")

# Créer le zip
shutil.make_archive(zip_path[:-4], 'zip', '.', include_dir=files_to_include)

print(f"\nArchive créée avec succès : {zip_path}")
print("Envoyez ce fichier à votre ami avec les instructions du README.md")
