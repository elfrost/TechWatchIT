#!/usr/bin/env python3

import pymysql
from config.config import Config

def check_mysql():
    try:
        print('🔍 Vérification base de données MySQL:')
        print(f'🔌 Connexion à {Config.MYSQL_HOST}:{Config.MYSQL_PORT}')
        print(f'📊 Base de données: {Config.MYSQL_DATABASE}')
        
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Articles bruts
            cursor.execute('SELECT COUNT(*) FROM raw_articles')
            raw_result = cursor.fetchone()
            raw_count = raw_result[0] if raw_result else 0
            print(f'📄 Articles bruts: {raw_count}')
            
            # Articles traités
            cursor.execute('SELECT COUNT(*) FROM processed_articles')
            processed_result = cursor.fetchone()
            processed_count = processed_result[0] if processed_result else 0
            print(f'🤖 Articles traités: {processed_count}')
            
            # Catégories
            if processed_count > 0:
                print('\n📂 Répartition par catégorie:')
                cursor.execute('SELECT category, COUNT(*) FROM processed_articles GROUP BY category ORDER BY COUNT(*) DESC')
                categories = cursor.fetchall()
                for cat, count in categories:
                    print(f'   {cat}: {count} articles')
                
                # Résumés
                print('\n✨ Résumés AI:')
                cursor.execute('SELECT COUNT(*) FROM processed_articles WHERE summary IS NOT NULL AND summary != ""')
                summary_result = cursor.fetchone()
                with_summary = summary_result[0] if summary_result else 0
                print(f'   ✅ Avec résumé: {with_summary}')
                print(f'   ❌ Sans résumé: {processed_count - with_summary}')
            
            # Sources
            if raw_count > 0:
                print('\n📡 Sources actives:')
                cursor.execute('SELECT feed_source, COUNT(*) FROM raw_articles GROUP BY feed_source ORDER BY COUNT(*) DESC')
                sources = cursor.fetchall()
                for source, count in sources:
                    print(f'   {source}: {count} articles')
        
        connection.close()
        
    except Exception as e:
        print(f'❌ Erreur MySQL: {e}')

if __name__ == '__main__':
    check_mysql() 