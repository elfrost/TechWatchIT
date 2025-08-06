"""
TechWatchIT - Digest quotidien
Script pour envoyer un digest quotidien par email
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

from config.config import Config
from src.database import db
from src.summarizer import summarizer

class DailyDigest:
    """Générateur et envoyeur de digest quotidien"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        
        # Vérifier la configuration SMTP
        if not all([Config.SMTP_USERNAME, Config.SMTP_PASSWORD, Config.ALERT_RECIPIENTS]):
            self.logger.error("❌ Configuration SMTP incomplète")
            raise ValueError("Configuration email manquante")
    
    def get_daily_articles(self, days_back: int = 1) -> List[Dict]:
        """Récupérer les articles des derniers jours"""
        try:
            filters = {
                'days_back': days_back,
                'limit': 500
            }
            
            articles = db.get_articles(filters)
            self.logger.info(f"📊 {len(articles)} articles récupérés pour le digest")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération articles: {str(e)}")
            return []
    
    def generate_html_digest(self, articles: List[Dict]) -> str:
        """Générer le digest au format HTML"""
        
        if not articles:
            return self._generate_empty_digest()
        
        # Trier les articles par sévérité et technologie
        critical_articles = [a for a in articles if a.get('severity_level') == 'critical']
        high_articles = [a for a in articles if a.get('severity_level') == 'high']
        medium_articles = [a for a in articles if a.get('severity_level') == 'medium']
        low_articles = [a for a in articles if a.get('severity_level') == 'low']
        
        # Statistiques par technologie
        tech_stats = {}
        for article in articles:
            tech = article.get('technology', 'other')
            if tech not in tech_stats:
                tech_stats[tech] = {'total': 0, 'alerts': 0}
            tech_stats[tech]['total'] += 1
            if article.get('is_security_alert'):
                tech_stats[tech]['alerts'] += 1
        
        today = datetime.now().strftime('%d/%m/%Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>TechWatchIT - Digest {today}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #333; }}
                .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid #eee; }}
                .critical {{ border-left: 4px solid #dc3545; }}
                .high {{ border-left: 4px solid #fd7e14; }}
                .medium {{ border-left: 4px solid #ffc107; }}
                .low {{ border-left: 4px solid #28a745; }}
                .article {{ margin: 10px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                .article-title {{ font-weight: bold; color: #333; margin-bottom: 5px; }}
                .article-meta {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
                .article-summary {{ color: #555; line-height: 1.4; }}
                .tech-badge {{ display: inline-block; padding: 2px 6px; background-color: #007bff; color: white; border-radius: 3px; font-size: 10px; text-transform: uppercase; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                .no-articles {{ text-align: center; padding: 40px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 TechWatchIT - Digest Quotidien</h1>
                    <p>📅 {today} • {len(articles)} articles analysés</p>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{len(critical_articles)}</div>
                        <div class="stat-label">Critiques</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{len(high_articles)}</div>
                        <div class="stat-label">Importantes</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{len(medium_articles)}</div>
                        <div class="stat-label">Moyennes</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{len([a for a in articles if a.get('is_security_alert')])}</div>
                        <div class="stat-label">Alertes sécu</div>
                    </div>
                </div>
        """
        
        # Section articles critiques
        if critical_articles:
            html_content += f"""
                <div class="section">
                    <div class="section-title critical">🚨 Articles Critiques ({len(critical_articles)})</div>
            """
            for article in critical_articles[:10]:  # Limiter à 10
                html_content += self._format_article_html(article, 'critical')
            html_content += "</div>"
        
        # Section articles importants
        if high_articles:
            html_content += f"""
                <div class="section">
                    <div class="section-title high">⚠️ Articles Importants ({len(high_articles)})</div>
            """
            for article in high_articles[:15]:  # Limiter à 15
                html_content += self._format_article_html(article, 'high')
            html_content += "</div>"
        
        # Section résumé par technologie
        if tech_stats:
            html_content += f"""
                <div class="section">
                    <div class="section-title">📊 Résumé par Technologie</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
            """
            for tech, stats in sorted(tech_stats.items(), key=lambda x: x[1]['total'], reverse=True):
                tech_display = tech.title() if tech != 'other' else 'Autres'
                html_content += f"""
                    <div class="article">
                        <span class="tech-badge">{tech_display}</span>
                        <div style="margin-top: 5px;">
                            <strong>{stats['total']}</strong> articles
                            {f"• <span style='color: #dc3545;'>{stats['alerts']} alertes</span>" if stats['alerts'] > 0 else ""}
                        </div>
                    </div>
                """
            html_content += "</div></div>"
        
        # Footer
        html_content += f"""
                <div class="footer">
                    <p>🔗 <a href="http://localhost:5000/dashboard">Consulter le dashboard complet</a></p>
                    <p>⚙️ TechWatchIT - Plateforme de veille IT automatisée</p>
                    <p>📧 Vous recevez cet email car vous êtes inscrit aux alertes TechWatchIT</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_article_html(self, article: Dict, severity_class: str) -> str:
        """Formater un article en HTML"""
        title = article.get('title', 'Sans titre')
        tech = article.get('technology', 'other')
        summary = article.get('summary', 'Pas de résumé disponible')
        link = article.get('link', '#')
        published_date = article.get('published_date', datetime.now())
        
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            except:
                published_date = datetime.now()
        
        date_str = published_date.strftime('%d/%m %H:%M')
        
        return f"""
        <div class="article {severity_class}">
            <div class="article-title">
                <span class="tech-badge">{tech.upper()}</span>
                <a href="{link}" style="color: #333; text-decoration: none;" target="_blank">{title}</a>
            </div>
            <div class="article-meta">📅 {date_str}</div>
            <div class="article-summary">{summary[:200]}{'...' if len(summary) > 200 else ''}</div>
        </div>
        """
    
    def _generate_empty_digest(self) -> str:
        """Générer un digest vide"""
        today = datetime.now().strftime('%d/%m/%Y')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>TechWatchIT - Digest {today}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 TechWatchIT</h1>
                <h2>Digest du {today}</h2>
                <div class="no-articles">
                    <p>😴 Aucun nouvel article aujourd'hui</p>
                    <p>La veille technologique continue...</p>
                </div>
                <hr>
                <p style="color: #666; font-size: 12px;">⚙️ TechWatchIT - Plateforme de veille IT automatisée</p>
            </div>
        </body>
        </html>
        """
    
    def send_digest(self, html_content: str, recipients: List[str] = None) -> bool:
        """Envoyer le digest par email"""
        try:
            if not recipients:
                recipients = [r.strip() for r in Config.ALERT_RECIPIENTS if r.strip()]
            
            if not recipients:
                self.logger.warning("⚠️ Aucun destinataire configuré")
                return False
            
            # Préparer l'email
            today = datetime.now().strftime('%d/%m/%Y')
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"TechWatchIT - Digest {today}"
            msg['From'] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USERNAME}>"
            msg['To'] = ', '.join(recipients)
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envoyer l'email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                
                for recipient in recipients:
                    try:
                        server.send_message(msg, to_addrs=[recipient])
                        self.logger.info(f"✅ Digest envoyé à {recipient}")
                    except Exception as e:
                        self.logger.error(f"❌ Erreur envoi à {recipient}: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi digest: {str(e)}")
            return False
    
    def run_daily_digest(self) -> bool:
        """Exécuter le digest quotidien complet"""
        try:
            self.logger.info("📧 Début génération digest quotidien...")
            
            # Récupérer les articles du jour
            articles = self.get_daily_articles(days_back=1)
            
            # Générer le HTML
            html_digest = self.generate_html_digest(articles)
            
            # Envoyer l'email
            success = self.send_digest(html_digest)
            
            if success:
                self.logger.info(f"✅ Digest quotidien envoyé avec succès ({len(articles)} articles)")
            else:
                self.logger.error("❌ Échec envoi digest quotidien")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erreur digest quotidien: {str(e)}")
            return False

def main():
    """Point d'entrée principal"""
    try:
        digest = DailyDigest()
        success = digest.run_daily_digest()
        
        if success:
            print("✅ Digest quotidien envoyé avec succès")
            sys.exit(0)
        else:
            print("❌ Échec envoi digest quotidien")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erreur fatale: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 