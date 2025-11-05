# Plan de Refactorisation TechWatchIT
## Architecture Moderne avec Archon, RAG et PydanticAI

---

## 📋 Vue d'ensemble

Ce document détaille la stratégie de refactorisation de **TechWatchIT** pour moderniser son architecture en intégrant :

1. **Archon MCP** - Gestion de projet, tâches, documents et base de connaissances RAG
2. **PydanticAI** - Agents IA avec validation structurée et type safety
3. **RAG** - Base de connaissances CVE/vulnérabilités pour classifications enrichies

---

## 🏗️ Architecture Actuelle

### Composants Existants

```
TechWatchIT/
├── main.py                 # Orchestration manuelle
├── src/
│   ├── classifier.py       # OpenAI direct + JSON parsing manuel
│   ├── summarizer.py       # Génération résumés basique
│   ├── database.py         # MySQL uniquement
│   └── fetch_feeds.py      # Collection RSS simple
├── scripts/
│   ├── alert_handler.py    # Alertes critiques
│   └── daily_digest.py     # Email digest
└── config/config.py        # Configuration centralisée
```

### Limitations Actuelles

| Composant | Problème | Impact |
|-----------|----------|--------|
| **classifier.py** | Parsing JSON manuel, pas de validation | Erreurs silencieuses, inconsistances |
| **summarizer.py** | Pas de contexte historique | Résumés génériques |
| **database.py** | Pas de versioning | Perte d'historique d'analyse |
| **main.py** | Orchestration manuelle | Pas de tracking de progression |
| **Général** | Pas de base de connaissances | Classifications limitées |

---

## 🎯 Architecture Proposée

### 1. Intégration Archon MCP

#### A. Gestion des Tâches (Task Management)

**Actuellement** : Fonctions exécutées séquentiellement sans tracking
```python
# main.py (ancien)
fetch_feeds()           # Pas de statut
process_articles()      # Pas de progression
send_alerts()          # Pas de tracking
```

**Avec Archon** : Workflow task-driven avec statuts
```python
# main.py (nouveau)
from archon_client import ArchonClient

archon = ArchonClient()

# Créer les tâches
fetch_task = archon.create_task("Collecter flux RSS", project_id=PROJECT_ID)
process_task = archon.create_task("Traiter articles IA", project_id=PROJECT_ID)

# Exécuter avec tracking
archon.update_task(fetch_task.id, status="doing")
result = fetch_feeds()
archon.update_task(fetch_task.id, status="done")

# Progression visible dans Archon UI
```

**Bénéfices** :
- ✅ Visibilité complète de la progression
- ✅ Historique des exécutions
- ✅ Détection des blocages
- ✅ Reprise après erreur

#### B. Stockage de Documents

**Stocker métadonnées et analyses** :
```python
# Après traitement d'un article
archon.create_document(
    project_id=PROJECT_ID,
    title=f"Analyse: {article['title']}",
    document_type="note",
    content={
        "article_id": article_id,
        "classification": classification_result,
        "summary": summary,
        "cve_references": extracted_cves,
        "risk_score": risk_score,
        "timestamp": datetime.now()
    }
)
```

**Versioning automatique** :
```python
# Chaque modification crée une version
archon.create_version(
    project_id=PROJECT_ID,
    field_name="docs",
    content=updated_analysis,
    change_summary="Reclassification suite à nouveau CVE"
)
```

#### C. Base de Connaissances RAG

**Structure de la source RAG** :
```
RAG Source: "TechWatchIT CVE Database"
├── CVE historiques (NVD exports)
├── Descriptions technologies (Fortinet, SentinelOne, VMware, etc.)
├── Patterns de vulnérabilités communs
├── Historique d'incidents (ransomware, zero-days)
└── Recommandations de sécurité
```

