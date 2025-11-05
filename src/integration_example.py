"""
TechWatchIT - Exemple d'intégration des agents PydanticAI
Montre comment utiliser les nouveaux agents dans le pipeline existant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from typing import Dict, Optional
import logging
from datetime import datetime

# Import des nouveaux agents
from src.classifier_agent import classify_with_fallback
from src.summarizer_agent import summarize_with_fallback
from src.models import ArticleClassification, ArticleSummary

# Import legacy pour comparaison
from src.classifier import ArticleClassifier as LegacyClassifier

# Configuration
logger = logging.getLogger(__name__)
USE_NEW_AGENTS = os.getenv("USE_PYDANTIC_AI", "true").lower() == "true"


async def process_article_new(
    article: Dict,
    archon_client=None
) -> Dict:
    """
    Traiter un article avec les nouveaux agents PydanticAI

    Args:
        article: Article brut depuis RSS
        archon_client: Client Archon pour RAG (optionnel)

    Returns:
        Dict contenant classification et résumé
    """
    start_time = datetime.now()

    try:
        logger.info(f"🤖 Traitement PydanticAI: {article.get('title', '')[:60]}...")

        # Étape 1: Classification avec validation Pydantic
        classification = await classify_with_fallback(article, archon_client)

        logger.info(
            f"   ✅ Classifié: {classification.technology.value} "
            f"(sévérité: {classification.severity_level.value}, "
            f"score: {classification.severity_score:.1f})"
        )

        # Étape 2: Résumé enrichi avec RAG
        summary = await summarize_with_fallback(
            article,
            classification,
            archon_client
        )

        logger.info(f"   ✅ Résumé: {len(summary.key_points)} points clés")

        # Calculer le temps de traitement
        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            'success': True,
            'classification': classification.model_dump(),
            'summary': summary.model_dump(),
            'processing_time': processing_time,
            'agent_used': 'PydanticAI',
            'confidence': classification.confidence_score
        }

    except Exception as e:
        logger.error(f"❌ Erreur traitement PydanticAI: {e}")
        return {
            'success': False,
            'error': str(e),
            'processing_time': (datetime.now() - start_time).total_seconds()
        }


def process_article_legacy(article: Dict) -> Dict:
    """
    Traiter un article avec l'ancien système (pour comparaison)

    Args:
        article: Article brut depuis RSS

    Returns:
        Dict contenant classification legacy
    """
    start_time = datetime.now()

    try:
        classifier = LegacyClassifier()
        result = classifier.classify_article(article)

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            'success': True,
            'classification': result,
            'processing_time': processing_time,
            'agent_used': 'Legacy'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processing_time': (datetime.now() - start_time).total_seconds()
        }


async def process_article_hybrid(
    article: Dict,
    archon_client=None,
    use_new_agents: bool = True
) -> Dict:
    """
    Traiter un article avec agents hybrides (nouveau avec fallback legacy)

    Cette fonction permet de basculer entre les agents selon la configuration
    et fournit un fallback automatique en cas d'erreur.

    Args:
        article: Article à traiter
        archon_client: Client Archon optionnel
        use_new_agents: Utiliser les agents PydanticAI (défaut: True)

    Returns:
        Résultat du traitement
    """
    if use_new_agents:
        result = await process_article_new(article, archon_client)

        # Si échec, fallback sur legacy
        if not result['success']:
            logger.warning("⚠️ Agents PydanticAI échoués, fallback legacy")
            return process_article_legacy(article)

        return result
    else:
        return process_article_legacy(article)


def save_processed_article_to_db(
    article_id: int,
    classification: Dict,
    summary: Optional[Dict] = None,
    db_manager=None
) -> bool:
    """
    Sauvegarder les résultats dans la base de données

    Compatible avec l'ancien format de database.py

    Args:
        article_id: ID de l'article brut
        classification: Classification (format dict)
        summary: Résumé optionnel (format dict)
        db_manager: Instance DatabaseManager

    Returns:
        True si sauvegarde réussie
    """
    try:
        if not db_manager:
            from src.database import db
            db_manager = db

        # Préparer les données pour la base
        processed_data = {
            'category': classification.get('category'),
            'technology': classification.get('technology'),
            'severity_level': classification.get('severity_level'),
            'severity_score': classification.get('severity_score'),
            'cvss_score': classification.get('cvss_score'),
            'is_security_alert': classification.get('is_security_alert'),
            'impact_analysis': classification.get('impact_analysis', ''),
            'action_required': classification.get('action_required', '')
        }

        # Ajouter le résumé si disponible
        if summary:
            processed_data['summary'] = summary.get('summary', '')

        # Sauvegarder dans MySQL
        success = db_manager.save_processed_article(article_id, processed_data)

        return success

    except Exception as e:
        logger.error(f"Erreur sauvegarde DB: {e}")
        return False


async def compare_agents(article: Dict) -> Dict:
    """
    Comparer les performances entre agents PydanticAI et Legacy

    Utile pour évaluation et migration progressive.

    Args:
        article: Article à analyser

    Returns:
        Comparaison des résultats
    """
    logger.info("🔬 Comparaison agents PydanticAI vs Legacy")

    # Exécuter en parallèle
    new_result, legacy_result = await asyncio.gather(
        process_article_new(article),
        asyncio.to_thread(process_article_legacy, article),
        return_exceptions=True
    )

    comparison = {
        'article_title': article.get('title', '')[:100],
        'pydantic_ai': new_result if not isinstance(new_result, Exception) else {'error': str(new_result)},
        'legacy': legacy_result if not isinstance(legacy_result, Exception) else {'error': str(legacy_result)},
        'time_difference': None,
        'classification_match': False
    }

    # Comparer les résultats
    if new_result.get('success') and legacy_result.get('success'):
        comparison['time_difference'] = (
            new_result['processing_time'] - legacy_result['processing_time']
        )

        # Vérifier si classifications correspondent
        new_tech = new_result['classification'].get('technology')
        legacy_tech = legacy_result['classification'].get('technology')
        comparison['classification_match'] = (new_tech == legacy_tech)

    return comparison


# Exemple d'utilisation dans main.py
async def example_pipeline():
    """
    Exemple de pipeline complet avec les nouveaux agents
    """
    # Article de test
    test_article = {
        'id': 1,
        'title': 'Critical FortiOS Vulnerability CVE-2024-12345 Enables Remote Code Execution',
        'description': 'Fortinet has disclosed a critical vulnerability affecting FortiOS versions 7.0.x',
        'content': '''
        Fortinet has released a critical security advisory for CVE-2024-12345,
        a remote code execution vulnerability in FortiOS. The vulnerability affects
        FortiOS versions 7.0.0 through 7.0.12. Exploitation of this vulnerability
        could allow an unauthenticated attacker to execute arbitrary code.

        CVSS Score: 9.8 (Critical)
        Affected Products: FortiGate appliances running FortiOS

        Fortinet strongly recommends immediate patching to version 7.0.13 or later.
        ''',
        'link': 'https://www.fortiguard.com/psirt/FG-IR-24-12345',
        'feed_source': 'fortinet',
        'tags': 'security, vulnerability, critical'
    }

    print("=" * 60)
    print("EXEMPLE: Pipeline TechWatchIT avec PydanticAI")
    print("=" * 60)

    # Traiter l'article
    result = await process_article_hybrid(test_article)

    if result['success']:
        print(f"\n✅ Traitement réussi ({result['processing_time']:.2f}s)")
        print(f"\n📊 Classification:")
        classification = result['classification']
        print(f"   - Technologie: {classification['technology']}")
        print(f"   - Catégorie: {classification['category']}")
        print(f"   - Sévérité: {classification['severity_level']} ({classification['severity_score']}/10)")
        print(f"   - CVSS: {classification.get('cvss_score', 'N/A')}")
        print(f"   - CVE: {', '.join(classification.get('cve_references', []))}")
        print(f"   - Alerte: {'OUI' if classification['is_security_alert'] else 'NON'}")

        if 'summary' in result:
            print(f"\n📝 Résumé:")
            summary = result['summary']
            print(f"   {summary['summary']}")
            print(f"\n   Points clés:")
            for point in summary['key_points']:
                print(f"   • {point}")
    else:
        print(f"\n❌ Échec: {result.get('error')}")

    # Comparaison avec legacy
    print("\n" + "=" * 60)
    print("COMPARAISON: PydanticAI vs Legacy")
    print("=" * 60)

    comparison = await compare_agents(test_article)

    print(f"\nTechnologie détectée:")
    print(f"   - PydanticAI: {comparison['pydantic_ai'].get('classification', {}).get('technology', 'N/A')}")
    print(f"   - Legacy: {comparison['legacy'].get('classification', {}).get('technology', 'N/A')}")
    print(f"   - Match: {'✅' if comparison['classification_match'] else '❌'}")

    if comparison['time_difference'] is not None:
        diff = comparison['time_difference']
        print(f"\nPerformance:")
        print(f"   - Différence: {diff:+.2f}s")
        print(f"   - {'PydanticAI plus rapide' if diff < 0 else 'Legacy plus rapide'}")


if __name__ == "__main__":
    # Exécuter l'exemple
    asyncio.run(example_pipeline())
