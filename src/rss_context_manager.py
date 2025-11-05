"""
TechWatchIT - Gestionnaire de sources RSS par contexte
Gestion des flux RSS organisés par contextes métier
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class RSSContext(str, Enum):
    """Contextes RSS disponibles"""
    VEILLE_TECHNO = "veille_techno"
    CVE_VULNERABILITES = "cve_vulnerabilites"
    EXPLOITS_MENACES = "exploits_menaces"
    ACTUALITES_IT = "actualites_it"


class RSSContextManager:
    """
    Gestionnaire de sources RSS par contexte métier

    Permet de charger, filtrer et gérer les flux RSS organisés
    par contextes: veille techno, CVE, exploits, actualités IT.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialiser le gestionnaire RSS

        Args:
            config_path: Chemin vers le fichier de configuration JSON
                        (par défaut: config/rss_sources_by_context.json)
        """
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "rss_sources_by_context.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Charger la configuration depuis le fichier JSON"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration RSS non trouvée: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_feeds_by_context(self, context: str) -> List[Dict]:
        """
        Obtenir tous les flux RSS d'un contexte spécifique

        Args:
            context: Nom du contexte (veille_techno, cve_vulnerabilites, etc.)

        Returns:
            Liste de dictionnaires contenant les informations des feeds
        """
        if context not in self.config:
            raise ValueError(f"Contexte inconnu: {context}")

        return self.config[context].get("feeds", [])

    def get_all_feeds(self) -> Dict[str, List[Dict]]:
        """
        Obtenir tous les flux RSS organisés par contexte

        Returns:
            Dictionnaire {context: [feeds]}
        """
        all_feeds = {}
        for context in RSSContext:
            all_feeds[context.value] = self.get_feeds_by_context(context.value)
        return all_feeds

    def get_feeds_flat(self, contexts: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtenir une liste plate de tous les feeds (compatibilité legacy)

        Args:
            contexts: Liste des contextes à inclure (None = tous)

        Returns:
            Liste plate de tous les feeds avec leur contexte ajouté
        """
        feeds = []

        if contexts is None:
            contexts = [c.value for c in RSSContext]

        for context in contexts:
            context_feeds = self.get_feeds_by_context(context)
            for feed in context_feeds:
                feed_copy = feed.copy()
                feed_copy['context'] = context
                feeds.append(feed_copy)

        return feeds

    def get_context_info(self, context: str) -> Dict:
        """
        Obtenir les métadonnées d'un contexte

        Args:
            context: Nom du contexte

        Returns:
            Dictionnaire avec description, color, icon
        """
        if context not in self.config:
            raise ValueError(f"Contexte inconnu: {context}")

        ctx_data = self.config[context]
        return {
            'context': context,
            'description': ctx_data.get('description', ''),
            'color': ctx_data.get('color', ''),
            'icon': ctx_data.get('icon', ''),
            'feed_count': len(ctx_data.get('feeds', []))
        }

    def get_all_contexts_info(self) -> List[Dict]:
        """Obtenir les métadonnées de tous les contextes"""
        return [self.get_context_info(c.value) for c in RSSContext]

    def get_feed_by_id(self, feed_id: str) -> Optional[Dict]:
        """
        Rechercher un feed spécifique par son ID

        Args:
            feed_id: ID unique du feed

        Returns:
            Dictionnaire du feed ou None si non trouvé
        """
        for context in RSSContext:
            feeds = self.get_feeds_by_context(context.value)
            for feed in feeds:
                if feed.get('id') == feed_id:
                    feed_copy = feed.copy()
                    feed_copy['context'] = context.value
                    return feed_copy
        return None

    def get_feeds_by_technology(self, technology: str) -> List[Dict]:
        """
        Obtenir tous les feeds d'une technologie spécifique

        Args:
            technology: Nom de la technologie (microsoft, vmware, etc.)

        Returns:
            Liste des feeds de cette technologie
        """
        matching_feeds = []

        for context in RSSContext:
            feeds = self.get_feeds_by_context(context.value)
            for feed in feeds:
                if feed.get('technology') == technology:
                    feed_copy = feed.copy()
                    feed_copy['context'] = context.value
                    matching_feeds.append(feed_copy)

        return matching_feeds

    def get_statistics(self) -> Dict:
        """Obtenir les statistiques sur les feeds configurés"""
        stats = {
            'total_feeds': 0,
            'by_context': {},
            'by_technology': {},
            'by_category': {}
        }

        for context in RSSContext:
            feeds = self.get_feeds_by_context(context.value)
            stats['by_context'][context.value] = len(feeds)
            stats['total_feeds'] += len(feeds)

            for feed in feeds:
                tech = feed.get('technology', 'unknown')
                cat = feed.get('category', 'unknown')

                stats['by_technology'][tech] = stats['by_technology'].get(tech, 0) + 1
                stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1

        return stats

    def validate_feeds(self) -> Dict[str, List[str]]:
        """
        Valider la configuration des feeds

        Returns:
            Dictionnaire {context: [erreurs]}
        """
        errors = {}
        required_fields = ['id', 'name', 'url', 'technology']

        for context in RSSContext:
            context_errors = []
            feeds = self.get_feeds_by_context(context.value)

            feed_ids = set()
            for feed in feeds:
                # Vérifier les champs requis
                for field in required_fields:
                    if field not in feed or not feed[field]:
                        context_errors.append(f"Feed manquant le champ '{field}': {feed.get('name', 'unknown')}")

                # Vérifier l'unicité des IDs
                feed_id = feed.get('id')
                if feed_id in feed_ids:
                    context_errors.append(f"ID dupliqué: {feed_id}")
                feed_ids.add(feed_id)

            if context_errors:
                errors[context.value] = context_errors

        return errors


