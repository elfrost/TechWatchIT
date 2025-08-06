"""
TechWatchIT - Script d'initialisation de la base de données
Création des tables MySQL et import de données de test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

from config.config import Config
from src.database import db

class DatabaseSetup:
    """Gestionnaire de setup de la base de données"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.connection_params = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    def create_database(self) -> bool:
        """Créer la base de données si elle n'existe pas"""
        try:
            print(f"🔌 Connexion à MySQL sur {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
            print(f"👤 Utilisateur: {Config.MYSQL_USER}")
            print(f"🗄️ Base de données cible: {Config.MYSQL_DATABASE}")
            
            # Connexion sans spécifier la base pour la créer
            connection = pymysql.connect(**self.connection_params)
            print("✅ Connexion MySQL réussie")
            
            with connection.cursor() as cursor:
                # Créer la base de données
                print(f"📝 Création de la base de données '{Config.MYSQL_DATABASE}'...")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.execute(f"USE {Config.MYSQL_DATABASE}")
                
                connection.commit()
                print(f"✅ Base de données '{Config.MYSQL_DATABASE}' créée/vérifiée")
                self.logger.info(f"✅ Base de données '{Config.MYSQL_DATABASE}' créée/vérifiée")
                
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur création base de données: {str(e)}")
            print("💡 Vérifiez que:")
            print("   - WAMP est démarré")
            print("   - MySQL est actif (icône verte)")
            print("   - Le port 3306 est libre")
            print("   - L'utilisateur 'root' existe sans mot de passe")
            self.logger.error(f"❌ Erreur création base de données: {str(e)}")
            return False
    
    def init_tables(self) -> bool:
        """Initialiser toutes les tables"""
        try:
            self.logger.info("🗄️ Initialisation des tables MySQL...")
            db.init_database()
            self.logger.info("✅ Tables initialisées avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation tables: {str(e)}")
            return False
    
    def insert_sample_data(self) -> bool:
        """Insérer des données d'exemple pour les tests"""
        try:
            self.logger.info("📊 Insertion de données d'exemple...")
            
            sample_articles = [
                {
                    'title': 'FortiOS Critical Security Update - CVE-2024-12345',
                    'link': 'https://www.fortiguard.com/psirt/FG-IR-24-001',
                    'description': 'Critical vulnerability in FortiOS SSL VPN component.',
                    'published_date': datetime.now() - timedelta(hours=2),
                    'content': 'A critical vulnerability has been discovered in FortiOS.',
                    'guid': 'FG-IR-24-001',
                    'tags': 'security,critical,ssl-vpn',
                    'feed_source': 'FortiGate',
                    'category': 'Security Advisory'
                },
                {
                    'title': 'VMware vCenter Server Security Advisory',
                    'link': 'https://www.vmware.com/security/advisories/VMSA-2024-0001.html',
                    'description': 'High severity vulnerability in vCenter Server.',
                    'published_date': datetime.now() - timedelta(hours=6),
                    'content': 'VMware vCenter Server contains a vulnerability.',
                    'guid': 'VMSA-2024-0001',
                    'tags': 'security,vcenter',
                    'feed_source': 'VMware',
                    'category': 'Security Advisory'
                }
            ]
            
            # Insérer les articles
            for article in sample_articles:
                article_id = db.save_raw_article(article)
                if article_id:
                    self.logger.info(f"📝 Article exemple inséré: {article['title'][:50]}...")
            
            self.logger.info("✅ Données d'exemple insérées avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur insertion données exemple: {str(e)}")
            return False
    
    def run_full_setup(self) -> bool:
        """Exécuter le setup complet"""
        try:
            self.logger.info("🚀 Début du setup complet de TechWatchIT...")
            
            # 1. Créer la base de données
            if not self.create_database():
                return False
            
            # 2. Initialiser les tables
            if not self.init_tables():
                return False
            
            # 3. Insérer des données d'exemple
            if not self.insert_sample_data():
                return False
            
            self.logger.info("✅ Setup complet terminé avec succès !")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ Erreur setup complet: {str(e)}")
            return False

def main():
    """Point d'entrée principal"""
    try:
        print("🚀 TechWatchIT - Initialisation de la base de données MySQL")
        print("=" * 60)
        
        setup = DatabaseSetup()
        
        # Exécuter le setup
        success = setup.run_full_setup()
        
        if success:
            print("\n✅ Setup terminé avec succès !")
            print("🌐 Vous pouvez maintenant:")
            print("   1. Lancer l'API: python src/api.py")
            print("   2. Récupérer des flux: python src/fetch_feeds.py")
            sys.exit(0)
        else:
            print("\n❌ Échec du setup")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur fatale: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 