#!/usr/bin/env python3
"""
Script de mise à jour du schéma de base de données pour les analyses détaillées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager
import pymysql

def update_database_schema():
    """Mettre à jour le schéma de base de données"""
    print("🔧 Mise à jour du schéma de base de données TechWatchIT")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier les colonnes existantes
            cursor.execute("DESCRIBE processed_articles")
            existing_columns = {row['Field'] for row in cursor.fetchall()}
            
            print(f"📋 Colonnes existantes: {len(existing_columns)}")
            
            # Colonnes à ajouter pour les analyses détaillées
            new_columns = {
                'detailed_analysis': 'TEXT',
                'blog_article': 'LONGTEXT',
                'executive_summary': 'TEXT',
                'technical_insights': 'TEXT',
                'business_impact': 'TEXT',
                'action_plan': 'TEXT',
                'risk_assessment': 'TEXT',
                'recommendations': 'TEXT',
                'timeline_info': 'TEXT',
                'related_topics': 'TEXT'
            }
            
            # Ajouter les nouvelles colonnes si elles n'existent pas
            columns_added = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE processed_articles ADD COLUMN {column_name} {column_type}"
                        cursor.execute(sql)
                        print(f"✅ Colonne ajoutée: {column_name} ({column_type})")
                        columns_added += 1
                    except Exception as e:
                        print(f"❌ Erreur ajout colonne {column_name}: {str(e)}")
                else:
                    print(f"⏭️ Colonne existe déjà: {column_name}")
            
            # Valider les changements
            conn.commit()
            
            print(f"\n📊 Résumé de la mise à jour:")
            print(f"   - Colonnes ajoutées: {columns_added}")
            print(f"   - Total colonnes: {len(existing_columns) + columns_added}")
            
            # Vérifier la structure finale
            cursor.execute("DESCRIBE processed_articles")
            final_columns = cursor.fetchall()
            
            print(f"\n📋 Structure finale de la table processed_articles:")
            for col in final_columns:
                print(f"   - {col['Field']}: {col['Type']}")
            
            print(f"\n✅ Mise à jour du schéma terminée avec succès!")
            
    except Exception as e:
        print(f"❌ Erreur mise à jour schéma: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_database_schema() 