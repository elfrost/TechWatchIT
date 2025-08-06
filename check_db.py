#!/usr/bin/env python3

import sqlite3
from pathlib import Path

db_path = Path('data/database.db')
if db_path.exists():
    conn = sqlite3.connect(db_path)
    
    print('=== TABLES EXISTANTES ===')
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for table in tables:
        print(f'- {table[0]}')
    
    print('\n=== STRUCTURE DES TABLES ===')
    for table in tables:
        table_name = table[0]
        print(f'\n📋 Table: {table_name}')
        
        # Structure
        schema = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        for col in schema:
            print(f'   - {col[1]} ({col[2]})')
        
        # Nombre d'enregistrements
        count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
        print(f'   📊 {count} enregistrements')
        
        # Exemples de catégories si colonne category existe
        try:
            categories = conn.execute(f'SELECT category, COUNT(*) FROM {table_name} GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5').fetchall()
            if categories:
                print(f'   📂 Catégories principales:')
                for cat, cnt in categories:
                    print(f'      - {cat}: {cnt}')
        except:
            pass
    
    conn.close()
else:
    print('❌ Base de données non trouvée') 