"""
Test de la séparation par contextes métier
"""

from src.models import (
    ArticleClassification,
    TechnologyType,
    SeverityLevel,
    CategoryType,
    ContextType,
    determine_context
)

print("=" * 60)
print("TEST: Separation par Contextes Metier")
print("=" * 60)

# Test 1: Veille Technologique
print("\n[TEST 1] Veille Technologique")
print("-" * 60)
classification1 = ArticleClassification(
    technology=TechnologyType.FORTINET,
    category=CategoryType.PRODUCT,
    severity_level=SeverityLevel.LOW,
    severity_score=3.0,
    is_security_alert=False,
    impact_analysis="Nouvelle release FortiOS 7.4.5",
    action_required="Evaluer la mise a jour",
    cve_references=[]
)
context1 = determine_context(classification1)
print(f"Technology: {classification1.technology.value}")
print(f"Category: {classification1.category.value}")
print(f"Severity: {classification1.severity_level.value}")
print(f"CVE: {classification1.cve_references}")
print(f"=> CONTEXTE: {context1.value}")
assert context1 == ContextType.VEILLE_TECHNO, f"Expected VEILLE_TECHNO, got {context1.value}"
print("[OK] Contexte correct: VEILLE_TECHNO")

# Test 2: CVE et Vulnerabilites
print("\n[TEST 2] CVE et Vulnerabilites")
print("-" * 60)
classification2 = ArticleClassification(
    technology=TechnologyType.VMWARE,
    category=CategoryType.VULNERABILITY,
    severity_level=SeverityLevel.HIGH,
    severity_score=8.5,
    is_security_alert=True,
    impact_analysis="Vulnerabilite critique dans vCenter",
    action_required="Appliquer le patch immediatement",
    cve_references=["CVE-2024-12345"]
)
context2 = determine_context(classification2)
print(f"Technology: {classification2.technology.value}")
print(f"Category: {classification2.category.value}")
print(f"Severity: {classification2.severity_level.value}")
print(f"CVE: {classification2.cve_references}")
print(f"=> CONTEXTE: {context2.value}")
assert context2 == ContextType.CVE_VULNERABILITES, f"Expected CVE_VULNERABILITES, got {context2.value}"
print("[OK] Contexte correct: CVE_VULNERABILITES")

# Test 3: Exploits et Menaces
print("\n[TEST 3] Exploits et Menaces")
print("-" * 60)
classification3 = ArticleClassification(
    technology=TechnologyType.EXPLOITS,
    category=CategoryType.SECURITY,
    severity_level=SeverityLevel.CRITICAL,
    severity_score=9.5,
    is_security_alert=True,
    impact_analysis="Nouveau ransomware actif",
    action_required="Alerter l'equipe securite",
    cve_references=[]
)
context3 = determine_context(classification3)
print(f"Technology: {classification3.technology.value}")
print(f"Category: {classification3.category.value}")
print(f"Severity: {classification3.severity_level.value}")
print(f"CVE: {classification3.cve_references}")
print(f"=> CONTEXTE: {context3.value}")
assert context3 == ContextType.EXPLOITS_MENACES, f"Expected EXPLOITS_MENACES, got {context3.value}"
print("[OK] Contexte correct: EXPLOITS_MENACES")

# Test 4: Actualites IT
print("\n[TEST 4] Actualites IT")
print("-" * 60)
classification4 = ArticleClassification(
    technology=TechnologyType.OTHER,
    category=CategoryType.NEWS,
    severity_level=SeverityLevel.LOW,
    severity_score=3.0,
    is_security_alert=False,
    impact_analysis="Tendances cloud computing 2025",
    action_required="Information generale",
    cve_references=[]
)
context4 = determine_context(classification4)
print(f"Technology: {classification4.technology.value}")
print(f"Category: {classification4.category.value}")
print(f"Severity: {classification4.severity_level.value}")
print(f"CVE: {classification4.cve_references}")
print(f"=> CONTEXTE: {context4.value}")
assert context4 == ContextType.ACTUALITES_IT, f"Expected ACTUALITES_IT, got {context4.value}"
print("[OK] Contexte correct: ACTUALITES_IT")

# Test 5: Alert critique Microsoft -> Exploits/Menaces
print("\n[TEST 5] Alerte Critique (Microsoft) -> Exploits/Menaces")
print("-" * 60)
classification5 = ArticleClassification(
    technology=TechnologyType.MICROSOFT,
    category=CategoryType.SECURITY,
    severity_level=SeverityLevel.CRITICAL,
    severity_score=9.8,
    is_security_alert=True,
    impact_analysis="Zero-day exploite activement",
    action_required="Action immediate",
    cve_references=["CVE-2024-99999"]
)
context5 = determine_context(classification5)
print(f"Technology: {classification5.technology.value}")
print(f"Category: {classification5.category.value}")
print(f"Severity: {classification5.severity_level.value}")
print(f"CVE: {classification5.cve_references}")
print(f"=> CONTEXTE: {context5.value}")
assert context5 == ContextType.EXPLOITS_MENACES, f"Expected EXPLOITS_MENACES, got {context5.value}"
print("[OK] Contexte correct: EXPLOITS_MENACES (critical alert)")

# Résumé
print("\n" + "=" * 60)
print("RESULTAT: Tous les tests passent avec succes!")
print("=" * 60)
print("\nRepartition des contextes:")
print(f"  1. Veille Techno: {ContextType.VEILLE_TECHNO.value}")
print(f"  2. CVE Vulnerabilites: {ContextType.CVE_VULNERABILITES.value}")
print(f"  3. Exploits Menaces: {ContextType.EXPLOITS_MENACES.value}")
print(f"  4. Actualites IT: {ContextType.ACTUALITES_IT.value}")
