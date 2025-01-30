from app import app, db
from models import User
import os
from sqlalchemy import inspect

def init_db():
    # Supprimer la base de données existante si elle existe
    db_path = 'instance/site.db'
    if os.path.exists(db_path):
        os.remove(db_path)

    with app.app_context():
        # Créer toutes les tables
        db.create_all()
        print("Base de données créée avec succès !")
        
        # Vérifier que la table user existe
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables créées : {tables}")
        
        if 'user' not in tables:
            print("ERREUR : La table 'user' n'a pas été créée correctement !")
        else:
            print("La table 'user' a été créée avec succès !")

if __name__ == '__main__':
    init_db()
