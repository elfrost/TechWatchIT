"""
TechWatchIT - API REST
API Flask pour servir les données de veille IT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import pytz  # Ajout de pytz

from config.config import Config
from src.database import db
from src.fetch_feeds import FeedFetcher
from src.classifier import classifier
from src.summarizer import summarizer

# Initialisation de Flask
app = Flask(__name__, 
           static_folder='../web/static',
           template_folder='../web/templates')

# Configuration CORS pour permettre les requêtes depuis le frontend
CORS(app)

# Configuration Flask
app.config['DEBUG'] = Config.API_DEBUG
app.config['JSON_AS_ASCII'] = False  # Support UTF-8

# Logger
logger = Config.setup_logging()

# ================================
# ROUTES PRINCIPALES
# ================================

@app.route('/')
def index():
    """Page d'accueil de l'API"""
    return jsonify({
        'name': 'TechWatchIT API',
        'version': '1.0.0',
        'description': 'API de veille IT centralisée avec IA',
        'endpoints': {
            'articles': '/api/articles',
            'stats': '/api/stats',
            'dashboard': '/dashboard',
            'health': '/health'
        }
    })

@app.route('/health')
def health_check():
    """Vérification de l'état de l'API"""
    try:
        # Test de connexion base de données
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            db_status = 'OK'
    except Exception as e:
        db_status = f'ERROR: {str(e)}'
    
    return jsonify({
        'status': 'OK' if db_status == 'OK' else 'ERROR',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'openai': 'OK' if Config.OPENAI_API_KEY else 'NOT_CONFIGURED'
    })

# ================================
# ROUTES API ARTICLES
# ================================

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """
    Récupérer les articles avec filtres optionnels
    
    Paramètres:
    - category: fortigate, sentinelone, jumpcloud, vmware, rubrik, dell, exploits
    - technology: alias pour category
    - severity: low, medium, high, critical
    - security_alerts_only: true/false
    - days_back: nombre de jours à remonter (défaut: 30)
    - limit: nombre d'articles max (défaut: 100)
    """
    try:
        # Récupérer les paramètres de filtrage
        filters = {}
        
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        if request.args.get('technology'):
            filters['technology'] = request.args.get('technology')
        
        if request.args.get('severity'):
            filters['severity'] = request.args.get('severity')
        
        if request.args.get('security_alerts_only') == 'true':
            filters['security_alerts_only'] = True
        
        if request.args.get('days_back'):
            filters['days_back'] = int(request.args.get('days_back'))
        else:
            filters['days_back'] = 30
        
        if request.args.get('limit'):
            filters['limit'] = int(request.args.get('limit'))
        else:
            filters['limit'] = 100
        
        # Récupérer les articles
        articles = db.get_articles(filters)
        
        # Formater les dates pour JSON en convertissant vers le fuseau horaire local
        local_tz = pytz.timezone('America/Toronto')
        utc_tz = pytz.utc
        
        for article in articles:
            if article.get('published_date'):
                # Assumer que la date de la DB est en UTC (naïve) et la convertir
                published_date_utc = utc_tz.localize(article['published_date'])
                published_date_local = published_date_utc.astimezone(local_tz)
                article['published_date'] = published_date_local.isoformat()

            if article.get('created_at'):
                created_at_utc = utc_tz.localize(article['created_at'])
                created_at_local = created_at_utc.astimezone(local_tz)
                article['created_at'] = created_at_local.isoformat()
                
            if article.get('processed_at'):
                processed_at_utc = utc_tz.localize(article['processed_at'])
                processed_at_local = processed_at_utc.astimezone(local_tz)
                article['processed_at'] = processed_at_local.isoformat()
        
        return jsonify({
            'success': True,
            'count': len(articles),
            'filters': filters,
            'articles': articles
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur API articles: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    """Récupérer les détails d'un article spécifique"""
    try:
        # Récupérer l'article directement par ID
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT 
                p.id, p.raw_article_id, p.category, p.technology, p.severity_level, 
                p.severity_score, p.cvss_score, p.summary, p.impact_analysis, p.action_required,
                p.is_security_alert, p.processed_at,
                r.title as raw_title,
                r.content as raw_content,
                r.link,
                r.published_date
            FROM processed_articles p
            LEFT JOIN raw_articles r ON p.raw_article_id = r.id
            WHERE p.id = %s
            ''', (article_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Article non trouvé'
                }), 404
            
            # Définir les fuseaux horaires
            local_tz = pytz.timezone('America/Toronto')
            utc_tz = pytz.utc

            def convert_to_local_iso(utc_naive_date):
                if not utc_naive_date:
                    return None
                return utc_tz.localize(utc_naive_date).astimezone(local_tz).isoformat()
            
            # Construire l'objet article avec gestion d'erreurs (MySQL retourne un dict)
            try:
                article = {
                    'id': result['id'],
                    'title': result['raw_title'] or "Titre non disponible",
                    'technology': result['technology'],
                    'severity_level': result['severity_level'],
                    'cvss_score': result['cvss_score'],
                    'is_security_alert': bool(result['is_security_alert']),
                    'ai_summary': result['summary'],
                    'ai_impact': result['impact_analysis'],
                    'ai_action': result['action_required'],
                    'processed_at': convert_to_local_iso(result['processed_at']),
                    'content': result['raw_content'] or "",
                    'link': result['link'] or "",
                    'published_date': convert_to_local_iso(result['published_date'])
                }
                
                logger.info(f"✅ Article {article_id} formaté avec succès")
                
            except KeyError as ke:
                logger.error(f"❌ Erreur clé manquante article {article_id}: {str(ke)} - Clés disponibles: {list(result.keys()) if result else 'Aucune'}")
                raise ke
        
        return jsonify(article)
        
    except Exception as e:
        logger.error(f"❌ Erreur API article détail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================
# ROUTES API STATISTIQUES
# ================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Récupérer les statistiques du dashboard
    
    Paramètres:
    - days: nombre de jours à analyser (défaut: 30)
    """
    try:
        days = int(request.args.get('days', 30))
        stats = db.get_dashboard_stats(days)
        
        return jsonify({
            'success': True,
            'period_days': days,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur API stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/summary', methods=['GET'])
def get_stats_summary():
    """Résumé rapide des statistiques"""
    try:
        stats = db.get_dashboard_stats(7)  # 7 derniers jours
        
        general = stats.get('general', {})
        
        summary = {
            'total_articles': general.get('total_articles', 0),
            'security_alerts': general.get('security_alerts', 0),
            'critical_count': general.get('critical', 0),
            'high_count': general.get('high', 0),
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur API summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================
# ROUTES ADMINISTRATIVES
# ================================

@app.route('/api/admin/fetch', methods=['POST'])
def trigger_fetch():
    """Déclencher manuellement la récupération des flux RSS"""
    try:
        fetcher = FeedFetcher()
        total_articles = fetcher.fetch_all_feeds()
        
        return jsonify({
            'success': True,
            'message': f'Récupération terminée: {total_articles} articles traités',
            'total_articles': total_articles
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur fetch manuel: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/process', methods=['POST'])
def trigger_processing():
    """Déclencher le traitement IA des articles non traités"""
    try:
        # Récupérer les articles non traités
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT r.* FROM raw_articles r
            LEFT JOIN processed_articles p ON r.id = p.raw_article_id
            WHERE p.id IS NULL
            ORDER BY r.created_at DESC
            LIMIT 50
            ''')
            raw_articles = cursor.fetchall()
        
        if not raw_articles:
            return jsonify({
                'success': True,
                'message': 'Aucun article à traiter',
                'processed_count': 0
            })
        
        processed_count = 0
        
        for article in raw_articles:
            try:
                # Classifier l'article
                classification = classifier.classify_article(article)
                
                # Générer un résumé
                summary = summarizer.summarize_article(article, classification)
                
                # Fusionner les données
                processed_data = {**classification, **summary}
                
                # Sauvegarder
                if db.save_processed_article(article['id'], processed_data):
                    processed_count += 1
                
            except Exception as e:
                logger.error(f"Erreur traitement article {article['id']}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Traitement terminé: {processed_count} articles traités',
            'processed_count': processed_count
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement manuel: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/init-db', methods=['POST'])
def init_database():
    """Initialiser la base de données"""
    try:
        db.init_database()
        return jsonify({
            'success': True,
            'message': 'Base de données initialisée avec succès'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur init DB: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================================
# ROUTES DASHBOARD WEB
# ================================

@app.route('/dashboard')
def dashboard():
    """Page dashboard web"""
    try:
        return send_from_directory('../web', 'dashboard.html')
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@app.route('/blog')
def blog_dashboard():
    """Page blog avec analyses détaillées"""
    try:
        return send_from_directory('../web', 'blog_dashboard.html')
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@app.route('/web/<path:filename>')
def serve_web_files(filename):
    """Servir les fichiers statiques du dashboard"""
    try:
        return send_from_directory('../web', filename)
    except Exception as e:
        return f"Fichier non trouvé: {filename}", 404

# ================================
# GESTION D'ERREURS
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint non trouvé',
        'available_endpoints': [
            '/api/articles',
            '/api/stats',
            '/dashboard',
            '/health'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Erreur interne du serveur'
    }), 500

# ================================
# FONCTIONS UTILITAIRES
# ================================

def setup_database():
    """Initialiser la base de données au démarrage"""
    try:
        logger.info("🗄️ Initialisation de la base de données...")
        db.init_database()
        logger.info("✅ Base de données initialisée")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation DB: {str(e)}")
        raise

# ================================
# POINT D'ENTRÉE PRINCIPAL
# ================================

if __name__ == '__main__':
    try:
        logger.info("🚀 Démarrage de TechWatchIT API...")
        
        # Initialiser la base de données
        setup_database()
        
        # Afficher les informations de démarrage
        logger.info(f"🌐 API disponible sur: http://{Config.API_HOST}:{Config.API_PORT}")
        logger.info(f"📊 Dashboard web: http://{Config.API_HOST}:{Config.API_PORT}/dashboard")
        logger.info("📋 Endpoints disponibles:")
        logger.info("   - GET  /api/articles")
        logger.info("   - GET  /api/stats")
        logger.info("   - POST /api/admin/fetch")
        logger.info("   - POST /api/admin/process")
        logger.info("   - GET  /health")
        
        # Démarrer le serveur Flask
        app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=Config.API_DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt de l'API demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {str(e)}")
        raise 