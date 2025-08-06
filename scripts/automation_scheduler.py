#!/usr/bin/env python3
"""
TechWatchIT - Système d'automatisation et de planification
Exécution automatique des tâches de veille, analyse et génération de rapports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
import subprocess

from src.fetch_feeds import FeedFetcher
from src.classifier import ArticleClassifier
from src.summarizer import ArticleSummarizer
from src.advanced_summarizer import AdvancedSummarizer
from src.database import DatabaseManager
from config.config import Config
import pymysql

class TechWatchITAutomation:
    """Système d'automatisation complète de TechWatchIT"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.db = DatabaseManager()
        self.fetcher = FeedFetcher()
        self.classifier = ArticleClassifier()
        self.summarizer = ArticleSummarizer()
        self.advanced_summarizer = AdvancedSummarizer()
        self.running = False
        
        self.logger.info("🤖 Système d'automatisation TechWatchIT initialisé")
    
    def setup_schedules(self):
        """Configurer les tâches planifiées"""
        
        # Récupération des flux RSS - Toutes les 30 minutes
        schedule.every(30).minutes.do(self.fetch_feeds_job)
        
        # Traitement IA des nouveaux articles - Toutes les heures
        schedule.every().hour.do(self.process_new_articles_job)
        
        # Génération d'analyses détaillées - Toutes les 2 heures
        schedule.every(2).hours.do(self.generate_detailed_analyses_job)
        
        # Rapport quotidien - Tous les jours à 8h00
        schedule.every().day.at("08:00").do(self.daily_report_job)
        
        # Nettoyage de la base - Tous les dimanches à 02:00
        schedule.every().sunday.at("02:00").do(self.database_maintenance_job)
        
        # Sauvegarde - Tous les jours à 23:00
        schedule.every().day.at("23:00").do(self.backup_job)
        
        self.logger.info("📅 Planification automatique configurée:")
        self.logger.info("   - Récupération RSS: Toutes les 30 minutes")
        self.logger.info("   - Traitement IA: Toutes les heures")
        self.logger.info("   - Analyses détaillées: Toutes les 2 heures")
        self.logger.info("   - Rapport quotidien: 8h00")
        self.logger.info("   - Maintenance: Dimanche 2h00")
        self.logger.info("   - Sauvegarde: 23h00")
    
    def fetch_feeds_job(self):
        """Tâche de récupération des flux RSS"""
        try:
            self.logger.info("🔄 Début récupération automatique des flux RSS")
            feed_results = self.fetcher.fetch_all_feeds()
            self.logger.info(f"✅ Récupération terminée: {feed_results} articles traités")
            
            # Notifier si articles critiques détectés
            if feed_results.get('total_articles', 0) > 0:
                self._check_critical_articles()
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération automatique: {str(e)}")
    
    def process_new_articles_job(self):
        """Tâche de traitement IA des nouveaux articles"""
        try:
            self.logger.info("🤖 Début traitement IA automatique")
            
            # Récupérer les articles non traités
            with self.db.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute('''
                SELECT r.* FROM raw_articles r
                LEFT JOIN processed_articles p ON r.id = p.raw_article_id
                WHERE p.id IS NULL
                ORDER BY r.created_at DESC
                LIMIT 50
                ''')
                raw_articles = cursor.fetchall()
            
            if not raw_articles:
                self.logger.info("📝 Aucun nouvel article à traiter")
                return
            
            processed_count = 0
            critical_count = 0
            
            for article in raw_articles:
                try:
                    # Classification
                    classification = self.classifier.classify_article(article)
                    
                    # Résumé standard
                    summary = self.summarizer.summarize_article(article, classification)
                    
                    # Fusionner les données
                    processed_data = {**classification, **summary}
                    
                    # Sauvegarder
                    if self.db.save_processed_article(article['id'], processed_data):
                        processed_count += 1
                        
                        # Compter les articles critiques
                        if classification.get('severity_level') == 'critical':
                            critical_count += 1
                
                except Exception as e:
                    self.logger.error(f"❌ Erreur traitement article {article['id']}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Traitement IA terminé: {processed_count} articles traités")
            
            if critical_count > 0:
                self.logger.warning(f"⚠️ {critical_count} articles critiques détectés - Analyse urgente recommandée")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement IA automatique: {str(e)}")
    
    def generate_detailed_analyses_job(self):
        """Tâche de génération d'analyses détaillées pour les articles critiques"""
        try:
            self.logger.info("🎯 Début génération analyses détaillées automatique")
            
            # Récupérer les articles critiques sans analyse détaillée
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT pa.*, ra.title, ra.content, ra.description, ra.link, ra.published_date
                FROM processed_articles pa
                INNER JOIN raw_articles ra ON pa.raw_article_id = ra.id
                WHERE pa.severity_level = 'critical' 
                AND pa.processed_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND (pa.detailed_analysis IS NULL OR pa.detailed_analysis = '')
                ORDER BY pa.processed_at DESC
                LIMIT 10
                ''')
                critical_articles = cursor.fetchall()
            
            if not critical_articles:
                self.logger.info("📝 Aucun article critique nécessitant une analyse détaillée")
                return
            
            analyses_generated = 0
            
            for article_data in critical_articles:
                try:
                    # Préparer les données
                    article = {
                        'title': article_data['title'],
                        'content': article_data['content'],
                        'description': article_data['description'] or '',
                        'link': article_data['link'],
                        'published_date': article_data['published_date']
                    }
                    
                    classification = {
                        'category': article_data['category'],
                        'technology': article_data['technology'],
                        'severity_level': article_data['severity_level'],
                        'severity_score': article_data['severity_score'],
                        'cvss_score': article_data['cvss_score'],
                        'is_security_alert': article_data['is_security_alert']
                    }
                    
                    # Générer l'analyse détaillée
                    detailed_analysis = self.advanced_summarizer.generate_detailed_analysis(article, classification)
                    
                    # Sauvegarder l'analyse détaillée
                    if detailed_analysis and detailed_analysis.get('detailed_summary'):
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                            UPDATE processed_articles 
                            SET detailed_analysis = %s,
                                blog_article = %s,
                                executive_summary = %s,
                                technical_insights = %s
                            WHERE id = %s
                            ''', (
                                detailed_analysis.get('detailed_summary', ''),
                                detailed_analysis.get('blog_article', ''),
                                detailed_analysis.get('executive_summary', ''),
                                str(detailed_analysis.get('technical_insights', {})),
                                article_data['id']
                            ))
                            conn.commit()
                        
                        analyses_generated += 1
                        self.logger.info(f"📊 Analyse détaillée générée pour: {article['title'][:50]}...")
                
                except Exception as e:
                    self.logger.error(f"❌ Erreur analyse détaillée article {article_data['id']}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Analyses détaillées générées: {analyses_generated}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération analyses détaillées: {str(e)}")
    
    def daily_report_job(self):
        """Tâche de génération du rapport quotidien"""
        try:
            self.logger.info("📊 Génération du rapport quotidien automatique")
            
            # Générer le rapport quotidien
            report_content = self._generate_daily_report()
            
            # Sauvegarder le rapport
            report_filename = f"rapport_quotidien_{datetime.now().strftime('%Y%m%d')}.txt"
            report_path = os.path.join("logs", report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"✅ Rapport quotidien sauvegardé: {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération rapport quotidien: {str(e)}")
    
    def database_maintenance_job(self):
        """Tâche de maintenance de la base de données"""
        try:
            self.logger.info("🧹 Début maintenance automatique de la base")
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Supprimer les anciens articles (> 90 jours)
                cursor.execute('''
                DELETE FROM raw_articles 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
                ''')
                deleted_raw = cursor.rowcount
                
                # Optimiser les tables
                cursor.execute("OPTIMIZE TABLE raw_articles")
                cursor.execute("OPTIMIZE TABLE processed_articles")
                
                conn.commit()
            
            self.logger.info(f"✅ Maintenance terminée: {deleted_raw} anciens articles supprimés")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur maintenance base: {str(e)}")
    
    def backup_job(self):
        """Tâche de sauvegarde automatique"""
        try:
            self.logger.info("💾 Début sauvegarde automatique")
            
            backup_filename = f"techwatchit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            backup_path = os.path.join("logs", backup_filename)
            
            # Commande mysqldump
            cmd = [
                "mysqldump",
                "-h", "localhost",
                "-u", "root",
                "--single-transaction",
                "--routines",
                "--triggers",
                "techwatchit"
            ]
            
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            
            self.logger.info(f"✅ Sauvegarde terminée: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde: {str(e)}")
    
    def _check_critical_articles(self):
        """Vérifier s'il y a de nouveaux articles critiques"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT COUNT(*) as count
                FROM processed_articles 
                WHERE severity_level = 'critical' 
                AND processed_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ''')
                result = cursor.fetchone()
                
                if result and result['count'] > 0:
                    self.logger.warning(f"🚨 ALERTE: {result['count']} nouveaux articles critiques détectés")
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification articles critiques: {str(e)}")
    
    def _generate_daily_report(self) -> str:
        """Générer le contenu du rapport quotidien"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Statistiques du jour
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_articles,
                    SUM(CASE WHEN severity_level = 'critical' THEN 1 ELSE 0 END) as critical_count,
                    SUM(CASE WHEN severity_level = 'high' THEN 1 ELSE 0 END) as high_count,
                    SUM(CASE WHEN is_security_alert = 1 THEN 1 ELSE 0 END) as security_alerts
                FROM processed_articles 
                WHERE DATE(processed_at) = CURDATE()
                ''')
                stats = cursor.fetchone()
                
                # Articles critiques du jour
                cursor.execute('''
                SELECT pa.technology, ra.title, pa.severity_score
                FROM processed_articles pa
                INNER JOIN raw_articles ra ON pa.raw_article_id = ra.id
                WHERE pa.severity_level = 'critical' 
                AND DATE(pa.processed_at) = CURDATE()
                ORDER BY pa.severity_score DESC
                LIMIT 5
                ''')
                critical_articles = cursor.fetchall()
                
                # Générer le rapport
                report = f"""
RAPPORT QUOTIDIEN TECHWATCHIT
========================================
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

STATISTIQUES DU JOUR
--------------------
📊 Total articles traités: {stats['total_articles'] if stats else 0}
🚨 Articles critiques: {stats['critical_count'] if stats else 0}
⚠️ Articles haute sévérité: {stats['high_count'] if stats else 0}
🛡️ Alertes sécurité: {stats['security_alerts'] if stats else 0}

ARTICLES CRITIQUES DU JOUR
---------------------------
"""
                
                if critical_articles:
                    for i, article in enumerate(critical_articles, 1):
                        report += f"{i}. [{article['technology'].upper()}] {article['title']} (Score: {article['severity_score']}/10)\n"
                else:
                    report += "Aucun article critique aujourd'hui.\n"
                
                report += f"""
========================================
Rapport généré automatiquement par TechWatchIT
Système de veille technologique automatisé
"""
                
                return report
                
        except Exception as e:
            self.logger.error(f"❌ Erreur génération rapport: {str(e)}")
            return f"Erreur génération rapport: {str(e)}"
    
    def start_automation(self):
        """Démarrer le système d'automatisation"""
        self.running = True
        self.setup_schedules()
        
        self.logger.info("🚀 Système d'automatisation TechWatchIT démarré")
        self.logger.info("⏰ Planificateur en cours d'exécution...")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Arrêt du système d'automatisation demandé")
            self.stop_automation()
    
    def stop_automation(self):
        """Arrêter le système d'automatisation"""
        self.running = False
        schedule.clear()
        self.logger.info("🛑 Système d'automatisation TechWatchIT arrêté")
    
    def run_manual_task(self, task_name: str):
        """Exécuter manuellement une tâche spécifique"""
        tasks = {
            'fetch': self.fetch_feeds_job,
            'process': self.process_new_articles_job,
            'analyze': self.generate_detailed_analyses_job,
            'report': self.daily_report_job,
            'maintenance': self.database_maintenance_job,
            'backup': self.backup_job
        }
        
        if task_name in tasks:
            self.logger.info(f"🔧 Exécution manuelle de la tâche: {task_name}")
            tasks[task_name]()
        else:
            self.logger.error(f"❌ Tâche inconnue: {task_name}")
            self.logger.info(f"📋 Tâches disponibles: {', '.join(tasks.keys())}")

def main():
    """Point d'entrée principal"""
    automation = TechWatchITAutomation()
    
    if len(sys.argv) > 1:
        # Mode manuel
        task = sys.argv[1]
        automation.run_manual_task(task)
    else:
        # Mode automatique
        try:
            automation.start_automation()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")

if __name__ == "__main__":
    main() 