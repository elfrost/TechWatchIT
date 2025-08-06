"""
TechWatchIT - Gestionnaire d'alertes critiques
Script pour traiter et envoyer les alertes de sécurité critiques en temps réel
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from config.config import Config
from src.database import db

class CriticalAlertHandler:
    """Gestionnaire d'alertes critiques"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        
        # Vérifier la configuration SMTP
        if not all([Config.SMTP_USERNAME, Config.SMTP_PASSWORD, Config.ALERT_RECIPIENTS]):
            self.logger.warning("⚠️ Configuration SMTP incomplète - alertes désactivées")
            self.smtp_enabled = False
        else:
            self.smtp_enabled = True
    
    def get_critical_articles(self, hours_back: int = 1) -> List[Dict]:
        """
        Récupérer les articles critiques récents non encore notifiés
        
        Args:
            hours_back: Nombre d'heures à remonter
            
        Returns:
            Liste des articles critiques
        """
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Articles critiques des dernières heures non encore notifiés
                cursor.execute('''
                SELECT 
                    r.id, r.feed_source, r.title, r.link, r.description, 
                    r.published_date, r.created_at,
                    p.technology, p.severity_level, p.severity_score,
                    p.cvss_score, p.summary, p.impact_analysis, p.action_required,
                    p.is_security_alert
                FROM raw_articles r
                JOIN processed_articles p ON r.id = p.raw_article_id
                LEFT JOIN alert_notifications an ON p.id = an.article_id AND an.alert_type = 'critical'
                WHERE 
                    p.severity_level = 'critical' 
                    AND p.is_security_alert = TRUE
                    AND r.created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    AND an.id IS NULL
                ORDER BY p.cvss_score DESC, p.severity_score DESC, r.published_date DESC
                ''', (hours_back,))
                
                articles = cursor.fetchall()
                
                self.logger.info(f"🔍 {len(articles)} articles critiques trouvés")
                return articles
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération articles critiques: {str(e)}")
            return []
    
    def send_critical_alert(self, article: Dict) -> bool:
        """Envoyer une alerte critique par email"""
        
        if not self.smtp_enabled:
            self.logger.warning("⚠️ SMTP désactivé - alerte critique non envoyée")
            return False
        
        try:
            recipients = [r.strip() for r in Config.ALERT_RECIPIENTS if r.strip()]
            
            if not recipients:
                self.logger.warning("⚠️ Aucun destinataire configuré pour les alertes")
                return False
            
            # Préparer l'email
            title = article.get('title', 'Alerte critique')[:100]
            technology = article.get('technology', 'UNKNOWN').upper()
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 CRITIQUE {technology} - {title}"
            msg['From'] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USERNAME}>"
            msg['To'] = ', '.join(recipients)
            msg['X-Priority'] = '1'  # Haute priorité
            
            # Contenu texte simple
            text_content = f"""
🚨 ALERTE CRITIQUE SÉCURITÉ - TechWatchIT

Technologie: {technology}
Titre: {title}
CVSS: {article.get('cvss_score', 'N/A')}
Sévérité: {article.get('severity_score', 'N/A')}/10

Résumé: {article.get('summary', 'Pas de résumé')}

Impact: {article.get('impact_analysis', 'Impact non analysé')}

Action recommandée: {article.get('action_required', 'Actions à déterminer')}

Lien: {article.get('link', '#')}

⚠️ Cette alerte nécessite une attention immédiate de l'équipe sécurité.

---
TechWatchIT - Système d'alerte automatique
{datetime.now().strftime('%d/%m/%Y à %H:%M')}
            """
            
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Envoyer l'email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                
                success_count = 0
                for recipient in recipients:
                    try:
                        server.send_message(msg, to_addrs=[recipient])
                        self.logger.info(f"🚨 Alerte critique envoyée à {recipient}")
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"❌ Erreur envoi alerte à {recipient}: {str(e)}")
                
                return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi alerte critique: {str(e)}")
            return False
    
    def mark_alert_sent(self, article_id: int, alert_type: str = 'critical') -> bool:
        """Marquer une alerte comme envoyée"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                recipients_str = ', '.join(Config.ALERT_RECIPIENTS)
                
                cursor.execute('''
                INSERT INTO alert_notifications 
                (article_id, alert_type, recipients, status)
                VALUES (%s, %s, %s, 'sent')
                ''', (article_id, alert_type, recipients_str))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erreur marquage alerte: {str(e)}")
            return False
    
    def process_critical_alerts(self) -> int:
        """
        Traiter toutes les alertes critiques en attente
        
        Returns:
            Nombre d'alertes envoyées
        """
        try:
            self.logger.info("🔥 Recherche d'alertes critiques...")
            
            # Récupérer les articles critiques non notifiés
            critical_articles = self.get_critical_articles(hours_back=2)
            
            if not critical_articles:
                self.logger.info("✅ Aucune alerte critique en attente")
                return 0
            
            sent_count = 0
            
            for article in critical_articles:
                try:
                    self.logger.info(f"🚨 Traitement alerte critique: {article.get('title', 'Sans titre')[:50]}...")
                    
                    # Envoyer l'alerte
                    if self.send_critical_alert(article):
                        # Marquer comme envoyée
                        self.mark_alert_sent(article['id'], 'critical')
                        sent_count += 1
                        self.logger.info(f"✅ Alerte critique envoyée pour l'article {article['id']}")
                    else:
                        self.logger.error(f"❌ Échec envoi alerte pour l'article {article['id']}")
                
                except Exception as e:
                    self.logger.error(f"❌ Erreur traitement alerte {article.get('id')}: {str(e)}")
                    continue
            
            if sent_count > 0:
                self.logger.info(f"🚨 {sent_count} alertes critiques envoyées avec succès")
            
            return sent_count
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement alertes critiques: {str(e)}")
            return 0

def main():
    """Point d'entrée principal"""
    try:
        alert_handler = CriticalAlertHandler()
        
        # Traiter les alertes critiques
        sent_count = alert_handler.process_critical_alerts()
        
        print(f"✅ Traitement des alertes terminé: {sent_count} alertes envoyées")
        
        sys.exit(0)
            
    except Exception as e:
        print(f"❌ Erreur fatale gestionnaire d'alertes: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 