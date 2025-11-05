"""
TechWatchIT - Agent de Résumé PydanticAI
Génération de résumés intelligents avec enrichissement RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from typing import Optional, List
import logging
from datetime import datetime

from src.models import (
    ArticleSummary,
    ArticleClassification
)
from config.config import Config

# Logger
logger = logging.getLogger(__name__)


class SummarizationDependencies:
    """Dépendances pour l'agent de résumé"""

    def __init__(self, archon_client=None):
        self.archon_client = archon_client
        self.rag_articles_source_id = os.getenv("ARCHON_RAG_ARTICLES_SOURCE_ID", None)

    async def find_similar_articles(self, title: str, technology: str) -> List[str]:
        """Trouver des articles similaires dans l'historique via RAG"""
        if not self.archon_client or not self.rag_articles_source_id:
            return []

        try:
            query = f"{title} {technology}"
            results = self.archon_client.rag_search_knowledge_base(
                query=query,
                source_id=self.rag_articles_source_id,
                match_count=3
            )

            if results.get('success') and results.get('results'):
                similar = []
                for result in results['results'][:3]:
                    similar.append(result.get('url', 'Article similaire'))
                return similar

            return []
        except Exception as e:
            logger.warning(f"Erreur recherche articles similaires: {e}")
            return []


# Créer l'agent de résumé
summarization_agent = Agent(
    model=OpenAIModel('gpt-4o'),
    result_type=ArticleSummary,
    system_prompt="""
    Tu es un expert en cybersécurité qui génère des résumés clairs, concis et actionnables.

    **Ton rôle:**
    - Résumer l'article en 3-4 phrases maximum (max 500 caractères)
    - Extraire 3-5 points clés essentiels
    - Évaluer l'impact business concret pour une entreprise
    - Fournir des détails techniques pertinents
    - Recommander des actions spécifiques

    **Style de rédaction:**
    - Concis et direct
    - Factuel, sans exagération
    - Orienté action
    - Adapté à un public technique (DSI, RSSI, admins sys)

    **Pour les articles de sécurité:**
    - Priorise l'impact et l'urgence
    - Mentionne les systèmes affectés
    - Indique la disponibilité de patches
    - Évalue le risque d'exploitation

    **Pour les mises à jour produit:**
    - Résume les nouvelles fonctionnalités clés
    - Identifie les bénéfices business
    - Note les prérequis de migration

    Utilise le tool find_similar_articles pour enrichir ton analyse avec le contexte historique.
    """,
    retries=2
)


@summarization_agent.tool
async def find_similar_articles(
    ctx: RunContext[SummarizationDependencies],
    title: str,
    technology: str
) -> str:
    """
    Rechercher des articles similaires dans l'historique

    Args:
        title: Titre de l'article actuel
        technology: Technologie concernée

    Returns:
        Liste des articles similaires trouvés
    """
    logger.info(f"🔍 Recherche articles similaires: {technology}")
    similar = await ctx.deps.find_similar_articles(title, technology)

    if similar:
        return f"Articles similaires trouvés: {', '.join(similar)}"
    return "Aucun article similaire trouvé dans l'historique"


async def summarize_article_with_agent(
    article: dict,
    classification: ArticleClassification,
    archon_client=None
) -> ArticleSummary:
    """
    Générer un résumé d'article avec l'agent PydanticAI

    Args:
        article: Dict contenant l'article
        classification: Classification de l'article
        archon_client: Client Archon pour RAG (optionnel)

    Returns:
        ArticleSummary validé par Pydantic

    Raises:
        Exception: Si la génération échoue après retries
    """
    try:
        # Préparer les dépendances
        deps = SummarizationDependencies(archon_client)

        # Construire le contexte
        content_preview = article.get('content', '')[:3000]
        description = article.get('description', '')

        # Informations de classification
        tech = classification.technology.value
        severity = classification.severity_level.value
        category = classification.category.value

        prompt = f"""
Génère un résumé professionnel de cet article de sécurité IT.

**Article:**
Titre: {article.get('title', '')}
URL: {article.get('link', '')}

Description: {description}

Contenu (extrait):
{content_preview}

**Classification:**
- Technologie: {tech}
- Catégorie: {category}
- Sévérité: {severity}
- Score: {classification.severity_score}/10
{f"- CVSS: {classification.cvss_score}" if classification.cvss_score else ""}
{f"- CVE: {', '.join(classification.cve_references)}" if classification.cve_references else ""}

**Instructions:**
1. Rédige un résumé concis (max 500 caractères)
2. Extrais 3-5 points clés essentiels
3. Évalue l'impact business concret
4. Fournis des détails techniques pertinents
5. Recommande des actions spécifiques
6. Utilise find_similar_articles pour enrichir ton analyse

**Ton de l'analyse:**
- Si sévérité CRITICAL/HIGH: Focus sur l'urgence et les actions immédiates
- Si sévérité MEDIUM: Focus sur la planification et les meilleures pratiques
- Si sévérité LOW: Focus sur l'information et la veille

Sois factuel, précis et actionnable.
"""

        # Exécuter l'agent
        result = await summarization_agent.run(
            prompt,
            deps=deps
        )

        summary = result.data

        logger.info(f"✅ Résumé généré: {len(summary.key_points)} points clés")

        return summary

    except Exception as e:
        logger.error(f"❌ Erreur génération résumé agent: {e}")
        raise


