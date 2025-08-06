"""
TechWatchIT - Générateur de résumés avancés et articles de blog IA
Analyses détaillées, format blog, et insights approfondis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import re
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json

from config.config import Config

class AdvancedSummarizer:
    """Générateur de résumés avancés et articles de blog basé sur GPT-4o"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.openai_client = None
        
        # Initialiser OpenAI
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.logger.info("✅ Client OpenAI avancé initialisé")
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation OpenAI avancé: {str(e)}")
                self.openai_client = None
        else:
            self.logger.error("❌ Clé OpenAI manquante pour résumés avancés")
    
    def generate_detailed_analysis(self, article: Dict, classification: Dict = None) -> Dict:
        """
        Générer une analyse détaillée complète avec format blog
        
        Args:
            article: Article à analyser
            classification: Classification existante
            
        Returns:
            Dict avec analyse complète, format blog, insights techniques
        """
        if not self.openai_client:
            return self._get_fallback_analysis(article)
        
        try:
            # Générer l'analyse détaillée
            detailed_analysis = self._generate_comprehensive_analysis(article, classification)
            
            # Générer le format blog
            blog_format = self._generate_blog_article(article, classification, detailed_analysis)
            
            # Générer les insights techniques
            technical_insights = self._generate_technical_insights(article, classification)
            
            # Générer un résumé exécutif
            executive_summary = self._generate_executive_summary(article, classification)
            
            result = {
                'detailed_summary': detailed_analysis.get('summary', ''),
                'technical_analysis': detailed_analysis.get('technical_analysis', ''),
                'business_impact': detailed_analysis.get('business_impact', ''),
                'action_plan': detailed_analysis.get('action_plan', ''),
                'risk_assessment': detailed_analysis.get('risk_assessment', ''),
                'blog_article': blog_format,
                'technical_insights': technical_insights,
                'executive_summary': executive_summary,
                'recommendations': detailed_analysis.get('recommendations', []),
                'timeline': detailed_analysis.get('timeline', ''),
                'related_topics': detailed_analysis.get('related_topics', [])
            }
            
            self.logger.info(f"🎯 Analyse détaillée générée pour: {article.get('title', '')[:50]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse détaillée: {str(e)}")
            return self._get_fallback_analysis(article)
    
    def _generate_comprehensive_analysis(self, article: Dict, classification: Dict = None) -> Dict:
        """Générer une analyse technique complète"""
        
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')[:4000]  # Plus de contenu pour l'analyse
        link = article.get('link', '')
        
        # Contexte de classification
        tech_context = ""
        if classification:
            tech_context = f"""
            CONTEXTE TECHNIQUE:
            - Technologie: {classification.get('technology', 'unknown')}
            - Catégorie: {classification.get('category', 'general')}
            - Sévérité: {classification.get('severity_level', 'medium')} ({classification.get('severity_score', 'N/A')}/10)
            - Score CVSS: {classification.get('cvss_score', 'N/A')}
            - Alerte sécurité: {'Oui' if classification.get('is_security_alert') else 'Non'}
            """
        
        prompt = f"""
        Tu es un expert senior en cybersécurité et architecte IT avec 15+ ans d'expérience.
        Tu dois analyser cet article de veille technologique et produire une analyse complète et approfondie.
        
        ARTICLE À ANALYSER:
        Titre: {title}
        Description: {description}
        Contenu: {content}
        Source: {link}
        
        {tech_context}
        
        MISSION: Produis une analyse technique complète, détaillée et actionnable en français.
        
        Structure ta réponse EXACTEMENT comme ceci:
        
        RÉSUMÉ DÉTAILLÉ:
        [Résumé complet en 8-12 phrases, technique mais accessible, expliquant le contexte, les détails techniques, et les implications]
        
        ANALYSE TECHNIQUE:
        [Analyse technique approfondie: comment ça fonctionne, quels systèmes sont affectés, mécanismes techniques, vecteurs d'attaque, etc. 6-8 phrases]
        
        IMPACT BUSINESS:
        [Impact sur l'entreprise: coûts, risques opérationnels, conformité, réputation, continuité d'activité. 4-6 sentences]
        
        PLAN D'ACTION:
        [Plan d'action détaillé étape par étape avec priorités et délais. Format liste numérotée]
        
        ÉVALUATION RISQUES:
        [Évaluation des risques: probabilité, impact, exposition, facteurs aggravants. 4-5 sentences]
        
        RECOMMANDATIONS:
        [Liste de 5-7 recommandations spécifiques et actionnables, format liste à puces]
        
        TIMELINE:
        [Timeline recommandée pour la mise en œuvre: Immédiat (0-24h), Court terme (1-7j), Moyen terme (1-4 semaines)]
        
        SUJETS CONNEXES:
        [3-5 sujets ou technologies connexes à surveiller]
        
        CRITÈRES QUALITÉ:
        - Sois précis et technique sans être obscur
        - Donne des exemples concrets quand possible
        - Quantifie les risques et impacts
        - Propose des solutions pratiques et réalisables
        - Adapte le niveau de détail à l'importance du sujet
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert senior en cybersécurité et architecte IT. Tu produis des analyses techniques détaillées, précises et actionnables."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1  # Très cohérent et factuel
            )
            
            ai_response = response.choices[0].message.content.strip()
            return self._parse_comprehensive_analysis(ai_response)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse complète: {str(e)}")
            return {}
    
    def _generate_blog_article(self, article: Dict, classification: Dict, analysis: Dict) -> str:
        """Générer un article de blog complet"""
        
        title = article.get('title', '')
        content = article.get('content', '')[:3000]
        
        prompt = f"""
        Tu es un rédacteur technique spécialisé en cybersécurité qui écrit pour un blog IT professionnel.
        
        MISSION: Transforme cette analyse technique en article de blog engageant, informatif et professionnel.
        
        ARTICLE SOURCE:
        Titre: {title}
        Contenu: {content}
        
        ANALYSE TECHNIQUE DISPONIBLE:
        {analysis.get('summary', '')}
        {analysis.get('technical_analysis', '')}
        
        INSTRUCTIONS POUR L'ARTICLE DE BLOG:
        
        1. Crée un titre accrocheur et informatif
        2. Structure l'article avec des sections claires
        3. Utilise un ton professionnel mais accessible
        4. Inclus des exemples pratiques
        5. Termine par des conseils actionnables
        
        FORMAT REQUIS:
        
        # [Titre accrocheur]
        
        ## 🚨 En Bref
        [Résumé exécutif en 2-3 phrases]
        
        ## 📋 Contexte et Détails
        [Explication détaillée du sujet, contexte, enjeux]
        
        ## 🔧 Aspects Techniques
        [Détails techniques accessibles, comment ça fonctionne]
        
        ## 💼 Impact sur Votre Organisation
        [Implications business, risques, opportunités]
        
        ## ✅ Actions Recommandées
        [Liste d'actions concrètes avec priorités]
        
        ## 🔮 Perspective et Tendances
        [Vision future, évolution du sujet, veille à maintenir]
        
        ---
        *Article généré par TechWatchIT - Système de veille automatisée*
        
        STYLE:
        - Professionnel mais engageant
        - Phrases courtes et claires
        - Utilise des emojis pour structurer
        - Évite le jargon excessif
        - Focus sur l'actionnable
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un rédacteur technique expert qui transforme des analyses complexes en articles de blog clairs et engageants."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3  # Un peu plus créatif pour le style
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération blog: {str(e)}")
            return self._get_fallback_blog(article)
    
    def _generate_technical_insights(self, article: Dict, classification: Dict) -> Dict:
        """Générer des insights techniques spécialisés"""
        
        title = article.get('title', '')
        content = article.get('content', '')[:2000]
        
        prompt = f"""
        En tant qu'expert technique, génère des insights spécialisés sur cet article.
        
        ARTICLE: {title}
        CONTENU: {content}
        
        Produis des insights techniques sous cette structure JSON:
        
        {{
            "key_technologies": ["tech1", "tech2", "tech3"],
            "attack_vectors": ["vecteur1", "vecteur2"],
            "affected_systems": ["système1", "système2"],
            "mitigation_strategies": ["stratégie1", "stratégie2"],
            "detection_methods": ["méthode1", "méthode2"],
            "compliance_impact": ["norme1", "norme2"],
            "similar_incidents": ["incident1", "incident2"],
            "vendor_response": "réponse du vendeur",
            "community_reaction": "réaction de la communauté"
        }}
        
        Réponds UNIQUEMENT avec le JSON valide, sans explication.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu génères des insights techniques structurés au format JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            json_response = response.choices[0].message.content.strip()
            return json.loads(json_response)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur insights techniques: {str(e)}")
            return {}
    
    def _generate_executive_summary(self, article: Dict, classification: Dict) -> str:
        """Générer un résumé exécutif pour la direction"""
        
        title = article.get('title', '')
        
        prompt = f"""
        Rédige un résumé exécutif de 3-4 phrases pour la direction sur: {title}
        
        Focus sur:
        - Impact business
        - Risques financiers/opérationnels  
        - Actions requises
        - Timeline critique
        
        Style: Direct, factuel, orienté décision.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu rédiges des résumés exécutifs pour dirigeants d'entreprise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur résumé exécutif: {str(e)}")
            return "Résumé exécutif non disponible."
    
    def _parse_comprehensive_analysis(self, ai_response: str) -> Dict:
        """Parser l'analyse complète structurée"""
        
        try:
            sections = {
                'summary': self._extract_section(ai_response, 'RÉSUMÉ DÉTAILLÉ'),
                'technical_analysis': self._extract_section(ai_response, 'ANALYSE TECHNIQUE'),
                'business_impact': self._extract_section(ai_response, 'IMPACT BUSINESS'),
                'action_plan': self._extract_section(ai_response, 'PLAN D\'ACTION'),
                'risk_assessment': self._extract_section(ai_response, 'ÉVALUATION RISQUES'),
                'recommendations': self._extract_list_section(ai_response, 'RECOMMANDATIONS'),
                'timeline': self._extract_section(ai_response, 'TIMELINE'),
                'related_topics': self._extract_list_section(ai_response, 'SUJETS CONNEXES')
            }
            
            return sections
            
        except Exception as e:
            self.logger.error(f"❌ Erreur parsing analyse: {str(e)}")
            return {}
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extraire une section spécifique du texte"""
        pattern = rf'{section_name}:\s*\n?(.*?)(?=\n?[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s]+:|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_list_section(self, text: str, section_name: str) -> List[str]:
        """Extraire une section sous forme de liste"""
        section_text = self._extract_section(text, section_name)
        if not section_text:
            return []
        
        # Extraire les éléments de liste (•, -, 1., etc.)
        items = re.findall(r'(?:•|\-|\d+\.)\s*([^\n•\-\d]+)', section_text)
        return [item.strip() for item in items if item.strip()]
    
    def _get_fallback_analysis(self, article: Dict) -> Dict:
        """Analyse de fallback si l'IA n'est pas disponible"""
        title = article.get('title', 'Article sans titre')
        
        return {
            'detailed_summary': f"Analyse de: {title}. Résumé détaillé non disponible sans IA.",
            'technical_analysis': "Analyse technique non disponible.",
            'business_impact': "Impact business à évaluer manuellement.",
            'action_plan': "Plan d'action à définir selon votre contexte.",
            'risk_assessment': "Évaluation des risques à effectuer.",
            'blog_article': self._get_fallback_blog(article),
            'technical_insights': {},
            'executive_summary': f"Article technique détecté: {title}. Analyse manuelle requise.",
            'recommendations': ["Analyser manuellement l'article", "Consulter les sources officielles"],
            'timeline': "Timeline à définir selon la criticité.",
            'related_topics': []
        }
    
    def _get_fallback_blog(self, article: Dict) -> str:
        """Article de blog de fallback"""
        title = article.get('title', 'Article Technique')
        
        return f"""# {title}

## 🚨 En Bref
Article technique détecté nécessitant une analyse manuelle.

## 📋 Informations Disponibles
- **Titre**: {title}
- **Source**: {article.get('link', 'Non disponible')}
- **Date**: {article.get('published_date', 'Non disponible')}

## ⚠️ Action Requise
Analyse manuelle recommandée pour cet article.

---
*Article généré par TechWatchIT - Analyse IA non disponible*
""" 