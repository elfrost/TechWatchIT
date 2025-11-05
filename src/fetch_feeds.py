"""
TechWatchIT - Collecteur de flux RSS
Récupère et parse les flux RSS des différentes sources de veille IT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse
import ssl
import urllib3

# Désactiver les avertissements SSL pour les tests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config.config import Config, RSS_FEEDS
from src.database import DatabaseManager

class FeedFetcher:
    """Classe principale pour la récupération des flux RSS"""
    
    def __init__(self):
        """Initialiser le récupérateur de flux"""
        self.db = DatabaseManager()
        self.logger = Config.setup_logging()
        
        # Configuration de session HTTP avec gestion SSL améliorée
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TechWatchIT/1.0 (RSS Feed Reader)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        })
        
        # Configuration SSL plus permissive pour éviter les erreurs de certificat
        self.session.verify = False
        
        # Configuration des timeouts
        self.session.timeout = (10, 30)  # Connexion, lecture
        
        # Désactiver les warnings SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def fetch_rss_feed(self, feed_config: Dict) -> List[Dict]:
        """
        Récupère et parse un flux RSS
        
        Args:
            feed_config: Configuration du flux RSS
            
        Returns:
            Liste des articles extraits
        """
        feed_name = feed_config['name']
        feed_url = feed_config['url']
        
        self.logger.info(f"Récupération du flux: {feed_name}")
        
        try:
            # Configuration pour feedparser afin d'ignorer SSL
            feedparser.USER_AGENT = 'TechWatchIT/1.0'
            
            # Tentative de récupération avec requests d'abord
            try:
                response = self.session.get(feed_url, timeout=15)  # Réduire le timeout
                response.raise_for_status()
                
                # Parser le contenu avec feedparser
                feed = feedparser.parse(response.content)
            except Exception as e:
                self.logger.warning(f"Erreur avec requests pour {feed_name}: {e}")
                # Fallback avec feedparser direct (avec timeout plus court)
                try:
                    # Essayer avec feedparser directement
                    feed = feedparser.parse(feed_url)
                except Exception as e2:
                    self.logger.error(f"Erreur fallback pour {feed_name}: {e2}")
                    return []
            
            if feed.bozo:
                self.logger.warning(f"Flux RSS mal formé pour {feed_name}: {feed.bozo_exception}")
            
            articles = []
            
            # Filtrer uniquement les articles des dernières 24 heures
            cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
            
            for entry in feed.entries:
                article = self._parse_entry(entry, feed_config)
                if article:
                    # Vérifier la date de l'article
                    article_date = article.get('published_date')
                    if article_date and article_date >= cutoff_date:
                        articles.append(article)
                    # Si pas de date, on inclut l'article par sécurité
                    elif not article_date:
                        articles.append(article)
            
            self.logger.info(f"[SUCCESS] {len(articles)} articles recuperes de {feed_name}")
            return articles
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[ERROR] Erreur reseau pour {feed_name}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur lors de la recuperation de {feed_name}: {e}")
            return []
    
    def _parse_entry(self, entry, feed_config: Dict) -> Optional[Dict]:
        """
        Parse une entrée RSS en article
        
        Args:
            entry: Entrée RSS
            feed_config: Configuration du flux
            
        Returns:
            Article parsé ou None
        """
        try:
            # Extraction des données de base
            title = getattr(entry, 'title', 'Titre non disponible')
            link = getattr(entry, 'link', '')
            description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
            
            # Gestion de la date de publication
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            if not published_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            if not published_date:
                published_date = datetime.now(timezone.utc)
            
            # Extraction du contenu complet si disponible
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
            elif hasattr(entry, 'summary'):
                content = entry.summary
            
            # GUID unique
            guid = getattr(entry, 'id', '') or getattr(entry, 'guid', '') or link
            
            # Tags/catégories
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            article = {
                'title': title,
                'link': link,
                'description': description,
                'published_date': published_date,
                'content': content,
                'guid': guid,
                'tags': ', '.join(tags),
                'feed_source': feed_config.get('technology', 'Unknown'),
                'category': feed_config.get('category', 'General')
            }
            
            return article
            
        except Exception as e:
            self.logger.error(f"Erreur lors du parsing d'une entrée: {e}")
            return None
    
    def save_articles(self, articles: List[Dict], feed_source: str):
        """
        Sauvegarde les articles dans la base de données
        
        Args:
            articles: Liste des articles
            feed_source: Source du flux
        """
        if not articles:
            return
            
        saved_count = 0
        
        for article in articles:
            try:
                # Vérifier si l'article existe déjà
                if not self.db.article_exists(article['link']):
                    self.db.save_raw_article(article)
                    saved_count += 1
                    
            except Exception as e:
                self.logger.error(f"Erreur lors de la sauvegarde: {e}")
                continue
        
        self.logger.info(f"[SAVE] {saved_count}/{len(articles)} articles sauvegardes pour {feed_source}")
    
    def fetch_all_feeds(self):
        """Récupérer tous les flux RSS configurés"""
        self.logger.info("[START] Debut de la recuperation de tous les flux RSS")
        
        total_articles = 0
        start_time = datetime.now()
        
        for feed_id, feed_config in RSS_FEEDS.items():
            feed_start_time = datetime.now()
            try:
                articles = self.fetch_rss_feed(feed_config)
                self.save_articles(articles, feed_id)
                
                # Calculer le temps d'exécution
                execution_time = (datetime.now() - feed_start_time).total_seconds()
                
                # Logger l'opération
                self.db.log_fetch_operation(
                    feed_source=feed_id,
                    status='success',
                    articles_fetched=len(articles),
                    execution_time=execution_time,
                    error_message=None
                )
                
                total_articles += len(articles)
                
            except Exception as e:
                execution_time = (datetime.now() - feed_start_time).total_seconds()
                error_msg = str(e)
                
                self.logger.error(f"[ERROR] Erreur pour {feed_id}: {error_msg}")
                
                # Logger l'erreur
                self.db.log_fetch_operation(
                    feed_source=feed_id,
                    status='error',
                    articles_fetched=0,
                    execution_time=execution_time,
                    error_message=error_msg
                )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"[COMPLETE] Collecte terminee: {total_articles} articles au total en {total_time:.2f}s")
        
        return {
            'total_articles': total_articles,
            'total_time': total_time,
            'feeds_processed': len(RSS_FEEDS)
        }

def main():
    """Point d'entrée principal"""
    fetcher = FeedFetcher()
    
    # Test avec 2 flux spécifiques (Fortinet et SentinelOne)
    print("🔍 Test de récupération des flux Fortinet et SentinelOne...")
    
    # Fortinet
    fortinet_articles = fetcher.fetch_rss_feed(RSS_FEEDS['fortinet'])
    fetcher.save_articles(fortinet_articles, 'fortinet')
    
    # SentinelOne
    sentinelone_articles = fetcher.fetch_rss_feed(RSS_FEEDS['sentinelone'])
    fetcher.save_articles(sentinelone_articles, 'sentinelone')
    
    print(f"[TEST] Test termine:")
    print(f"   - Fortinet: {len(fortinet_articles)} articles")
    print(f"   - SentinelOne: {len(sentinelone_articles)} articles")
    print(f"   - Base de données: {Config.DATABASE_PATH}")

if __name__ == "__main__":
    main() 