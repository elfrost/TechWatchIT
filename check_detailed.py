#!/usr/bin/env python3

import pymysql
from config.config import Config

def check_detailed():
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print('🔍 VÉRIFICATION DÉTAILLÉE DES ARTICLES TRAITÉS')
            print('=' * 60)
            
            # Vérifier les catégories "Other"
            cursor.execute('SELECT COUNT(*) FROM processed_articles WHERE category = "Other"')
            other_result = cursor.fetchone()
            other_count = other_result[0] if other_result else 0
            print(f'❌ Articles "Other": {other_count}')
            
            # Vérifier les catégories réelles
            cursor.execute('SELECT category, COUNT(*) FROM processed_articles GROUP BY category ORDER BY COUNT(*) DESC')
            categories = cursor.fetchall()
            print('\n📂 TOUTES LES CATÉGORIES:')
            for cat, count in categories:
                print(f'   {cat}: {count} articles')
            
            # Exemples d'articles avec résumés
            print('\n✨ EXEMPLES D\'ARTICLES AVEC RÉSUMÉS:')
            cursor.execute('''
                SELECT ra.title, pa.category, pa.technology, LEFT(pa.summary, 100) as summary_preview
                FROM processed_articles pa
                JOIN raw_articles ra ON pa.raw_article_id = ra.id
                WHERE pa.summary IS NOT NULL AND pa.summary != ""
                ORDER BY pa.processed_at DESC 
                LIMIT 5
            ''')
            
            examples = cursor.fetchall()
            for i, (title, category, tech, summary) in enumerate(examples, 1):
                print(f'\n{i}. {title[:60]}...')
                print(f'   📂 Catégorie: {category}')
                print(f'   🔧 Technologie: {tech}')
                print(f'   📝 Résumé: {summary}...')
            
            # Vérifier articles sans résumé
            cursor.execute('SELECT COUNT(*) FROM processed_articles WHERE summary IS NULL OR summary = ""')
            no_summary_result = cursor.fetchone()
            no_summary_count = no_summary_result[0] if no_summary_result else 0
            print(f'\n❌ Articles sans résumé: {no_summary_count}')
            
            # Vérifier si il y a des articles récents non traités
            cursor.execute('''
                SELECT COUNT(*) 
                FROM raw_articles ra 
                LEFT JOIN processed_articles pa ON ra.id = pa.raw_article_id 
                WHERE pa.id IS NULL
            ''')
            unprocessed_result = cursor.fetchone()
            unprocessed_count = unprocessed_result[0] if unprocessed_result else 0
            print(f'⏳ Articles non traités: {unprocessed_count}')
            
        connection.close()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')

if __name__ == '__main__':
    check_detailed() 