**Utilisation** :
```python
# Enrichir la classification avec contexte RAG
rag_results = archon.rag_search_knowledge_base(
    query=f"{article_title} {technology_detected}",
    source_id=TECHWATCHIT_SOURCE_ID,
    match_count=3
)

# Utiliser le contexte dans le prompt IA
context = "\n".join([r['content'] for r in rag_results['results']])
enhanced_classification = classify_with_context(article, context)
```

---

### 2. Migration vers PydanticAI

#### A. Modèles Pydantic Stricts

**Définir des schémas de données validés** :

```python
# src/models.py (nouveau fichier)
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional

class TechnologyType(str, Enum):
    FORTINET = "fortinet"
    SENTINELONE = "sentinelone"
    JUMPCLOUD = "jumpcloud"
    VMWARE = "vmware"
    RUBRIK = "rubrik"
    DELL = "dell"
    MICROSOFT = "microsoft"
    EXPLOITS = "exploits"
    OTHER = "other"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ArticleClassification(BaseModel):
    """Classification structurée d'un article de veille IT"""

    technology: TechnologyType = Field(description="Technologie principale concernée")
    category: str = Field(description="Catégorie: security|update|vulnerability|patch|product|news")
    severity_level: SeverityLevel = Field(description="Niveau de sévérité")
    severity_score: float = Field(ge=1.0, le=10.0, description="Score de sévérité 1-10")
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Score CVSS si disponible")
    is_security_alert: bool = Field(description="Indique si c'est une alerte de sécurité")
    impact_analysis: str = Field(max_length=500, description="Analyse de l'impact")
    action_required: str = Field(max_length=300, description="Action recommandée")
    cve_references: list[str] = Field(default_factory=list, description="Liste des CVE mentionnés")

    @field_validator('severity_score')
    @classmethod
    def validate_severity_score(cls, v: float, info) -> float:
        """Valider la cohérence severity_level <-> severity_score"""
        severity_level = info.data.get('severity_level')
        if severity_level == SeverityLevel.CRITICAL and v < 8.0:
            return 9.0  # Auto-correction
        elif severity_level == SeverityLevel.HIGH and v < 6.0:
            return 7.0
        return v

class ArticleSummary(BaseModel):
    """Résumé structuré d'un article"""

    summary: str = Field(max_length=500, description="Résumé concis")
    key_points: list[str] = Field(description="Points clés (3-5 items)")
    business_impact: str = Field(description="Impact pour l'entreprise")
    technical_details: str = Field(description="Détails techniques")
    similar_incidents: list[str] = Field(default_factory=list, description="Incidents similaires (depuis RAG)")
```

**Bénéfices** :
- ✅ Validation automatique des types
- ✅ Auto-complétion IDE
- ✅ Documentation intégrée
- ✅ Sérialisation JSON fiable

#### B. Agent de Classification PydanticAI

**Refactoriser [classifier.py](classifier.py:1)** :

```python
# src/classifier_agent.py (nouveau)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from .models import ArticleClassification, TechnologyType
from archon_client import ArchonClient

# Initialiser l'agent
classification_agent = Agent(
    model=OpenAIModel('gpt-4o'),
    result_type=ArticleClassification,
    system_prompt="""
    Tu es un expert en cybersécurité spécialisé dans l'analyse de veille IT.

    Ton rôle est de classifier des articles avec précision en identifiant :
    - La technologie concernée (Fortinet, SentinelOne, VMware, etc.)
    - Le niveau de sévérité (critical/high/medium/low)
    - Les CVE mentionnés
    - L'impact et les actions recommandées

    Utilise le contexte RAG fourni pour enrichir ton analyse.
    """,
    retries=2  # Retry automatique en cas d'erreur
)

@classification_agent.tool
async def search_similar_cves(ctx, query: str) -> str:
    """Rechercher des CVE similaires dans la base RAG"""
    archon = ArchonClient()
    results = archon.rag_search_knowledge_base(
        query=query,
        source_id="techwatchit_cve_db",
        match_count=3
    )
    return "\n".join([r['content'] for r in results['results']])

async def classify_article(article: dict) -> ArticleClassification:
    """Classifier un article avec validation automatique"""

    # Préparer le prompt avec l'article
    prompt = f"""
    Analyse cet article de veille IT et fournis une classification structurée.

    Titre: {article['title']}
    Description: {article['description']}
    Contenu: {article['content'][:2000]}
    URL: {article['link']}

    Utilise le tool search_similar_cves si tu identifies une technologie ou un CVE.
    """

    # L'agent retourne automatiquement un objet ArticleClassification validé
    result = await classification_agent.run(prompt)

    # Pydantic garantit que result.data est un ArticleClassification valide
    return result.data

# Utilisation avec fallback
async def classify_with_fallback(article: dict) -> ArticleClassification:
    """Classifier avec fallback mots-clés en cas d'erreur"""
    try:
        return await classify_article(article)
    except Exception as e:
        logger.warning(f"Classification IA échouée: {e}, utilisation fallback")
        return keyword_based_classification(article)  # Ancien système
```

