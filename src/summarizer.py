"""
TechWatchIT - Générateur de résumés IA
Création de résumés intelligents avec impact et actions recommandées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import re
from typing import Dict, List, Optional
import logging
from datetime import datetime

from config.config import Config

class ArticleSummarizer:
    """Générateur de résumés d'articles basé sur GPT-4o"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.openai_client = None
        
        # Initialiser OpenAI si la clé est disponible
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.logger.info("✅ Client OpenAI pour résumés initialisé")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur initialisation OpenAI: {str(e)}")
                self.logger.warning("⚠️ Résumés basiques uniquement")
                self.openai_client = None
        else:
            self.logger.warning("⚠️ Clé OpenAI manquante, résumés basiques uniquement")
    
    def summarize_article(self, article: Dict, classification: Dict = None) -> Dict:
        """
        Générer un résumé intelligent d'un article
        
        Args:
            article: Dictionnaire contenant title, description, content, link
            classification: Classification existante (optionnel)
            
        Returns:
            Dict avec summary, impact_analysis, action_required
        """
        try:
            # Tentative de résumé IA d'abord
            if self.openai_client:
                ai_summary = self._generate_ai_summary(article, classification)
                if ai_summary:
                    self.logger.info(f"🤖 Résumé IA généré pour: {article.get('title', 'Sans titre')[:50]}...")
                    return ai_summary
            
            # Fallback sur résumé basique
            basic_summary = self._generate_basic_summary(article, classification)
            self.logger.info(f"📝 Résumé basique généré pour: {article.get('title', 'Sans titre')[:50]}...")
            return basic_summary
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la génération du résumé: {str(e)}")
            return self._get_default_summary(article)
    
    def _generate_ai_summary(self, article: Dict, classification: Dict = None) -> Optional[Dict]:
        """Générer un résumé via GPT-4o"""
        try:
            # Préparer le contexte
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', '')[:3000]  # Limiter pour l'API
            link = article.get('link', '')
            
            # Informations de classification si disponibles
            tech_context = ""
            if classification:
                tech_context = f"""
                Technologie identifiée: {classification.get('technology', 'unknown')}
                Niveau de sévérité: {classification.get('severity_level', 'medium')}
                Score CVSS: {classification.get('cvss_score', 'N/A')}
                Alerte de sécurité: {'Oui' if classification.get('is_security_alert') else 'Non'}
                """
            
            # Prompt spécialisé pour les résumés IT
            prompt = f"""
            Tu es un expert en cybersécurité qui rédige des résumés exécutifs pour des équipes IT.
            
            Ton objectif: créer un résumé structuré, actionnable et en français de cet article de veille IT.
            
            ARTICLE À RÉSUMER:
            Titre: {title}
            Description: {description}
            Contenu: {content}
            URL: {link}
            
            CONTEXTE TECHNIQUE:
            {tech_context}
            
            INSTRUCTIONS:
            1. Rédige un résumé en français de maximum 6 sentences
            2. Sois précis, technique mais accessible
            3. Mets l'accent sur l'IMPACT et les ACTIONS à entreprendre
            4. Structure ta réponse EXACTEMENT comme ceci:
            
            RÉSUMÉ:
            [Résumé en 4-6 sentences maximum, en français]
            
            IMPACT:
            [Impact potentiel sur l'infrastructure IT en 2-3 sentences]
            
            ACTION:
            [Actions recommandées en 1-2 sentences précises]
            
            CRITÈRES IMPORTANTS:
            - Si c'est une vulnérabilité: précise la gravité et l'urgence
            - Si c'est un patch: indique la priorité d'installation
            - Si c'est un produit: explique l'intérêt pour la sécurité
            - Toujours proposer une action concrète et mesurable
            
            Rédige UNIQUEMENT le résumé structuré, sans préambule ni conclusion.
            """
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert en cybersécurité qui rédige des résumés techniques précis et actionnables pour des équipes IT."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2  # Cohérence et précision
            )
            
            # Parser la réponse structurée
            ai_response = response.choices[0].message.content.strip()
            return self._parse_ai_summary(ai_response, article)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération résumé IA: {str(e)}")
            return None
    
    def _parse_ai_summary(self, ai_response: str, article: Dict) -> Dict:
        """Parser la réponse structurée de l'IA"""
        
        try:
            # Nettoyer la réponse
            cleaned_response = ai_response.strip()
            
            # Extraire les sections avec regex
            summary_match = re.search(r'RÉSUMÉ:\s*\n?(.*?)(?=\n?IMPACT:|$)', cleaned_response, re.DOTALL | re.IGNORECASE)
            impact_match = re.search(r'IMPACT:\s*\n?(.*?)(?=\n?ACTION:|$)', cleaned_response, re.DOTALL | re.IGNORECASE)
            action_match = re.search(r'ACTION:\s*\n?(.*?)$', cleaned_response, re.DOTALL | re.IGNORECASE)
            
            # Extraire le contenu
            summary = summary_match.group(1).strip() if summary_match else ""
            impact = impact_match.group(1).strip() if impact_match else ""
            action = action_match.group(1).strip() if action_match else ""
            
            # Nettoyer les sauts de ligne excessifs
            summary = re.sub(r'\n+', ' ', summary).strip()
            impact = re.sub(r'\n+', ' ', impact).strip()
            action = re.sub(r'\n+', ' ', action).strip()
            
            # Validation et fallback
            if not summary:
                # Fallback si la structure n'est pas respectée
                lines = cleaned_response.split('\n')
                summary = ' '.join(line.strip() for line in lines if line.strip())[:600]
                impact = "Impact à évaluer selon votre environnement technique."
                action = "Analyser la pertinence pour votre infrastructure."
            
            return {
                'summary': summary[:600],  # Limiter la taille
                'impact_analysis': impact[:400],
                'action_required': action[:300]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur parsing résumé IA: {str(e)}")
            # Fallback sur le texte brut
            return {
                'summary': ai_response[:600],
                'impact_analysis': "Impact à évaluer manuellement.",
                'action_required': "Analyser cet article pour déterminer les actions."
            }
    
    def _generate_basic_summary(self, article: Dict, classification: Dict = None) -> Dict:
        """Générer un résumé basique sans IA"""
        
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        
        # Résumé basique basé sur le titre et la description
        summary_parts = []
        
        if title:
            summary_parts.append(f"Article: {title}")
        
        if description:
            # Prendre les premiers mots de la description
            desc_summary = ' '.join(description.split()[:50])
            if len(description.split()) > 50:
                desc_summary += "..."
            summary_parts.append(desc_summary)
        
        summary = ' - '.join(summary_parts) if summary_parts else "Article de veille IT sans description détaillée."
        
        # Impact basé sur la classification
        impact = "Impact à évaluer selon votre environnement."
        if classification:
            severity = classification.get('severity_level', 'medium')
            technology = classification.get('technology', 'unknown')
            
            if severity == 'critical':
                impact = f"Impact critique potentiel sur les systèmes {technology}. Évaluation urgente requise."
            elif severity == 'high':
                impact = f"Impact important possible sur les systèmes {technology}. Évaluation prioritaire."
            elif severity == 'medium':
                impact = f"Impact modéré possible sur les systèmes {technology}. Évaluation dans les prochains jours."
            else:
                impact = f"Impact faible sur les systèmes {technology}. Information à noter."
        
        # Action basée sur la classification
        action = "Analyser la pertinence pour votre infrastructure."
        if classification:
            if classification.get('is_security_alert'):
                action = "Vérifier l'exposition de vos systèmes et planifier les correctifs si nécessaire."
            elif classification.get('category') == 'patch':
                action = "Évaluer la nécessité d'appliquer les correctifs mentionnés."
            elif classification.get('category') == 'vulnerability':
                action = "Vérifier si vos systèmes sont vulnérables et prendre les mesures appropriées."
            else:
                action = "Prendre connaissance de l'information pour référence future."
        
        return {
            'summary': summary[:600],
            'impact_analysis': impact[:400],
            'action_required': action[:300]
        }
    
    def _get_default_summary(self, article: Dict) -> Dict:
        """Résumé par défaut en cas d'erreur"""
        title = article.get('title', 'Article sans titre')
        
        return {
            'summary': f"Article de veille IT: {title}. Résumé automatique non disponible.",
            'impact_analysis': "Impact à évaluer manuellement selon votre environnement.",
            'action_required': "Consulter l'article original pour plus de détails."
        }
    
    def bulk_summarize(self, articles_with_classification: List[tuple]) -> List[Dict]:
        """
        Générer des résumés pour plusieurs articles
        
        Args:
            articles_with_classification: Liste de tuples (article, classification)
            
        Returns:
            Liste des résumés générés
        """
        results = []
        
        for i, (article, classification) in enumerate(articles_with_classification, 1):
            self.logger.info(f"📋 Génération résumé {i}/{len(articles_with_classification)}: {article.get('title', 'Sans titre')[:50]}...")
            
            summary = self.summarize_article(article, classification)
            results.append({
                'article': article,
                'classification': classification,
                'summary': summary
            })
            
            # Pause pour éviter de surcharger l'API OpenAI
            if self.openai_client and i % 5 == 0:
                import time
                time.sleep(2)
        
        return results
    
    def generate_daily_digest(self, articles: List[Dict], days: int = 1) -> str:
        """
        Générer un digest quotidien des articles
        
        Args:
            articles: Liste des articles avec classifications et résumés
            days: Nombre de jours couverts
            
        Returns:
            Digest formaté en HTML ou texte
        """
        if not articles:
            return "Aucun nouvel article aujourd'hui."
        
        # Trier par sévérité
        critical_articles = [a for a in articles if a.get('classification', {}).get('severity_level') == 'critical']
        high_articles = [a for a in articles if a.get('classification', {}).get('severity_level') == 'high']
        medium_articles = [a for a in articles if a.get('classification', {}).get('severity_level') == 'medium']
        
        digest_parts = []
        digest_parts.append(f"📊 **TechWatchIT - Digest {datetime.now().strftime('%d/%m/%Y')}**")
        digest_parts.append(f"📈 Total: {len(articles)} articles")
        
        if critical_articles:
            digest_parts.append(f"\n🚨 **CRITIQUES ({len(critical_articles)})**")
            for article in critical_articles[:5]:  # Limiter à 5
                title = article.get('title', 'Sans titre')
                summary = article.get('summary', {}).get('summary', 'Pas de résumé')
                digest_parts.append(f"• {title}")
                digest_parts.append(f"  {summary[:200]}...")
        
        if high_articles:
            digest_parts.append(f"\n⚠️ **IMPORTANTES ({len(high_articles)})**")
            for article in high_articles[:10]:  # Limiter à 10
                title = article.get('title', 'Sans titre')
                tech = article.get('classification', {}).get('technology', 'unknown')
                digest_parts.append(f"• [{tech.upper()}] {title}")
        
        if medium_articles:
            digest_parts.append(f"\n📋 **MOYENNES ({len(medium_articles)})**")
            # Grouper par technologie
            tech_groups = {}
            for article in medium_articles:
                tech = article.get('classification', {}).get('technology', 'other')
                if tech not in tech_groups:
                    tech_groups[tech] = []
                tech_groups[tech].append(article)
            
            for tech, tech_articles in tech_groups.items():
                digest_parts.append(f"  {tech.upper()}: {len(tech_articles)} articles")
        
        digest_parts.append(f"\n🔗 Dashboard: http://localhost:8080")
        digest_parts.append(f"⚙️ TechWatchIT - Veille IT automatisée")
        
        return '\n'.join(digest_parts)

# Instance globale
summarizer = ArticleSummarizer() 