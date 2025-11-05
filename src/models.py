"""
TechWatchIT - Modèles Pydantic pour validation structurée
Modèles de données utilisés par les agents PydanticAI
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional, List
from datetime import datetime


class TechnologyType(str, Enum):
    """Technologies surveillées par TechWatchIT"""
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
    """Niveaux de sévérité des vulnérabilités"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CategoryType(str, Enum):
    """Catégories d'articles"""
    SECURITY = "security"
    UPDATE = "update"
    VULNERABILITY = "vulnerability"
    PATCH = "patch"
    PRODUCT = "product"
    NEWS = "news"


class ArticleClassification(BaseModel):
    """
    Classification structurée d'un article de veille IT

    Utilisé par l'agent de classification PydanticAI pour garantir
    que toutes les classifications ont une structure cohérente et valide.
    """

    technology: TechnologyType = Field(
        description="Technologie principale concernée par l'article"
    )

    category: CategoryType = Field(
        description="Catégorie de l'article"
    )

    severity_level: SeverityLevel = Field(
        description="Niveau de sévérité (low, medium, high, critical)"
    )

    severity_score: float = Field(
        ge=1.0,
        le=10.0,
        description="Score de sévérité de 1.0 à 10.0"
    )

    cvss_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Score CVSS si mentionné dans l'article"
    )

    is_security_alert: bool = Field(
        description="Indique si l'article est une alerte de sécurité nécessitant une action"
    )

    impact_analysis: str = Field(
        max_length=500,
        description="Analyse de l'impact potentiel pour l'entreprise"
    )

    action_required: str = Field(
        max_length=300,
        description="Action recommandée en réponse à cet article"
    )

    cve_references: List[str] = Field(
        default_factory=list,
        description="Liste des identifiants CVE mentionnés (ex: CVE-2024-1234)"
    )

    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance de la classification (0-1)"
    )

    @field_validator('severity_score')
    @classmethod
    def validate_severity_consistency(cls, v: float, info) -> float:
        """
        Valider la cohérence entre severity_level et severity_score
        Auto-correction si les valeurs sont incohérentes
        """
        severity_level = info.data.get('severity_level')

        if severity_level == SeverityLevel.CRITICAL and v < 8.0:
            return 9.0  # Auto-correction
        elif severity_level == SeverityLevel.HIGH and v < 6.0:
            return 7.0
        elif severity_level == SeverityLevel.MEDIUM and (v < 4.0 or v > 7.0):
            return 5.0
        elif severity_level == SeverityLevel.LOW and v > 4.0:
            return 3.0

        return v

    @field_validator('cve_references')
    @classmethod
    def validate_cve_format(cls, v: List[str]) -> List[str]:
        """Valider le format des CVE (CVE-YYYY-NNNNN)"""
        import re
        cve_pattern = re.compile(r'^CVE-\d{4}-\d{4,}$', re.IGNORECASE)

        valid_cves = []
        for cve in v:
            cve = cve.strip().upper()
            if cve_pattern.match(cve):
                valid_cves.append(cve)

        return valid_cves


class ArticleSummary(BaseModel):
    """
    Résumé structuré d'un article de veille IT

    Généré par l'agent de résumé PydanticAI pour fournir
    une vue condensée mais complète de l'article.
    """

    summary: str = Field(
        max_length=500,
        description="Résumé concis de l'article (max 500 caractères)"
    )

    key_points: List[str] = Field(
        min_length=3,
        max_length=5,
        description="Points clés principaux (3-5 items)"
    )

    business_impact: str = Field(
        max_length=300,
        description="Impact potentiel pour l'entreprise"
    )

    technical_details: str = Field(
        max_length=400,
        description="Détails techniques importants"
    )

    similar_incidents: List[str] = Field(
        default_factory=list,
        description="Incidents ou articles similaires trouvés via RAG"
    )

    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommandations d'action"
    )

    @field_validator('key_points')
    @classmethod
    def validate_key_points_not_empty(cls, v: List[str]) -> List[str]:
        """S'assurer que les points clés ne sont pas vides"""
        return [point.strip() for point in v if point.strip()]


class CriticalAlert(BaseModel):
    """
    Structure d'une alerte critique enrichie

    Utilisé pour les alertes de sécurité critiques avec
    contexte enrichi via RAG.
    """

    article_id: int = Field(description="ID de l'article dans la base MySQL")

    title: str = Field(description="Titre de l'alerte")

    classification: ArticleClassification = Field(
        description="Classification complète de l'article"
    )

    summary: ArticleSummary = Field(
        description="Résumé de l'article"
    )

    urgency_level: str = Field(
        description="Niveau d'urgence: immediate, high, medium"
    )

    affected_systems: List[str] = Field(
        default_factory=list,
        description="Systèmes potentiellement affectés"
    )

    rag_context: Optional[str] = Field(
        None,
        description="Contexte additionnel depuis la base RAG CVE"
    )

    similar_cves: List[dict] = Field(
        default_factory=list,
        description="CVE similaires trouvés via RAG"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création de l'alerte"
    )


class RAGSearchResult(BaseModel):
    """Résultat d'une recherche RAG"""

    content: str = Field(description="Contenu trouvé")

    similarity: float = Field(
        ge=0.0,
        le=1.0,
        description="Score de similarité"
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )

    source: str = Field(
        default="",
        description="Source de l'information"
    )


class ProcessingResult(BaseModel):
    """Résultat du traitement complet d'un article"""

    article_id: int = Field(description="ID de l'article")

    classification: ArticleClassification = Field(
        description="Classification de l'article"
    )

    summary: ArticleSummary = Field(
        description="Résumé de l'article"
    )

    processing_time_seconds: float = Field(
        ge=0.0,
        description="Temps de traitement en secondes"
    )

    success: bool = Field(
        default=True,
        description="Indique si le traitement a réussi"
    )

    error_message: Optional[str] = Field(
        None,
        description="Message d'erreur si le traitement a échoué"
    )

    processed_at: datetime = Field(
        default_factory=datetime.now,
        description="Date et heure du traitement"
    )


# Exemples de validation pour tests
if __name__ == "__main__":
    # Test de création d'une classification
    classification = ArticleClassification(
        technology=TechnologyType.FORTINET,
        category=CategoryType.VULNERABILITY,
        severity_level=SeverityLevel.CRITICAL,
        severity_score=9.5,
        cvss_score=9.8,
        is_security_alert=True,
        impact_analysis="Vulnérabilité critique dans FortiOS permettant l'exécution de code à distance",
        action_required="Appliquer immédiatement le patch de sécurité",
        cve_references=["CVE-2024-12345", "CVE-2024-12346"]
    )

    print("✅ Classification validée:")
    print(classification.model_dump_json(indent=2))

    # Test de validation auto-correction
    classification_bad = ArticleClassification(
        technology=TechnologyType.VMWARE,
        category=CategoryType.SECURITY,
        severity_level=SeverityLevel.CRITICAL,
        severity_score=5.0,  # Incohérent avec CRITICAL
        is_security_alert=True,
        impact_analysis="Test",
        action_required="Test",
        cve_references=["cve-2024-99999", "invalid-cve"]  # Un valide, un invalide
    )

    print("\n✅ Auto-correction appliquée:")
    print(f"Score corrigé: {classification_bad.severity_score} (devrait être >= 8.0)")
    print(f"CVE filtrés: {classification_bad.cve_references} (invalides supprimés)")