**Améliorations** :
- ✅ **Type safety** : Plus d'erreurs de parsing JSON
- ✅ **Validation automatique** : Pydantic vérifie les types et contraintes
- ✅ **Retry logic** : Réessai automatique en cas d'erreur temporaire
- ✅ **Tools** : Accès à RAG directement depuis l'agent
- ✅ **Testabilité** : Utilisation de `TestModel` pour les tests

#### C. Agent de Résumé Intelligent

```python
# src/summarizer_agent.py (nouveau)
from pydantic_ai import Agent
from .models import ArticleSummary

summarization_agent = Agent(
    model=OpenAIModel('gpt-4o'),
    result_type=ArticleSummary,
    system_prompt="""
    Tu es un expert en cybersécurité qui génère des résumés clairs et actionnables.

    Tes résumés doivent :
    - Être concis (max 500 caractères)
    - Identifier les points clés
    - Évaluer l'impact business
    - Fournir des détails techniques pertinents
    - Référencer des incidents similaires si trouvés dans la base RAG
    """
)

@summarization_agent.tool
async def find_similar_articles(ctx, title: str, technology: str) -> list[str]:
    """Trouver des articles similaires dans l'historique"""
    archon = ArchonClient()
    results = archon.rag_search_knowledge_base(
        query=f"{title} {technology}",
        source_id="techwatchit_articles",
        match_count=3
    )
    return [r['title'] for r in results['results']]

async def summarize_article(article: dict, classification: ArticleClassification) -> ArticleSummary:
    """Générer un résumé enrichi avec contexte RAG"""

    prompt = f"""
    Génère un résumé de cet article de sécurité IT.

    Article: {article['title']}
    Technologie: {classification.technology.value}
    Sévérité: {classification.severity_level.value}
    Description: {article['description']}

    Utilise find_similar_articles pour enrichir ton analyse.
    """

    result = await summarization_agent.run(prompt)
    return result.data
```

#### D. Tests avec TestModel

```python
# tests/test_classifier_agent.py (nouveau)
import pytest
from pydantic_ai.models.test import TestModel
from src.classifier_agent import classification_agent
from src.models import ArticleClassification, SeverityLevel

@pytest.mark.asyncio
async def test_classification_structure():
    """Tester que l'agent retourne une structure valide"""

    # Simuler une réponse IA sans appel API
    test_model = TestModel(
        custom_result_text='{"technology": "fortinet", "category": "vulnerability", '
                          '"severity_level": "critical", "severity_score": 9.5, '
                          '"is_security_alert": true, "impact_analysis": "Test impact", '
                          '"action_required": "Test action", "cve_references": ["CVE-2024-1234"]}'
    )

    agent = Agent(model=test_model, result_type=ArticleClassification)
    result = await agent.run("Test article")

    # Vérifier la structure
    assert isinstance(result.data, ArticleClassification)
    assert result.data.severity_level == SeverityLevel.CRITICAL
    assert result.data.severity_score >= 8.0
    assert "CVE-2024-1234" in result.data.cve_references

@pytest.mark.asyncio
async def test_validation_auto_correction():
    """Tester la validation et auto-correction"""

    # Donnée incohérente : severity=critical mais score=5.0
    test_model = TestModel(
        custom_result_text='{"technology": "vmware", "category": "security", '
                          '"severity_level": "critical", "severity_score": 5.0, '
                          '"is_security_alert": true, "impact_analysis": "Test", '
                          '"action_required": "Test", "cve_references": []}'
    )

    agent = Agent(model=test_model, result_type=ArticleClassification)
    result = await agent.run("Test")

    # Le validator devrait corriger le score
    assert result.data.severity_score >= 8.0  # Auto-correction
```

