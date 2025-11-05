"""
TechWatchIT - Wrapper Pydantic pour Classifier Legacy
Solution hybride: Validation Pydantic + Code existant fonctionnel
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict

from src.models import (
    ArticleClassification,
    TechnologyType,
    SeverityLevel,
    CategoryType
)
from src.classifier import ArticleClassifier

logger = logging.getLogger(__name__)


class PydanticClassifier:
    """
    Wrapper qui utilise le classifier existant mais retourne
    des objets Pydantic validés

    Avantages:
    - Type safety immédiat
    - Validation automatique
    - Compatible avec code existant
    - Pas besoin de pydantic-ai pour l'instant
    """

    def __init__(self):
        self.legacy_classifier = ArticleClassifier()
        logger.info("PydanticClassifier initialisé (wrapper legacy)")

    def classify_article(self, article: Dict) -> ArticleClassification:
        """
        Classifier un article avec validation Pydantic

        Args:
            article: Dict contenant title, description, content, link

        Returns:
            ArticleClassification validé par Pydantic
        """
        try:
            # Utiliser le classifier legacy
            legacy_result = self.legacy_classifier.classify_article(article)

            # Convertir en modèle Pydantic avec validation
            classification = ArticleClassification(
                technology=self._map_technology(legacy_result.get('technology', 'other')),
                category=self._map_category(legacy_result.get('category', 'news')),
                severity_level=SeverityLevel(legacy_result.get('severity_level', 'medium')),
                severity_score=float(legacy_result.get('severity_score', 5.0)),
                cvss_score=legacy_result.get('cvss_score'),
                is_security_alert=bool(legacy_result.get('is_security_alert', False)),
                impact_analysis=str(legacy_result.get('impact_analysis', ''))[:500],
                action_required=str(legacy_result.get('action_required', ''))[:300],
                cve_references=self._extract_cve_references(article, legacy_result),
                confidence_score=0.85  # Score moyen pour classification legacy
            )

            logger.info(
                f"Classification Pydantic: {classification.technology.value} "
                f"({classification.severity_level.value})"
            )

            return classification

        except Exception as e:
            logger.error(f"Erreur classification Pydantic: {e}")
            # Retourner classification par défaut valide
            return self._get_default_classification()

    def _map_technology(self, tech_str: str) -> TechnologyType:
        """Mapper string technology vers TechnologyType enum"""
        tech_map = {
            'fortinet': TechnologyType.FORTINET,
            'fortigate': TechnologyType.FORTINET,
            'sentinelone': TechnologyType.SENTINELONE,
            'jumpcloud': TechnologyType.JUMPCLOUD,
            'vmware': TechnologyType.VMWARE,
            'rubrik': TechnologyType.RUBRIK,
            'dell': TechnologyType.DELL,
            'microsoft': TechnologyType.MICROSOFT,
            'exploits': TechnologyType.EXPLOITS,
            'other': TechnologyType.OTHER
        }
        return tech_map.get(tech_str.lower(), TechnologyType.OTHER)

    def _map_category(self, cat_str: str) -> CategoryType:
        """Mapper string category vers CategoryType enum"""
        cat_map = {
            'security': CategoryType.SECURITY,
            'update': CategoryType.UPDATE,
            'vulnerability': CategoryType.VULNERABILITY,
            'patch': CategoryType.PATCH,
            'product': CategoryType.PRODUCT,
            'news': CategoryType.NEWS
        }
        return cat_map.get(cat_str.lower(), CategoryType.NEWS)

    def _extract_cve_references(self, article: Dict, legacy_result: Dict) -> list:
        """Extraire et valider les CVE"""
        import re

        cves = []

        # Chercher CVE dans le texte
        text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
        cve_pattern = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)

        found_cves = cve_pattern.findall(text)
        cves.extend([cve.upper() for cve in found_cves])

        # Ajouter ceux du legacy result si présents
        if 'cve_references' in legacy_result:
            cves.extend(legacy_result['cve_references'])

        # Dédupliquer
        return list(set(cves))[:10]  # Max 10 CVE

    def _get_default_classification(self) -> ArticleClassification:
        """Classification par défaut en cas d'erreur"""
        return ArticleClassification(
            technology=TechnologyType.OTHER,
            category=CategoryType.NEWS,
            severity_level=SeverityLevel.MEDIUM,
            severity_score=5.0,
            is_security_alert=False,
            impact_analysis="Classification par défaut - Vérification manuelle recommandée",
            action_required="Analyser manuellement cet article",
            confidence_score=0.5
        )

    def classify_batch(self, articles: list) -> list[ArticleClassification]:
        """Classifier plusieurs articles"""
        results = []
        for article in articles:
            try:
                classification = self.classify_article(article)
                results.append(classification)
            except Exception as e:
                logger.error(f"Erreur batch classification: {e}")
                results.append(self._get_default_classification())
        return results


# Instance globale
pydantic_classifier = PydanticClassifier()


def classify_article_pydantic(article: Dict) -> ArticleClassification:
    """
    Fonction helper pour classification avec validation Pydantic
    Compatible avec l'API existante mais retourne objet Pydantic
    """
    return pydantic_classifier.classify_article(article)


# Export
__all__ = [
    'PydanticClassifier',
    'pydantic_classifier',
    'classify_article_pydantic'
]


if __name__ == "__main__":
    # Test
    test_article = {
        'title': 'Critical Fortinet FortiOS Vulnerability CVE-2024-12345',
        'description': 'A critical vulnerability affecting FortiOS allows remote code execution',
        'content': 'CVE-2024-12345 discovered in FortiOS versions 7.0.x...',
        'link': 'https://example.com/fortinet-vuln',
        'feed_source': 'fortinet'
    }

    print("Test PydanticClassifier...")
    result = classify_article_pydantic(test_article)

    print(f"\nResultat:")
    print(f"  Technology: {result.technology.value}")
    print(f"  Category: {result.category.value}")
    print(f"  Severity: {result.severity_level.value} ({result.severity_score}/10)")
    print(f"  CVE: {result.cve_references}")
    print(f"  Security Alert: {result.is_security_alert}")
    print(f"  Confidence: {result.confidence_score}")

    # Test JSON
    print(f"\nJSON serialization:")
    print(result.model_dump_json(indent=2))
