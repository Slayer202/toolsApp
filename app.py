from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import json
from waitress import serve
import time
from flask_login import current_user, login_user, logout_user, login_required
from extensions import db, bcrypt, login_manager
import logging
from werkzeug.urls import url_encode, url_decode  # Explicitly import url_decode

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète_très_longue_et_aléatoire'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser les extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# Import des modèles après l'initialisation
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.debug(f"Données reçues : {data}")
            
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if not username or not email or not password:
                logger.error("Données manquantes dans la requête")
                return jsonify({'error': 'Tous les champs sont requis'}), 400
            
            if User.query.filter_by(username=username).first():
                logger.warning(f"Nom d'utilisateur déjà pris : {username}")
                return jsonify({'error': 'Ce nom d\'utilisateur est déjà pris'}), 400
                
            if User.query.filter_by(email=email).first():
                logger.warning(f"Email déjà utilisé : {email}")
                return jsonify({'error': 'Cette adresse email est déjà utilisée'}), 400
            
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            
            logger.debug("Ajout de l'utilisateur à la base de données")
            db.session.add(user)
            db.session.commit()
            logger.info(f"Nouvel utilisateur créé : {username}")
            
            return jsonify({'success': 'Compte créé avec succès !'}), 200
            
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription : {str(e)}")
            db.session.rollback()
            return jsonify({'error': f'Erreur lors de l\'inscription : {str(e)}'}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            return jsonify({'success': 'Connexion réussie !'}), 200
        else:
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recherche', methods=['POST'])
def recherche_activites():
    try:
        data = request.get_json()
        ville = data.get('ville', '')
        rayon = min(data.get('rayon', 40), 100)  # Limite le rayon à 100km maximum

        # Géocodage de la ville
        geolocator = Nominatim(user_agent="activites-france")
        location = geolocator.geocode(f"{ville}, France", timeout=10)
        
        if not location:
            return jsonify({"error": "Ville non trouvée. Vérifiez l'orthographe."}), 404

        # Recherche des activités via OpenStreetMap
        activites = rechercher_activites_osm(location.latitude, location.longitude, rayon)
        
        if not activites:
            return jsonify({
                "activites": [],
                "centre": {
                    "lat": location.latitude,
                    "lon": location.longitude
                },
                "rayon": rayon,
                "message": f"Aucune activité trouvée dans un rayon de {rayon}km."
            })

        # Calculer les distances pour chaque activité
        for activite in activites:
            distance = geodesic(
                (location.latitude, location.longitude),
                (activite['lat'], activite['lon'])
            ).kilometers
            activite['distance'] = round(distance, 2)

        return jsonify({
            "activites": activites,
            "centre": {
                "lat": location.latitude,
                "lon": location.longitude
            },
            "rayon": rayon
        })

    except Exception as e:
        print(f"Erreur serveur: {str(e)}")
        return jsonify({"error": "Une erreur est survenue. Veuillez réessayer."}), 500

def rechercher_activites_osm(lat, lon, rayon_km, max_retries=3):
    # Convertir le rayon en mètres
    rayon_m = rayon_km * 1000
    
    # Version simplifiée de la requête pour éviter les timeouts
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    (
        // Loisirs essentiels
        node["leisure"~"sports_centre|swimming_pool|park"](around:{rayon_m},{lat},{lon});
        way["leisure"~"sports_centre|swimming_pool|park"](around:{rayon_m},{lat},{lon});
        
        // Sports populaires
        node["sport"~"fitness|swimming|tennis"](around:{rayon_m},{lat},{lon});
        way["sport"~"fitness|swimming|tennis"](around:{rayon_m},{lat},{lon});
        
        // Culture et tourisme principaux
        node["tourism"~"museum|gallery"](around:{rayon_m},{lat},{lon});
        way["tourism"~"museum|gallery"](around:{rayon_m},{lat},{lon});
        
        // Divertissement essentiel
        node["amenity"~"theatre|cinema|restaurant"](around:{rayon_m},{lat},{lon});
        way["amenity"~"theatre|cinema|restaurant"](around:{rayon_m},{lat},{lon});
    );
    out body center;
    >;
    out skel qt;
    """
    
    for attempt in range(max_retries):
        try:
            response = requests.post(overpass_url, data={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            activites = []
            for element in data.get("elements", []):
                if "tags" in element:
                    tags = element["tags"]
                    nom = tags.get("name")
                    if not nom or nom == "Sans nom":
                        continue
                    
                    type_activite = None
                    if "leisure" in tags:
                        type_activite = "Loisir: " + tags["leisure"].replace("_", " ").title()
                    elif "sport" in tags:
                        type_activite = "Sport: " + tags["sport"].replace("_", " ").title()
                    elif "tourism" in tags:
                        type_activite = "Tourisme: " + tags["tourism"].replace("_", " ").title()
                    elif "amenity" in tags:
                        type_activite = "Lieu: " + tags["amenity"].replace("_", " ").title()
                    
                    if type_activite:
                        if element["type"] == "node":
                            lat_act = element.get("lat")
                            lon_act = element.get("lon")
                        else:  # way ou relation
                            center = element.get("center", {})
                            lat_act = center.get("lat")
                            lon_act = center.get("lon")
                        
                        if lat_act and lon_act:
                            activite = {
                                "nom": nom,
                                "type": type_activite,
                                "lat": lat_act,
                                "lon": lon_act,
                                "description": tags.get("description", ""),
                                "website": tags.get("website", ""),
                                "phone": tags.get("phone", tags.get("contact:phone", "")),
                                "address": tags.get("addr:street", "") + " " + tags.get("addr:housenumber", "")
                            }
                            activites.append(activite)
            
            return activites
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)  # Attendre 2 secondes avant de réessayer
                continue
            return []
        except Exception as e:
            print(f"Erreur lors de la recherche d'activités: {str(e)}")
            return []

@app.route('/localisation', methods=['GET', 'POST'])
def localisation():
    location = None
    ip = None
    if request.method == 'POST':
        ip = request.form.get('ip_address')
        location = get_ip_location(ip)
    return render_template('localisation.html', location=location, ip=ip)

def get_ip_location(ip_address):
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        return {
            'ville': response.get('city', 'Inconnu'),
            'pays': response.get('country_name', 'Inconnu'),
            'latitude': response.get('latitude', 'N/A'),
            'longitude': response.get('longitude', 'N/A'),
            'region': response.get('region', 'Inconnu'),
            'code_postal': response.get('postal', 'Inconnu')
        }
    except Exception as e:
        return {'erreur': str(e)}

if __name__ == '__main__':
    # Récupérer l'adresse IP locale
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\nServeur démarré !")
    print(f"URL locale : http://localhost:8080")
    print(f"URL pour vos amis : http://{local_ip}:8080")
    print("\nPartagez l'URL pour vos amis pour qu'ils puissent accéder au site !")
    print("Pour arrêter le serveur : Ctrl+C\n")
    
    serve(app, host='0.0.0.0', port=8080, threads=4)