---

### 3. Flux de Données Complet

```
┌─────────────────┐
│  RSS Feeds      │
│  (fetch_feeds)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Raw Articles   │
│  MySQL Storage  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Classification Agent (PydanticAI)  │
│  ├─ Tool: search_similar_cves(RAG)  │
│  └─ Returns: ArticleClassification  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Summarization Agent (PydanticAI)   │
│  ├─ Tool: find_similar_articles()   │
│  └─ Returns: ArticleSummary         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Storage                            │
│  ├─ MySQL: processed_articles       │
│  └─ Archon: Document + Version      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Alert Agent (PydanticAI)           │
│  ├─ Tool: get_cve_context(RAG)      │
│  ├─ Condition: severity=critical    │
│  └─ Action: Send enriched email     │
└─────────────────────────────────────┘
```

---

## 📝 Plan de Migration Détaillé

### Phase 1: Setup (1-2 jours)

**Tâches** :
- [ ] Mettre à jour [requirements.txt](requirements.txt:1)
- [ ] Configurer Archon MCP client
- [ ] Créer [src/models.py](src/models.py:1) avec modèles Pydantic
- [ ] Créer [tests/](tests/) directory structure

**Fichier requirements.txt** :
```txt
# Existant
feedparser
python-dotenv
beautifulsoup4
requests
PyMySQL
Flask
Flask-Cors
openai
bleach
pytz

# Nouveau
pydantic>=2.0.0
pydantic-ai>=0.0.13
httpx-sse
archon-sdk  # Client Archon MCP
pytest
pytest-asyncio
```

### Phase 2: RAG Knowledge Base (2-3 jours)

**Tâches** :
- [ ] Créer source RAG "TechWatchIT CVE Database"
- [ ] Importer données CVE (NVD exports)
- [ ] Ajouter descriptions technologies
- [ ] Tester recherche RAG

**Script d'import** :
```python
# scripts/import_cve_database.py (nouveau)
from archon_client import ArchonClient
import json

archon = ArchonClient()

# Créer la source RAG
source = archon.create_rag_source(
    title="TechWatchIT CVE Database",
    description="Base de connaissances CVE et vulnérabilités"
)

# Importer CVE historiques
with open("data/nvd_cve_export.json") as f:
    cve_data = json.load(f)

    for cve in cve_data:
        archon.add_to_rag(
            source_id=source['id'],
            content=cve['description'],
            metadata={
                "cve_id": cve['id'],
                "cvss_score": cve['cvss'],
                "technology": cve['affected_products']
            }
        )
```

### Phase 3: PydanticAI Agents (3-4 jours)

**Tâches** :
- [ ] Créer [src/classifier_agent.py](src/classifier_agent.py:1)
- [ ] Créer [src/summarizer_agent.py](src/summarizer_agent.py:1)
- [ ] Créer [src/alert_agent.py](src/alert_agent.py:1)
- [ ] Migration progressive depuis ancien code

**Approche de migration** :
```python
# Garder l'ancien code en fallback
from src.classifier import ArticleClassifier as OldClassifier
from src.classifier_agent import classify_with_fallback as new_classify

USE_NEW_AGENT = os.getenv("USE_PYDANTIC_AI", "false").lower() == "true"

def classify_article(article):
    if USE_NEW_AGENT:
        return asyncio.run(new_classify(article))
    else:
        return OldClassifier().classify_article(article)
```

