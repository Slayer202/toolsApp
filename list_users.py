from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    print("\nListe des utilisateurs enregistrés :")
    print("-" * 50)
    for user in users:
        print(f"Nom d'utilisateur : {user.username}")
        print(f"Email : {user.email}")
        print(f"Date d'inscription : {user.created_at}")
        print("-" * 50)
