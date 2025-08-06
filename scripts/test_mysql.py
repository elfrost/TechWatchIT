#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion MySQL sur TEST-WAMP
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from config.config import Config

def test_mysql_connection():
    """Tester la connexion MySQL"""
    print("🧪 Test de connexion MySQL sur TEST-WAMP")
    print("=" * 50)
    
    try:
        print(f"🔌 Tentative de connexion à:")
        print(f"   Host: {Config.MYSQL_HOST}")
        print(f"   Port: {Config.MYSQL_PORT}")
        print(f"   User: {Config.MYSQL_USER}")
        print(f"   Password: {'(vide)' if not Config.MYSQL_PASSWORD else '***'}")
        
        # Test de connexion de base
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        print("✅ Connexion MySQL réussie !")
        
        # Test des privilèges
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"📋 Bases de données disponibles: {len(databases)}")
            
            # Vérifier les privilèges de création
            cursor.execute("SELECT USER(), DATABASE()")
            user_info = cursor.fetchone()
            print(f"👤 Utilisateur connecté: {user_info[0]}")
            
            # Test de création de base temporaire
            test_db = "test_techwatchit_temp"
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {test_db}")
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db}")
            print("✅ Privilèges de création/suppression confirmés")
            
        connection.close()
        print("\n🎉 MySQL est prêt pour TechWatchIT !")
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez que WAMP est démarré")
        print("   2. Vérifiez que MySQL est actif (icône verte)")
        print("   3. Vérifiez que le port 3306 n'est pas bloqué")
        print("   4. Testez avec phpMyAdmin: http://localhost/phpmyadmin")
        return False
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1) 