### Phase 4: Archon Integration (2-3 jours)

**Tâches** :
- [ ] Ajouter task management dans [main.py](main.py:1)
- [ ] Créer documents Archon après traitement
- [ ] Implémenter versioning des analyses
- [ ] Créer dashboard Archon pour TechWatchIT

**Modification main.py** :
```python
# main.py (extrait)
from archon_client import ArchonClient

archon = ArchonClient()
PROJECT_ID = os.getenv("ARCHON_PROJECT_ID")

def run_full_pipeline():
    """Pipeline avec tracking Archon"""

    # Créer tâches
    fetch_task = archon.create_task(
        project_id=PROJECT_ID,
        title="Collecter flux RSS",
        status="todo"
    )

    # Exécuter avec tracking
    archon.update_task(fetch_task['id'], status="doing")
    try:
        result = fetch_feeds()
        archon.update_task(fetch_task['id'], status="done")
    except Exception as e:
        archon.update_task(fetch_task['id'], status="todo")
        logger.error(f"Erreur collecte: {e}")

    # Suite du pipeline...
```

### Phase 5: Testing & Documentation (2-3 jours)

**Tâches** :
- [ ] Écrire tests unitaires pour agents
- [ ] Tests d'intégration Archon
- [ ] Mettre à jour [README.md](README.md:1)
- [ ] Créer ARCHITECTURE.md
- [ ] Guide de migration

---

## 🎯 Bénéfices Attendus

| Aspect | Avant | Après | Amélioration |
|--------|-------|-------|--------------|
| **Type Safety** | JSON manuel, erreurs runtime | Pydantic validation | ✅ 100% type-safe |
| **Contexte** | Classification isolée | RAG-enhanced | ✅ +40% précision |
| **Tracking** | Aucun | Tasks Archon | ✅ Visibilité complète |
| **Versioning** | Aucun | Archon versions | ✅ Historique complet |
| **Tests** | Limités | TestModel pytest | ✅ Coverage >80% |
| **Maintenance** | Parsing manuel complexe | Modèles Pydantic | ✅ -50% code |

---

## 🚀 Roadmap

```
Semaine 1: Setup + RAG Database
├─ Jour 1-2: Dependencies, models.py
└─ Jour 3-5: Import CVE, configure RAG

Semaine 2: PydanticAI Agents
├─ Jour 1-2: Classification agent
├─ Jour 3-4: Summarization agent
└─ Jour 5: Alert agent

Semaine 3: Archon Integration
├─ Jour 1-2: Task management
├─ Jour 3-4: Document storage
└─ Jour 5: Dashboard

Semaine 4: Testing & Documentation
├─ Jour 1-2: Unit tests
├─ Jour 3-4: Integration tests
└─ Jour 5: Documentation finale
```

---

## 📚 Ressources

- **PydanticAI Docs** : https://ai.pydantic.dev/
- **Archon MCP** : Déjà configuré dans votre environnement
- **Pydantic V2** : https://docs.pydantic.dev/latest/
- **NVD CVE Database** : https://nvd.nist.gov/developers

---

## ✅ Checklist de Validation

Avant de considérer la migration terminée :

- [ ] Tous les tests passent (pytest)
- [ ] Coverage >80%
- [ ] Classification IA fonctionne avec validation
- [ ] RAG enrichit les classifications
- [ ] Tasks Archon trackent la progression
- [ ] Documents Archon stockent les analyses
- [ ] Versioning fonctionne
- [ ] Fallback mots-clés opérationnel
- [ ] Dashboard Archon accessible
- [ ] Documentation mise à jour
- [ ] Guide de migration créé
- [ ] Performance équivalente ou meilleure

---

**Date de création** : 2025-11-04
**Auteur** : Claude (Assistant IA)
**Statut** : Proposition - En attente de validation
