# TechWatchIT 🔍

Plateforme centralisée de monitoring IT pour Windows avec agrégation RSS, classification IA et alertes automatiques.

## 🎯 Fonctionnalités

- **Agrégation RSS** : Collecte automatique des feeds de sécurité IT
- **Classification IA** : Analyse GPT-4o avec fallback par mots-clés
- **Résumés intelligents** : TL;DR ≤6 phrases avec impact et actions
- **Base de données MySQL** : Stockage professionnel via WAMP
- **API REST** : Endpoints filtrables et statistiques
- **Interface web** : Dashboard Bootstrap 5 responsive
- **Notifications** : Digest quotidien + alertes critiques (CVSS ≥9.0)

## 🛠️ Technologies surveillées

- **FortiGate** (Fortinet PSIRT)
- **SentinelOne** (Security Advisories)
- **JumpCloud** (Release Notes)
- **VMware** (Security Advisories)
- **Rubrik** (Zero-Trust Blog)
- **Dell** (Security Advisories)
- **Exploits** (NVD JSON Feed)

## 📋 Prérequis

### Serveur TEST-WAMP
- **WAMP Server** installé et fonctionnel
- **MySQL** actif (icône verte dans WAMP)
- **Python 3.12** installé
- **Utilisateur MySQL** : `root` sans mot de passe
- **Port** : 3306 (par défaut)

### Clés API
- **OpenAI API Key** pour GPT-4o
- **Compte SMTP** Office 365 pour notifications

## 🚀 Installation

### 1. Préparation WAMP
```bash
# Vérifiez que WAMP est démarré
# Icône WAMP verte dans la barre des tâches
# Testez : http://localhost/phpmyadmin
```

### 2. Configuration du projet
```bash
# Clonez le projet
git clone https://github.com/elfrost/TechWatchIT.git
cd TechWatchIT

# Copiez et configurez l'environnement
copy env.example .env
# Éditez .env avec vos clés API
```

### 3. Installation automatique
```bash
# Exécutez le script d'installation
setup.bat
```

Le script va :
- ✅ Tester la connexion MySQL
- 📦 Installer les dépendances Python
- 🗄️ Créer la base de données `techwatchit`
- 📊 Initialiser les tables avec données d'exemple
- 🎉 Lancer le serveur de développement

### 4. Vérification
```bash
# Test manuel de MySQL
python scripts/test_mysql.py

# Accès au dashboard
http://localhost:5000
```

## 📁 Structure du projet

```
TechWatchIT/
├── config/
│   ├── __init__.py
│   └── config.py              # Configuration centralisée
├── src/
│   ├── __init__.py
│   ├── fetch_feeds.py         # Collecteur RSS
│   ├── classifier.py          # Classification IA
│   ├── summarizer.py          # Résumés intelligents
│   ├── database.py            # Gestionnaire MySQL
│   └── api.py                 # API REST Flask
├── scripts/
│   ├── test_mysql.py          # Test connexion MySQL
│   ├── setup_db.py            # Initialisation base
│   ├── daily_digest.py        # Digest quotidien
│   └── alert_handler.py       # Alertes critiques
├── web/
│   └── dashboard.html         # Interface utilisateur
├── logs/                      # Fichiers de logs
├── data/                      # Données temporaires
├── main.py                    # Script principal
├── requirements.txt           # Dépendances Python
├── setup.bat                  # Installation Windows
└── .env.example               # Template environnement
```

## ⚙️ Configuration (.env)

```env
# API OpenAI pour classification/résumés
OPENAI_API_KEY=your_openai_api_key_here

# Configuration MySQL pour TEST-WAMP
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=techwatchit

# Configuration SMTP Office 365
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=your_password
EMAIL_FROM=your_email@company.com
EMAIL_TO=admin@company.com

# Configuration serveur
FLASK_HOST=localhost
FLASK_PORT=5000
FLASK_DEBUG=True
```

## 🎮 Utilisation

### Lancement manuel
```bash
# Collecte RSS et traitement IA
python main.py --fetch

# Serveur API/Dashboard
python main.py --server

# Digest quotidien
python scripts/daily_digest.py

# Alertes critiques
python scripts/alert_handler.py
```

### API REST

```bash
# Articles récents
GET /api/articles?limit=10&technology=fortinet

# Statistiques
GET /api/stats

# Santé du système
GET /api/health
```

### Interface Web
- **Dashboard** : http://localhost:5000
- **Filtres** : Technologie, sévérité, date
- **Graphiques** : Évolution 30 jours
- **Administration** : Gestion des données

## 🔧 Dépannage

### Erreur MySQL
```bash
# Test de connexion
python scripts/test_mysql.py

# Vérifications :
# - WAMP démarré (icône verte)
# - MySQL actif dans WAMP
# - Port 3306 libre
# - phpMyAdmin accessible
```

### Erreur API OpenAI
```bash
# Vérifiez votre clé dans .env
# Testez avec classification manuelle
python -c "from src.classifier import *; print('OK')"
```

### Erreur SMTP
```bash
# Testez la configuration email
python -c "from scripts.daily_digest import *; test_smtp()"
```

## 📊 Base de données

### Tables principales
- `raw_articles` : Articles RSS bruts
- `processed_articles` : Articles traités avec IA
- `fetch_log` : Historique des collectes
- `alert_notifications` : Journal des alertes
- `daily_stats` : Statistiques quotidiennes

### Accès phpMyAdmin
http://localhost/phpmyadmin
- Utilisateur : `root`
- Mot de passe : (vide)
- Base : `techwatchit`

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez les logs dans `logs/`
2. Testez la connexion MySQL
3. Consultez la documentation WAMP
4. Vérifiez les clés API dans `.env`

---
**TechWatchIT** - Monitoring IT professionnel pour Windows 🚀 