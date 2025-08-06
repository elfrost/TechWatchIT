"""
TechWatchIT - Classificateur IA
Classification automatique des articles via GPT-4o avec fallback par mots-clés
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import re
import json
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from config.config import Config, TECH_KEYWORDS

class ArticleClassifier:
    """Classificateur d'articles basé sur l'IA et mots-clés"""
    
    def __init__(self):
        self.logger = Config.setup_logging()
        self.openai_client = None
        
        # Initialiser OpenAI si la clé est disponible
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.logger.info("✅ Client OpenAI initialisé")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur initialisation OpenAI: {str(e)}")
                self.logger.warning("⚠️ Utilisation des mots-clés uniquement")
                self.openai_client = None
        else:
            self.logger.warning("⚠️ Clé OpenAI manquante, utilisation des mots-clés uniquement")
    
    def classify_article(self, article: Dict) -> Dict:
        """
        Classifier un article avec IA ou fallback mots-clés
        
        Args:
            article: Dictionnaire contenant title, description, content, link
            
        Returns:
            Dict avec category, technology, severity_level, severity_score, etc.
        """
        try:
            # Tentative de classification IA d'abord
            if self.openai_client:
                ai_result = self._classify_with_ai(article)
                if ai_result:
                    self.logger.info(f"🤖 Classification IA réussie: {ai_result.get('technology', 'unknown')}")
                    return ai_result
            
            # Fallback sur les mots-clés
            keyword_result = self._classify_with_keywords(article)
            self.logger.info(f"🔍 Classification par mots-clés: {keyword_result.get('technology', 'unknown')}")
            return keyword_result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la classification: {str(e)}")
            return self._get_default_classification()
    
    def _classify_with_ai(self, article: Dict) -> Optional[Dict]:
        """Classification via GPT-4o"""
        try:
            # Préparer le contenu pour l'IA
            content_to_analyze = f"""
            Titre: {article.get('title', '')}
            Description: {article.get('description', '')}
            Contenu: {article.get('content', '')[:2000]}  # Limiter pour l'API
            URL: {article.get('link', '')}
            """
            
            # Prompt spécialisé pour la veille IT
            prompt = """
            Tu es un expert en cybersécurité qui analyse des articles de veille IT. 
            
            Analyse cet article et fournis une classification JSON avec ces champs EXACTEMENT:
            {
                "technology": "fortinet|sentinelone|jumpcloud|vmware|rubrik|dell|microsoft|exploits|other",
                "category": "security|update|vulnerability|patch|product|news",
                "severity_level": "low|medium|high|critical",
                "severity_score": 1.0-10.0,
                "cvss_score": null ou score CVSS si mentionné,
                "is_security_alert": true/false,
                "impact_analysis": "Description courte de l'impact",
                "action_required": "Action recommandée en une phrase"
            }
            
            Critères de classification:
            - "critical": CVE critique, exploitation active, impact majeur
            - "high": Vulnérabilité importante, patch urgent requis
            - "medium": Mise à jour de sécurité standard
            - "low": Information générale, mise à jour fonctionnelle
            
            Technologies ciblées:
            - fortinet: Fortinet, FortiGate, FortiOS, FortiAnalyzer, FortiManager
            - sentinelone: SentinelOne, Sentinel One, S1, protection endpoint
            - jumpcloud: JumpCloud, Jump Cloud, service d'annuaire, LDAP
            - vmware: VMware, vCenter, vSphere, ESXi, vSAN, NSX
            - rubrik: Rubrik, sauvegarde, zero trust, protection données
            - dell: Dell, EMC, PowerEdge, iDRAC, OpenManage
            - microsoft: Microsoft, Windows, Office, Exchange, Azure, Active Directory
            - exploits: CVE, exploits, malware, ransomware, zero-day
            
            Article à analyser:
            """ + content_to_analyze + """
            
            Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
            """
            
            if not self.openai_client:
                return None
                
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert en cybersécurité qui analyse et classifie des articles de veille IT avec précision."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1  # Réponses cohérentes
            )
            
            # Parser la réponse JSON
            ai_response = response.choices[0].message.content
            if ai_response:
                ai_response = ai_response.strip()
            else:
                return None
            
            # Nettoyer la réponse (enlever les ```json``` si présents)
            if ai_response.startswith('```'):
                ai_response = re.sub(r'^```(?:json)?\n', '', ai_response)
                ai_response = re.sub(r'\n```$', '', ai_response)
            
            classification = json.loads(ai_response)
            
            # Validation et normalisation
            return self._validate_ai_classification(classification, article)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Erreur parsing JSON IA: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Erreur OpenAI: {str(e)}")
            return None
    
    def _validate_ai_classification(self, classification: Dict, article: Dict) -> Dict:
        """Valider et normaliser la classification IA"""
        
        # Valeurs par défaut
        defaults = {
            'technology': 'other',
            'category': 'news',
            'severity_level': 'medium',
            'severity_score': 5.0,
            'cvss_score': None,
            'is_security_alert': False,
            'impact_analysis': '',
            'action_required': ''
        }
        
        # Normaliser les valeurs
        valid_technologies = ['fortinet', 'fortigate', 'sentinelone', 'jumpcloud', 'vmware', 'rubrik', 'dell', 'microsoft', 'exploits', 'other']
        valid_categories = ['security', 'update', 'vulnerability', 'patch', 'product', 'news']
        valid_severities = ['low', 'medium', 'high', 'critical']
        
        result = defaults.copy()
        
        # Technology avec normalisation
        ai_tech = classification.get('technology', '').lower()
        
        # Normalisation des technologies similaires
        tech_mapping = {
            'fortigate': 'fortinet',
            'fortios': 'fortinet',
            'fortianalyzer': 'fortinet',
            'fortimanager': 'fortinet',
            'sentinel one': 'sentinelone',
            's1': 'sentinelone',
            'jump cloud': 'jumpcloud',
            'vcenter': 'vmware',
            'vsphere': 'vmware',
            'esxi': 'vmware',
            'windows': 'microsoft',
            'office': 'microsoft',
            'azure': 'microsoft',
            'exchange': 'microsoft'
        }
        
        # Appliquer la normalisation
        normalized_tech = tech_mapping.get(ai_tech, ai_tech)
        
        if normalized_tech in valid_technologies:
            result['technology'] = normalized_tech
        elif ai_tech in valid_technologies:
            result['technology'] = ai_tech
        
        # Category
        if classification.get('category') in valid_categories:
            result['category'] = classification['category']
        
        # Severity level
        if classification.get('severity_level') in valid_severities:
            result['severity_level'] = classification['severity_level']
        
        # Severity score
        try:
            score = float(classification.get('severity_score', 5.0))
            result['severity_score'] = max(1.0, min(10.0, score))
        except:
            result['severity_score'] = 5.0
        
        # CVSS score
        try:
            if classification.get('cvss_score'):
                cvss = float(classification['cvss_score'])
                result['cvss_score'] = max(0.0, min(10.0, cvss))
        except:
            pass
        
        # Security alert
        result['is_security_alert'] = bool(classification.get('is_security_alert', False))
        
        # Textes
        result['impact_analysis'] = str(classification.get('impact_analysis', ''))[:500]
        result['action_required'] = str(classification.get('action_required', ''))[:300]
        
        # Auto-détection d'alerte de sécurité basée sur les mots-clés critiques
        critical_keywords = ['cve', 'exploit', 'vulnerability', 'patch', 'critical', 'urgent', 'security']
        content_lower = (article.get('title', '') + ' ' + article.get('description', '')).lower()
        
        if any(keyword in content_lower for keyword in critical_keywords):
            result['is_security_alert'] = True
            if result['severity_level'] in ['low', 'medium']:
                result['severity_level'] = 'high'
                result['severity_score'] = max(result['severity_score'], 7.0)
        
        return result
    
    def _classify_with_keywords(self, article: Dict) -> Dict:
        """Classification par mots-clés (fallback)"""
        
        # Texte à analyser (titre + description + contenu)
        text_to_analyze = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}".lower()
        
        # Classification par technologie
        technology = 'other'
        max_matches = 0
        
        for tech, keywords in TECH_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in text_to_analyze)
            if matches > max_matches:
                max_matches = matches
                technology = tech
        
        # Classification par sévérité basée sur les mots-clés
        severity_score = 5.0
        severity_level = 'medium'
        is_security_alert = False
        
        # Mots-clés critiques
        if any(word in text_to_analyze for word in ['critical', 'urgent', 'exploit', 'zero-day', 'ransomware']):
            severity_level = 'critical'
            severity_score = 9.0
            is_security_alert = True
        elif any(word in text_to_analyze for word in ['high', 'vulnerability', 'cve', 'patch']):
            severity_level = 'high'
            severity_score = 7.0
            is_security_alert = True
        elif any(word in text_to_analyze for word in ['security', 'update', 'fix']):
            severity_level = 'medium'
            severity_score = 5.0
            is_security_alert = True
        elif any(word in text_to_analyze for word in ['info', 'announcement', 'release']):
            severity_level = 'low'
            severity_score = 3.0
        
        # Détection CVSS
        cvss_match = re.search(r'cvss[:\s]*(\d+\.?\d*)', text_to_analyze)
        cvss_score = None
        if cvss_match:
            try:
                cvss_score = float(cvss_match.group(1))
                if cvss_score >= 9.0:
                    severity_level = 'critical'
                    severity_score = cvss_score
                    is_security_alert = True
                elif cvss_score >= 7.0:
                    severity_level = 'high'
                    severity_score = cvss_score
                    is_security_alert = True
            except:
                pass
        
        # Catégorie basée sur le contenu
        category = 'news'
        if any(word in text_to_analyze for word in ['vulnerability', 'cve', 'exploit']):
            category = 'vulnerability'
        elif any(word in text_to_analyze for word in ['patch', 'fix', 'update']):
            category = 'patch'
        elif any(word in text_to_analyze for word in ['security', 'alert']):
            category = 'security'
        elif any(word in text_to_analyze for word in ['release', 'product']):
            category = 'product'
        
        # Action recommandée basique
        action_required = ""
        if severity_level == 'critical':
            action_required = "Action immédiate requise - Évaluer l'impact et appliquer les correctifs"
        elif severity_level == 'high':
            action_required = "Planifier l'application des correctifs de sécurité"
        elif severity_level == 'medium':
            action_required = "Vérifier la pertinence pour votre environnement"
        else:
            action_required = "Information à noter pour référence future"
        
        return {
            'technology': technology,
            'category': category,
            'severity_level': severity_level,
            'severity_score': severity_score,
            'cvss_score': cvss_score,
            'is_security_alert': is_security_alert,
            'impact_analysis': f"Article {technology} classé {severity_level} - {max_matches} mots-clés détectés",
            'action_required': action_required
        }
    
    def _get_default_classification(self) -> Dict:
        """Classification par défaut en cas d'erreur"""
        return {
            'technology': 'other',
            'category': 'news',
            'severity_level': 'medium',
            'severity_score': 5.0,
            'cvss_score': None,
            'is_security_alert': False,
            'impact_analysis': 'Classification par défaut - Vérification manuelle recommandée',
            'action_required': 'Analyser manuellement cet article'
        }
    
    def bulk_classify(self, articles: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Classifier plusieurs articles en lot"""
        results = []
        
        for i, article in enumerate(articles, 1):
            self.logger.info(f"📊 Classification article {i}/{len(articles)}: {article.get('title', 'Sans titre')[:50]}...")
            
            classification = self.classify_article(article)
            results.append((article, classification))
            
            # Pause pour éviter de surcharger l'API OpenAI
            if self.openai_client and i % 10 == 0:
                import time
                time.sleep(1)
        
        return results

# Instance globale
classifier = ArticleClassifier() 