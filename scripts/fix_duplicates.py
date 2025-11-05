"""
Script de correction des doublons dans processed_articles
Supprime les doublons et ajoute la contrainte UNIQUE sur raw_article_id
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from config.config import Config
from src.database import db

def fix_duplicates():
    """Supprimer les doublons et ajouter la contrainte UNIQUE"""
    print("Correction des doublons dans processed_articles...")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Identifier les doublons
            print("\n[1/4] Identification des doublons...")
            cursor.execute('''
            SELECT raw_article_id, COUNT(*) as count
            FROM processed_articles
            GROUP BY raw_article_id
            HAVING count > 1
            ''')
            duplicates = cursor.fetchall()

            if not duplicates:
                print("[OK] Aucun doublon trouve")
            else:
                print(f"[WARNING] {len(duplicates)} articles en doublon trouves")

                # 2. Supprimer les doublons (garder le plus récent)
                print("\n[2/4] Suppression des doublons (conservation de la version la plus récente)...")
                for dup in duplicates:
                    raw_article_id = dup['raw_article_id']

                    # Garder uniquement l'entrée la plus récente
                    cursor.execute('''
                    DELETE FROM processed_articles
                    WHERE raw_article_id = %s
                    AND id NOT IN (
                        SELECT * FROM (
                            SELECT id FROM processed_articles
                            WHERE raw_article_id = %s
                            ORDER BY processed_at DESC
                            LIMIT 1
                        ) as keep_row
                    )
                    ''', (raw_article_id, raw_article_id))

                    deleted = cursor.rowcount
                    if deleted > 0:
                        print(f"   Supprimé {deleted} doublon(s) pour raw_article_id={raw_article_id}")

                conn.commit()
                print("[OK] Doublons supprimes")

            # 3. Vérifier si la contrainte existe déjà
            print("\n[3/4] Vérification de la contrainte UNIQUE...")
            cursor.execute('''
            SELECT COUNT(*) as constraint_exists
            FROM information_schema.statistics
            WHERE table_schema = %s
            AND table_name = 'processed_articles'
            AND index_name = 'raw_article_id'
            AND non_unique = 0
            ''', (Config.MYSQL_DATABASE,))

            result = cursor.fetchone()

            if result['constraint_exists'] > 0:
                print("[OK] Contrainte UNIQUE deja presente")
            else:
                # 4. Ajouter la contrainte UNIQUE
                print("\n[4/4] Ajout de la contrainte UNIQUE sur raw_article_id...")
                try:
                    cursor.execute('''
                    ALTER TABLE processed_articles
                    ADD UNIQUE KEY unique_raw_article (raw_article_id)
                    ''')
                    conn.commit()
                    print("[OK] Contrainte UNIQUE ajoutee avec succes")
                except pymysql.err.OperationalError as e:
                    if "Duplicate key name" in str(e):
                        print("[OK] Contrainte UNIQUE deja presente")
                    else:
                        raise

            # Statistiques finales
            print("\n[STATS] Statistiques finales:")
            cursor.execute('SELECT COUNT(*) as total FROM raw_articles')
            raw_count = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(*) as total FROM processed_articles')
            processed_count = cursor.fetchone()['total']

            cursor.execute('''
            SELECT COUNT(DISTINCT raw_article_id) as unique_processed
            FROM processed_articles
            ''')
            unique_count = cursor.fetchone()['unique_processed']

            print(f"   - Articles bruts: {raw_count}")
            print(f"   - Articles traites: {processed_count}")
            print(f"   - Articles uniques: {unique_count}")

            if processed_count == unique_count:
                print("\n[OK] Tous les articles sont maintenant uniques !")
            else:
                print(f"\n[WARNING] Attention: {processed_count - unique_count} doublons restants")

            return True

    except Exception as e:
        print(f"\n[ERROR] Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TechWatchIT - Correction des doublons")
    print("=" * 60)

    success = fix_duplicates()

    if success:
        print("\n[SUCCESS] Correction terminee avec succes")
        print("\n[INFO] Vous pouvez maintenant relancer le pipeline sans craindre les doublons")
        sys.exit(0)
    else:
        print("\n[ERROR] Echec de la correction")
        sys.exit(1)