async def summarize_with_fallback(
    article: dict,
    classification: ArticleClassification,
    archon_client=None
) -> ArticleSummary:
    """
    Générer un résumé avec fallback basique en cas d'erreur

    Args:
        article: Article à résumer
        classification: Classification de l'article
        archon_client: Client Archon optionnel

    Returns:
        ArticleSummary (toujours)
    """
    try:
        # Tentative avec l'agent PydanticAI
        return await summarize_article_with_agent(article, classification, archon_client)

    except Exception as e:
        logger.warning(f"⚠️ Résumé IA échoué: {e}, utilisation fallback basique")

        # Fallback: résumé basique
        title = article.get('title', '')
        description = article.get('description', '')[:300]

        # Générer des points clés basiques
        key_points = []
        if classification.technology:
            key_points.append(f"Concerne {classification.technology.value}")
        if classification.cve_references:
            key_points.append(f"CVE: {', '.join(classification.cve_references[:2])}")
        if classification.severity_level:
            key_points.append(f"Sévérité {classification.severity_level.value}")

        # Ajouter au moins 3 points
        if len(key_points) < 3:
            key_points.append("Voir l'article complet pour détails")

        return ArticleSummary(
            summary=description or f"Résumé de: {title}"[:500],
            key_points=key_points[:5],
            business_impact=classification.impact_analysis[:300],
            technical_details=description[:400],
            similar_incidents=[],
            recommendations=[classification.action_required]
        )


def summarize_article_sync(
    article: dict,
    classification: ArticleClassification,
    archon_client=None
) -> ArticleSummary:
    """
    Version synchrone pour compatibilité

    Args:
        article: Article à résumer
        classification: Classification
        archon_client: Client Archon optionnel

    Returns:
        ArticleSummary
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        summarize_with_fallback(article, classification, archon_client)
    )


# Export
__all__ = [
    'summarization_agent',
    'summarize_article_with_agent',
    'summarize_with_fallback',
    'summarize_article_sync'
]


# Test
if __name__ == "__main__":
    import asyncio
    from src.models import TechnologyType, SeverityLevel, CategoryType

    test_article = {
        'title': 'Critical FortiOS Vulnerability Allows Remote Code Execution',
        'description': 'Fortinet has disclosed a critical vulnerability in FortiOS that could allow attackers to execute arbitrary code remotely. Organizations should apply patches immediately.',
        'content': 'A critical security vulnerability (CVE-2024-12345) has been discovered in Fortinet FortiOS versions 7.0.0 through 7.0.12...',
        'link': 'https://example.com/fortios-vuln'
    }

    test_classification = ArticleClassification(
        technology=TechnologyType.FORTINET,
        category=CategoryType.VULNERABILITY,
        severity_level=SeverityLevel.CRITICAL,
        severity_score=9.5,
        cvss_score=9.8,
        is_security_alert=True,
        impact_analysis="Permet l'exécution de code à distance sur les appliances FortiGate",
        action_required="Appliquer immédiatement le patch FortiOS 7.0.13+",
        cve_references=["CVE-2024-12345"]
    )

    async def test():
        summary = await summarize_with_fallback(test_article, test_classification)
        print("\n✅ Test de résumé:")
        print(summary.model_dump_json(indent=2))

    asyncio.run(test())
