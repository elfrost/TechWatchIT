#!/usr/bin/env python3
"""
TechWatchIT - Script principal
Orchestrateur principal pour toutes les fonctionnalités de TechWatchIT
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Ajouter le répertoire du projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from src.database import db
from src.fetch_feeds import FeedFetcher
from src.classifier import classifier
from src.summarizer import summarizer
from scripts.daily_digest import DailyDigest
from scripts.alert_handler import CriticalAlertHandler

def setup_logging():
    """Configurer le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/main.log') if os.path.exists('logs') else logging.NullHandler()
        ]
    )
    return logging.getLogger('TechWatchIT')

def init_database():
    """Initialiser la base de données"""
    try:
        print("🗄️ Initialisation de la base de données...")
        db.init_database()
        print("✅ Base de données initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur initialisation base de données: {str(e)}")
        return False

def fetch_feeds():
    """Récupérer tous les flux RSS"""
    try:
        print("📡 Récupération des flux RSS...")
        fetcher = FeedFetcher()
        result = fetcher.fetch_all_feeds()
        total_articles = result['total_articles']
        print(f"✅ {total_articles} articles récupérés et sauvegardés")
        return total_articles
    except Exception as e:
        print(f"❌ Erreur récupération flux: {str(e)}")
        return 0

def process_articles():
    """Traiter les articles avec l'IA"""
    try:
        print("🤖 Traitement IA des articles...")
        
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
            print("ℹ️ Aucun article à traiter")
            return 0
        
        processed_count = 0
        
        for article in raw_articles:
            try:
                print(f"📊 Traitement: {article['title'][:60]}...")
                
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
                print(f"❌ Erreur traitement article {article['id']}: {str(e)}")
                continue
        
        print(f"✅ {processed_count} articles traités avec succès")
        return processed_count
        
    except Exception as e:
        print(f"❌ Erreur traitement IA: {str(e)}")
        return 0

def send_daily_digest():
    """Envoyer le digest quotidien"""
    try:
        print("📧 Envoi du digest quotidien...")
        digest = DailyDigest()
        success = digest.run_daily_digest()
        
        if success:
            print("✅ Digest quotidien envoyé avec succès")
        else:
            print("❌ Échec envoi digest quotidien")
        
        return success
    except Exception as e:
        print(f"❌ Erreur digest quotidien: {str(e)}")
        return False

def check_critical_alerts():
    """Vérifier et envoyer les alertes critiques"""
    try:
        print("🚨 Vérification des alertes critiques...")
        alert_handler = CriticalAlertHandler()
        sent_count = alert_handler.process_critical_alerts()
        
        if sent_count > 0:
            print(f"🚨 {sent_count} alertes critiques envoyées")
        else:
            print("✅ Aucune alerte critique en attente")
        
        return sent_count
    except Exception as e:
        print(f"❌ Erreur gestion alertes: {str(e)}")
        return 0

def run_full_pipeline():
    """Exécuter le pipeline complet"""
    print("🚀 TechWatchIT - Pipeline complet")
    print("=" * 50)
    
    # 1. Récupération des flux
    articles_fetched = fetch_feeds()
    
    # 2. Traitement IA
    if articles_fetched > 0:
        articles_processed = process_articles()
        print(f"📊 Résumé: {articles_fetched} récupérés, {articles_processed} traités")
    
    # 3. Vérification alertes critiques
    alerts_sent = check_critical_alerts()
    
    # 4. Statistiques finales
    print("\n📈 Statistiques finales:")
    try:
        stats = db.get_dashboard_stats(1)  # Dernières 24h
        general = stats.get('general', {})
        print(f"   • Articles totaux: {general.get('total_articles', 0)}")
        print(f"   • Alertes sécurité: {general.get('security_alerts', 0)}")
        print(f"   • Articles critiques: {general.get('critical', 0)}")
    except:
        pass
    
    print("\n✅ Pipeline terminé")

def show_status():
    """Afficher l'état du système"""
    print("📊 TechWatchIT - État du système")
    print("=" * 40)
    
    # Test base de données
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
        print("✅ Base de données: Connectée")
    except Exception as e:
        print(f"❌ Base de données: Erreur - {str(e)}")
    
    # Test OpenAI
    if Config.OPENAI_API_KEY:
        print("✅ OpenAI: Configuré")
    else:
        print("⚠️  OpenAI: Non configuré")
    
    # Test SMTP
    if all([Config.SMTP_USERNAME, Config.SMTP_PASSWORD]):
        print("✅ SMTP: Configuré")
    else:
        print("⚠️  SMTP: Non configuré")
    
    # Statistiques
    try:
        stats = db.get_dashboard_stats(7)
        general = stats.get('general', {})
        print(f"\n📈 Statistiques (7 derniers jours):")
        print(f"   • Articles totaux: {general.get('total_articles', 0)}")
        print(f"   • Alertes sécurité: {general.get('security_alerts', 0)}")
        print(f"   • Articles critiques: {general.get('critical', 0)}")
        print(f"   • Articles importants: {general.get('high', 0)}")
    except Exception as e:
        print(f"❌ Erreur récupération statistiques: {str(e)}")

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='TechWatchIT - Plateforme de veille IT centralisée',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py --init                    # Initialiser la base de données
  python main.py --fetch                   # Récupérer les flux RSS
  python main.py --process                 # Traiter avec l\'IA
  python main.py --digest                  # Envoyer le digest quotidien
  python main.py --alerts                  # Vérifier les alertes critiques
  python main.py --pipeline                # Exécuter le pipeline complet (fetch + process + alerts)')
  python main.py --status                  # Afficher l\'état du système
  python main.py --api                     # Lancer l\'API web
        """
    )
    
    parser.add_argument('--init', action='store_true',
                        help='Initialiser la base de données')
    parser.add_argument('--fetch', action='store_true',
                        help='Récupérer les flux RSS')
    parser.add_argument('--process', action='store_true',
                        help='Traiter les articles avec l\'IA')
    parser.add_argument('--digest', action='store_true',
                        help='Envoyer le digest quotidien')
    parser.add_argument('--alerts', action='store_true',
                        help='Vérifier et envoyer les alertes critiques')
    parser.add_argument('--pipeline', action='store_true',
                        help='Exécuter le pipeline complet (fetch + process + alerts)')
    parser.add_argument('--status', action='store_true',
                        help='Afficher l\'état du système')
    parser.add_argument('--api', action='store_true',
                        help='Lancer l\'API web')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mode verbeux')
    
    args = parser.parse_args()
    
    # Configuration du logging
    if args.verbose:
        setup_logging()
    
    # Si aucun argument, afficher l'aide
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        print(f"🚀 TechWatchIT - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if args.init:
            success = init_database()
            sys.exit(0 if success else 1)
        
        elif args.fetch:
            articles = fetch_feeds()
            sys.exit(0 if articles > 0 else 1)
        
        elif args.process:
            processed = process_articles()
            sys.exit(0 if processed >= 0 else 1)
        
        elif args.digest:
            success = send_daily_digest()
            sys.exit(0 if success else 1)
        
        elif args.alerts:
            alerts = check_critical_alerts()
            sys.exit(0)
        
        elif args.pipeline:
            run_full_pipeline()
            sys.exit(0)
        
        elif args.status:
            show_status()
            sys.exit(0)
        
        elif args.api:
            print("🌐 Lancement de l'API TechWatchIT...")
            print(f"📊 Dashboard disponible sur: http://localhost:{Config.API_PORT}/dashboard")
            from src.api import app
            app.run(
                host=Config.API_HOST,
                port=Config.API_PORT,
                debug=Config.API_DEBUG
            )
    
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 