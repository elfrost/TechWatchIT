"""
TechWatchIT - Gestionnaire de base de données MySQL
Interface avec la base MySQL de WAMP pour TechWatchIT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from config.config import Config

class DatabaseManager:
    """Gestionnaire de base de données MySQL pour TechWatchIT"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.connection_params = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        # Paramètres sans base de données pour création initiale
        self.connection_params_no_db = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    @contextmanager
    def get_connection(self, use_database=True):
        """Context manager pour les connexions MySQL"""
        connection = None
        try:
            params = self.connection_params if use_database else self.connection_params_no_db
            connection = pymysql.connect(**params)
            yield connection
        finally:
            if connection:
                connection.close()
    
    def create_database_if_not_exists(self):
        """Créer la base de données si elle n'existe pas"""
        try:
            with self.get_connection(use_database=False) as conn:
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit()
                self.logger.info(f"✅ Base de données '{Config.MYSQL_DATABASE}' créée ou vérifiée")
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la création de la base: {str(e)}")
            raise
    
    def init_database(self):
        """Initialiser la base de données MySQL avec toutes les tables"""
        try:
            # D'abord créer la base de données si nécessaire
            self.create_database_if_not_exists()
            
            # Puis créer les tables
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Table des articles bruts
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    feed_source VARCHAR(50) NOT NULL,
                    title TEXT NOT NULL,
                    link VARCHAR(500) NOT NULL UNIQUE,
                    description TEXT,
                    published_date DATETIME,
                    content LONGTEXT,
                    guid VARCHAR(255),
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_feed_source (feed_source),
                    INDEX idx_published_date (published_date),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Table des articles traités avec classification IA
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    raw_article_id INT NOT NULL UNIQUE,
                    category VARCHAR(50),
                    technology VARCHAR(50),
                    severity_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
                    severity_score DECIMAL(3,1) DEFAULT 5.0,
                    cvss_score DECIMAL(3,1),
                    summary TEXT,
                    impact_analysis TEXT,
                    action_required TEXT,
                    is_security_alert BOOLEAN DEFAULT FALSE,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (raw_article_id) REFERENCES raw_articles(id) ON DELETE CASCADE,
                    INDEX idx_category (category),
                    INDEX idx_technology (technology),
                    INDEX idx_severity_level (severity_level),
                    INDEX idx_cvss_score (cvss_score),
                    INDEX idx_security_alert (is_security_alert)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Table de log des récupérations
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS fetch_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    feed_source VARCHAR(50) NOT NULL,
                    status ENUM('success', 'error', 'partial') NOT NULL,
                    articles_count INT DEFAULT 0,
                    new_articles_count INT DEFAULT 0,
                    error_message TEXT,
                    execution_time DECIMAL(5,2),
                    fetch_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_feed_source (feed_source),
                    INDEX idx_status (status),
                    INDEX idx_fetch_date (fetch_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Table des alertes envoyées
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    article_id INT NOT NULL,
                    alert_type ENUM('critical', 'daily_digest') NOT NULL,
                    recipients TEXT NOT NULL,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('sent', 'failed') DEFAULT 'sent',
                    error_message TEXT,
                    FOREIGN KEY (article_id) REFERENCES processed_articles(id) ON DELETE CASCADE,
                    INDEX idx_alert_type (alert_type),
                    INDEX idx_sent_at (sent_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Table des statistiques quotidiennes
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    stat_date DATE NOT NULL UNIQUE,
                    total_articles INT DEFAULT 0,
                    new_articles INT DEFAULT 0,
                    critical_alerts INT DEFAULT 0,
                    high_severity INT DEFAULT 0,
                    medium_severity INT DEFAULT 0,
                    low_severity INT DEFAULT 0,
                    fortigate_count INT DEFAULT 0,
                    sentinelone_count INT DEFAULT 0,
                    jumpcloud_count INT DEFAULT 0,
                    vmware_count INT DEFAULT 0,
                    rubrik_count INT DEFAULT 0,
                    dell_count INT DEFAULT 0,
                    exploits_count INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_stat_date (stat_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                conn.commit()
                self.logger.info("✅ Base de données MySQL initialisée avec succès")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation de la base: {str(e)}")
            raise
    
    def save_raw_article(self, article: Dict) -> Optional[int]:
        """Sauvegarder un article brut et retourner son ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT IGNORE INTO raw_articles 
                (feed_source, title, link, description, published_date, content, guid, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    article.get('feed_source', 'Unknown'),
                    article['title'][:500],  # Limiter la taille du titre
                    article['link'],
                    article.get('description', '')[:1000],
                    article.get('published_date'),
                    article.get('content', ''),
                    article.get('guid', '')[:255],
                    article.get('tags', '')[:500]
                ))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return cursor.lastrowid
                else:
                    # Article déjà existant, récupérer son ID
                    cursor.execute('SELECT id FROM raw_articles WHERE link = %s', (article['link'],))
                    result = cursor.fetchone()
                    return result['id'] if result else None
                    
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde article: {str(e)}")
            return None
    
    def article_exists(self, link: str) -> bool:
        """Vérifier si un article existe déjà"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM raw_articles WHERE link = %s', (link,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Erreur vérification article: {str(e)}")
            return False
    
    def save_processed_article(self, raw_article_id: int, processed_data: Dict) -> bool:
        """Sauvegarder un article traité par l'IA"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO processed_articles 
                (raw_article_id, category, technology, severity_level, severity_score, 
                 cvss_score, summary, impact_analysis, action_required, is_security_alert)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                technology = VALUES(technology),
                severity_level = VALUES(severity_level),
                severity_score = VALUES(severity_score),
                cvss_score = VALUES(cvss_score),
                summary = VALUES(summary),
                impact_analysis = VALUES(impact_analysis),
                action_required = VALUES(action_required),
                is_security_alert = VALUES(is_security_alert),
                processed_at = CURRENT_TIMESTAMP
                ''', (
                    raw_article_id,
                    processed_data.get('category'),
                    processed_data.get('technology'),
                    processed_data.get('severity_level', 'medium'),
                    processed_data.get('severity_score', 5.0),
                    processed_data.get('cvss_score'),
                    processed_data.get('summary', ''),
                    processed_data.get('impact_analysis', ''),
                    processed_data.get('action_required', ''),
                    processed_data.get('is_security_alert', False)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde article traité: {str(e)}")
            return False
    
    def get_articles(self, filters: Dict = None) -> List[Dict]:
        """Récupérer les articles avec filtres optionnels"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = '''
                SELECT 
                    r.id, r.feed_source, r.title, r.link, r.description, 
                    r.published_date, r.tags, r.created_at,
                    p.category, p.technology, p.severity_level, p.severity_score,
                    p.cvss_score, p.summary, p.impact_analysis, p.action_required,
                    p.is_security_alert, p.processed_at
                FROM raw_articles r
                LEFT JOIN processed_articles p ON r.id = p.raw_article_id
                WHERE 1=1
                '''
                
                params = []
                
                if filters:
                    if filters.get('category'):
                        base_query += ' AND p.category = %s'
                        params.append(filters['category'])
                    
                    if filters.get('technology'):
                        base_query += ' AND p.technology = %s'
                        params.append(filters['technology'])
                    
                    if filters.get('severity'):
                        base_query += ' AND p.severity_level = %s'
                        params.append(filters['severity'])
                    
                    if filters.get('security_alerts_only'):
                        base_query += ' AND p.is_security_alert = TRUE'
                    
                    if filters.get('days_back'):
                        base_query += ' AND r.published_date >= %s'
                        date_limit = datetime.now() - timedelta(days=int(filters['days_back']))
                        params.append(date_limit)
                
                base_query += ' ORDER BY r.published_date DESC LIMIT %s'
                params.append(filters.get('limit', 100))
                
                cursor.execute(base_query, params)
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.error(f"Erreur récupération articles: {str(e)}")
            return []
    
    def get_dashboard_stats(self, days: int = 30) -> Dict:
        """Récupérer les statistiques pour le dashboard"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                date_limit = datetime.now() - timedelta(days=days)
                
                # Statistiques générales
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN p.is_security_alert = TRUE THEN 1 END) as security_alerts,
                    COUNT(CASE WHEN p.severity_level = 'critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN p.severity_level = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN p.severity_level = 'medium' THEN 1 END) as medium,
                    COUNT(CASE WHEN p.severity_level = 'low' THEN 1 END) as low
                FROM raw_articles r
                LEFT JOIN processed_articles p ON r.id = p.raw_article_id
                WHERE r.published_date >= %s
                ''', (date_limit,))
                
                general_stats = cursor.fetchone()
                
                # Statistiques par technologie
                cursor.execute('''
                SELECT 
                    p.technology,
                    COUNT(*) as count,
                    COUNT(CASE WHEN p.is_security_alert = TRUE THEN 1 END) as alerts
                FROM raw_articles r
                JOIN processed_articles p ON r.id = p.raw_article_id
                WHERE r.published_date >= %s AND p.technology IS NOT NULL
                GROUP BY p.technology
                ORDER BY count DESC
                ''', (date_limit,))
                
                tech_stats = cursor.fetchall()
                
                # Évolution quotidienne
                cursor.execute('''
                SELECT 
                    DATE(r.published_date) as date,
                    COUNT(*) as articles,
                    COUNT(CASE WHEN p.is_security_alert = TRUE THEN 1 END) as alerts
                FROM raw_articles r
                LEFT JOIN processed_articles p ON r.id = p.raw_article_id
                WHERE r.published_date >= %s
                GROUP BY DATE(r.published_date)
                ORDER BY date DESC
                LIMIT 30
                ''', (date_limit,))
                
                daily_stats = cursor.fetchall()
                
                return {
                    'general': general_stats,
                    'by_technology': tech_stats,
                    'daily_evolution': daily_stats
                }
                
        except Exception as e:
            self.logger.error(f"Erreur statistiques dashboard: {str(e)}")
            return {}
    
    def log_fetch_operation(self, feed_source: str, status: str, 
                           articles_fetched: int = 0, execution_time: float = 0,
                           error_message: str = None):
        """Logger une opération de récupération"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO fetch_log 
                (feed_source, status, articles_count, new_articles_count, error_message, execution_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (feed_source, status, articles_fetched, articles_fetched, error_message, execution_time))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Erreur log fetch: {str(e)}")

# Instance globale
db = DatabaseManager() 