"""
TechWatchIT - Agent de Classification PydanticAI
Classification d'articles avec validation structurée et enrichissement RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from typing import Optional
import logging
from datetime import datetime

from src.models import (
    ArticleClassification,
    TechnologyType,
    SeverityLevel,
    CategoryType
)
from config.config import Config

# Logger
logger = logging.getLogger(__name__)


class ClassificationDependencies:
    """Dépendances pour l'agent de classification"""

    def __init__(self, archon_client=None):
        self.archon_client = archon_client
        self.rag_source_id = os.getenv("ARCHON_RAG_CVE_SOURCE_ID", None)

    async def search_cve_context(self, query: str) -> str:
        """Rechercher du contexte CVE dans la base RAG"""
        if not self.archon_client or not self.rag_source_id:
            return "RAG non configuré"

        try:
            results = self.archon_client.rag_search_knowledge_base(
                query=query,
                source_id=self.rag_source_id,
                match_count=3
            )

            if results.get('success') and results.get('results'):
                context_parts = []
                for result in results['results'][:3]:
                    context_parts.append(result.get('content', ''))
                return "\n---\n".join(context_parts)

            return "Aucun contexte RAG trouvé"
        except Exception as e:
            logger.warning(f"Erreur recherche RAG: {e}")
            return "Erreur RAG"


# Créer l'agent de classification
classification_agent = Agent(
    model=OpenAIModel('gpt-4o'),
    result_type=ArticleClassification,
    system_prompt="""
    Tu es un expert en cybersécurité spécialisé dans l'analyse de veille technologique IT.

    Ton rôle est de classifier des articles de sécurité avec une PRÉCISION MAXIMALE.

    **Technologies surveillées:**
    - fortinet: Fortinet, FortiGate, FortiOS, FortiAnalyzer, FortiManager, FortiWeb
    - sentinelone: SentinelOne, Sentinel One, S1, protection endpoint EDR
    - jumpcloud: JumpCloud, Jump Cloud, directory service, LDAP, IAM
    - vmware: VMware, vCenter, vSphere, ESXi, vSAN, NSX, Horizon
    - rubrik: Rubrik, backup, zero trust data security
    - dell: Dell, EMC, PowerEdge, iDRAC, OpenManage
    - microsoft: Microsoft, Windows, Office, Exchange, Azure, Active Directory, M365
    - exploits: CVE génériques, malware, ransomware, zero-day sans technologie spécifique
    - other: Si aucune technologie ci-dessus ne correspond

    **Niveaux de sévérité:**
    - CRITICAL (9-10): CVE critique, exploitation active, impact majeur immédiat
    - HIGH (7-8.9): Vulnérabilité importante, patch urgent recommandé
    - MEDIUM (4-6.9): Mise à jour de sécurité standard, impact modéré
    - LOW (1-3.9): Information, mise à jour fonctionnelle, impact faible

    **Catégories:**
    - vulnerability: Article décrivant une faille de sécurité (CVE)
    - patch: Correctif ou mise à jour de sécurité
    - security: Alerte de sécurité générale, advisory
    - update: Mise à jour produit (non-sécurité)
    - product: Annonce de nouveau produit/fonctionnalité
    - news: Information générale

    **Instructions:**
    1. Lis attentivement l'article fourni
    2. Utilise le tool search_cve_context si tu identifies un CVE ou une technologie spécifique
    3. Extrais tous les CVE mentionnés (format CVE-YYYY-NNNNN)
    4. Évalue la sévérité en fonction de l'impact réel
    5. Fournis une analyse d'impact concrète pour une entreprise
    6. Recommande une action spécifique et actionnable

    **Critères pour is_security_alert=true:**
    - Présence de CVE avec CVSS >= 7.0
    - Exploitation active ou zero-day
    - Patch de sécurité critique disponible
    - Ransomware ou malware dangereux

    Sois précis, factuel et base-toi sur les informations de l'article.
    """,
    retries=2,  # Retry automatique en cas d'erreur API
    defer_model_check=False
)


@classification_agent.tool
async def search_cve_context(
    ctx: RunContext[ClassificationDependencies],
    cve_or_technology: str
) -> str:
    """
    Rechercher du contexte sur un CVE ou une technologie dans la base RAG.

    Args:
        cve_or_technology: Identifiant CVE (ex: CVE-2024-1234) ou nom de technologie

    Returns:
        Contexte enrichi depuis la base de connaissances
    """
    logger.info(f"🔍 Recherche RAG pour: {cve_or_technology}")
    return await ctx.deps.search_cve_context(cve_or_technology)


