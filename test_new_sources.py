#!/usr/bin/env python3
"""
Script de test pour les nouvelles sources RSS
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fetch_feeds import FeedFetcher
from config.config import RSS_FEEDS

def test_new_sources():
    """Test des nouvelles sources RSS"""
    fetcher = FeedFetcher()
    
    # Test de quelques sources clés
    test_sources = [
        "bleeping_computer",
        "exploit_db", 
        "rapid7_blog",
        "cyware_alerts",
        "sans_isc"
    ]
    
    print("🔍 Test des nouvelles sources RSS:")
    print("=" * 50)
    
    total_articles = 0
    
    for source_id in test_sources:
        if source_id in RSS_FEEDS:
            print(f"\n📡 Test de {RSS_FEEDS[source_id]['name']}...")
            print(f"URL: {RSS_FEEDS[source_id]['url']}")
            
            try:
                articles = fetcher.fetch_rss_feed(RSS_FEEDS[source_id])
                print(f"✅ {len(articles)} articles récupérés")
                
                if articles:
                    print("📰 Exemples d'articles:")
                    for i, article in enumerate(articles[:3]):  # Afficher 3 premiers
                        print(f"   {i+1}. {article['title'][:80]}...")
                        print(f"      📅 {article['published_date']}")
                        print(f"      🏷️ {article['category']}")
                        print()
                
                total_articles += len(articles)
                
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        else:
            print(f"❌ Source {source_id} non trouvée")
    
    print(f"\n🎉 Total: {total_articles} articles récupérés")
    print(f"📊 Moyenne: {total_articles/len(test_sources):.1f} articles par source")

if __name__ == "__main__":
    test_new_sources() 