# Instance globale
rss_manager = RSSContextManager()


# Fonctions helper pour compatibilité
def get_feeds_by_context(context: str) -> List[Dict]:
    """Helper: Obtenir les feeds d'un contexte"""
    return rss_manager.get_feeds_by_context(context)


def get_all_feeds_flat() -> List[Dict]:
    """Helper: Obtenir tous les feeds en liste plate"""
    return rss_manager.get_feeds_flat()


def get_context_statistics() -> Dict:
    """Helper: Obtenir les statistiques"""
    return rss_manager.get_statistics()


if __name__ == "__main__":
    # Tests
    print("=" * 60)
    print("RSS Context Manager - Tests")
    print("=" * 60)

    manager = RSSContextManager()

    # Test 1: Contextes info
    print("\n[TEST 1] Informations sur les contextes")
    print("-" * 60)
    for ctx_info in manager.get_all_contexts_info():
        print(f"[{ctx_info['context']}] {ctx_info['feed_count']} feeds - {ctx_info['color']}")
        print(f"   {ctx_info['description']}")

    # Test 2: Feeds par contexte
    print("\n[TEST 2] Feeds du contexte 'exploits_menaces'")
    print("-" * 60)
    exploits_feeds = manager.get_feeds_by_context('exploits_menaces')
    for feed in exploits_feeds[:3]:  # Afficher les 3 premiers
        print(f"  • {feed['name']}: {feed['url']}")
    print(f"  ... et {len(exploits_feeds) - 3} autres")

    # Test 3: Feeds par technologie
    print("\n[TEST 3] Feeds pour Microsoft")
    print("-" * 60)
    ms_feeds = manager.get_feeds_by_technology('microsoft')
    for feed in ms_feeds:
        print(f"  • [{feed['context']}] {feed['name']}")

    # Test 4: Statistiques
    print("\n[TEST 4] Statistiques")
    print("-" * 60)
    stats = manager.get_statistics()
    print(f"Total feeds: {stats['total_feeds']}")
    print("\nPar contexte:")
    for ctx, count in stats['by_context'].items():
        print(f"  • {ctx}: {count}")

    # Test 5: Validation
    print("\n[TEST 5] Validation de la configuration")
    print("-" * 60)
    errors = manager.validate_feeds()
    if errors:
        print("Erreurs trouvées:")
        for ctx, err_list in errors.items():
            print(f"  [{ctx}]")
            for err in err_list:
                print(f"    - {err}")
    else:
        print("[OK] Configuration valide!")

    print("\n" + "=" * 60)
    print("Tests terminés!")
    print("=" * 60)