async def classify_article_with_agent(
    article: dict,
    archon_client=None
) -> ArticleClassification:
    """
    Classifier un article en utilisant l'agent PydanticAI

    Args:
        article: Dict contenant title, description, content, link
        archon_client: Client Archon pour accès RAG (optionnel)

    Returns:
        ArticleClassification validé par Pydantic

    Raises:
        Exception: Si la classification échoue après retries
    """
    try:
        # Préparer les dépendances
        deps = ClassificationDependencies(archon_client)

        # Préparer le prompt avec l'article
        content_preview = article.get('content', '')[:2000]  # Limiter pour API
        prompt = f"""
Analyse cet article de veille IT et fournis une classification structurée complète.

**Article:**
Titre: {article.get('title', 'Sans titre')}
URL: {article.get('link', '')}
Description: {article.get('description', '')}

Contenu (extrait):
{content_preview}

Source: {article.get('feed_source', 'Unknown')}
Tags: {article.get('tags', '')}

**Instructions:**
1. Identifie la technologie principale concernée
2. Si tu identifies un CVE ou une technologie, utilise search_cve_context pour enrichir ton analyse
3. Détermine la catégorie la plus appropriée
4. Évalue la sévérité en fonction de l'impact réel
5. Extrais tous les CVE mentionnés
6. Fournis une analyse d'impact business concrète
7. Recommande une action spécifique

N'invente rien, base-toi uniquement sur les informations de l'article.
"""

        # Exécuter l'agent avec les dépendances
        result = await classification_agent.run(
            prompt,
            deps=deps
        )

        # L'agent retourne automatiquement un ArticleClassification validé
        classification = result.data

        logger.info(
            f"✅ Classification réussie: {classification.technology.value} "
            f"({classification.severity_level.value})"
        )

        return classification

    except Exception as e:
        logger.error(f"❌ Erreur classification agent: {e}")
        raise


async def classify_with_fallback(
    article: dict,
    archon_client=None
) -> ArticleClassification:
    """
    Classifier avec fallback mots-clés en cas d'erreur

    Cette fonction garantit toujours un résultat, soit via l'agent IA,
    soit via le système de mots-clés legacy.

    Args:
        article: Article à classifier
        archon_client: Client Archon optionnel

    Returns:
        ArticleClassification (toujours)
    """
    try:
        # Tentative avec l'agent PydanticAI
        return await classify_article_with_agent(article, archon_client)

    except Exception as e:
        logger.warning(f"⚠️ Classification IA échouée: {e}, utilisation fallback mots-clés")

        # Fallback sur l'ancien système
        from src.classifier import ArticleClassifier
        old_classifier = ArticleClassifier()
        legacy_result = old_classifier.classify_article(article)

        # Convertir en ArticleClassification Pydantic
        return ArticleClassification(
            technology=TechnologyType(legacy_result.get('technology', 'other')),
            category=CategoryType(legacy_result.get('category', 'news')),
            severity_level=SeverityLevel(legacy_result.get('severity_level', 'medium')),
            severity_score=legacy_result.get('severity_score', 5.0),
            cvss_score=legacy_result.get('cvss_score'),
            is_security_alert=legacy_result.get('is_security_alert', False),
            impact_analysis=legacy_result.get('impact_analysis', '')[:500],
            action_required=legacy_result.get('action_required', '')[:300],
            cve_references=legacy_result.get('cve_references', []),
            confidence_score=0.6  # Score plus faible pour fallback
        )


def classify_article_sync(
    article: dict,
    archon_client=None
) -> ArticleClassification:
    """
    Version synchrone pour compatibilité avec le code existant

    Args:
        article: Article à classifier
        archon_client: Client Archon optionnel

    Returns:
        ArticleClassification
    """
    import asyncio

    # Créer une nouvelle event loop si nécessaire
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        classify_with_fallback(article, archon_client)
    )


# Export pour compatibilité
__all__ = [
    'classification_agent',
    'classify_article_with_agent',
    'classify_with_fallback',
    'classify_article_sync'
]


# Test si exécuté directement
if __name__ == "__main__":
    import asyncio

    # Article de test
    test_article = {
        'title': 'Critical Fortinet FortiOS Vulnerability CVE-2024-12345',
        'description': 'A critical vulnerability in FortiOS allows remote code execution',
        'content': 'Fortinet has released a security advisory for CVE-2024-12345...',
        'link': 'https://example.com/fortinet-cve',
        'feed_source': 'fortinet',
        'tags': 'security, vulnerability'
    }

    async def test():
        result = await classify_with_fallback(test_article)
        print("\n✅ Test de classification:")
        print(result.model_dump_json(indent=2))

    asyncio.run(test())
