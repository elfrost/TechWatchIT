"""
TechWatchIT - Configuration centralisée
Gestion des variables d'environnement et paramètres du système
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Chargement du fichier .env
load_dotenv()

class Config:
    """Configuration principale de TechWatchIT"""
    
    # Chemins de base
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    WEB_DIR = BASE_DIR / "web"
    
    # Configuration OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Économique pour tests
    OPENAI_MODEL_CLASSIFIER = os.getenv("OPENAI_MODEL_CLASSIFIER", "gpt-4o-mini")
    OPENAI_MODEL_SUMMARIZER = os.getenv("OPENAI_MODEL_SUMMARIZER", "gpt-4o-mini")
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 1000))
    
    # Alternatives recommandées :
    # - gpt-4o-mini : $0.025/semaine (~60 articles) - Idéal pour tests
    # - gpt-4.1-mini : $0.066/semaine - Meilleur rapport qualité/prix
    # - gpt-4.1 : $0.330/semaine - Qualité entreprise
    
    # Configuration base de données SQLite (fallback)
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "database.db"))
    
    # Configuration MySQL pour WAMP
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "techwatchit")
    
    # Configuration API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")  # Écoute sur toutes les interfaces
    API_PORT = int(os.getenv("API_PORT", 5000))
    API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"
    
    # Configuration SMTP
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "TechWatchIT Alert System")
    
    # Configuration des alertes
    ALERT_THRESHOLD_CVSS = float(os.getenv("ALERT_THRESHOLD_CVSS", 9.0))
    DAILY_DIGEST_TIME = os.getenv("DAILY_DIGEST_TIME", "08:00")
    ALERT_RECIPIENTS = os.getenv("ALERT_RECIPIENTS", "").split(",")
    
    # Configuration logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))
    
    # Configuration des flux RSS
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 3600))  # 1 heure
    MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", 50))
    
    # Configuration serveur web
    WEB_SERVER_HOST = os.getenv("WEB_SERVER_HOST", "localhost")
    WEB_SERVER_PORT = int(os.getenv("WEB_SERVER_PORT", 8080))
    
    @classmethod
    def setup_directories(cls):
        """Créer les répertoires nécessaires s'ils n'existent pas"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.WEB_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def setup_logging(cls):
        """Configuration du système de logs"""
        cls.setup_directories()
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger('TechWatchIT')

# Configuration des flux RSS - Technologies Business (validées)
RSS_FEEDS = {
    # === CVE ET ALERTES SÉCURITÉ (PRIORITÉ MAXIMALE) ===
    "cisa_current": {
        "name": "CISA Current Activity", 
        "url": "https://www.cisa.gov/uscert/ncas/current-activity.xml",
        "category": "CVE Alert",
        "technology": "cve",
        "description": "CISA current security activities and vulnerability alerts"
    },
    "cisa_advisories": {
        "name": "CISA Security Advisories",
        "url": "https://www.cisa.gov/uscert/ncas/alerts.xml", 
        "category": "CVE Alert",
        "technology": "cve",
        "description": "CISA critical security advisories and alerts"
    },
    "sans_isc": {
        "name": "SANS Internet Storm Center",
        "url": "https://isc.sans.edu/rssfeed.xml",
        "category": "CVE Alert", 
        "technology": "cve",
        "description": "SANS ISC threat intelligence and security alerts"
    },
    "the_hacker_news": {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "category": "Security News",
        "technology": "cve", 
        "description": "Latest hacking news and vulnerability reports"
    },
    
    # === TECHNOLOGIES BUSINESS UTILISÉES ===
    "microsoft_office365": {
        "name": "Microsoft 365 Blog",
        "url": "https://www.microsoft.com/en-us/microsoft-365/blog/feed/",
        "category": "Product Update",
        "technology": "office365",
        "description": "Microsoft Office 365 updates and announcements"
    },
    "microsoft_security": {
        "name": "Microsoft Security Blog",
        "url": "https://www.microsoft.com/security/blog/feed/",
        "category": "Security Update", 
        "technology": "windows",
        "description": "Microsoft security updates for Windows and Office"
    },
    "sentinelone": {
        "name": "SentinelOne Blog",
        "url": "https://www.sentinelone.com/feed/",
        "category": "Endpoint Security",
        "technology": "sentinelone", 
        "description": "SentinelOne endpoint security research and updates"
    },
    "jumpcloud_main": {
        "name": "JumpCloud Blog",
        "url": "https://jumpcloud.com/blog/feed/",
        "category": "Identity Management",
        "technology": "jumpcloud",
        "description": "JumpCloud directory service and IAM updates"
    },
    "jumpcloud_resources": {
        "name": "JumpCloud Resources",
        "url": "https://jumpcloud.com/resources/feed/",
        "category": "Identity Management", 
        "technology": "jumpcloud",
        "description": "JumpCloud technical resources and guides"
    },
    "vmware_blogs": {
        "name": "VMware Blogs",
        "url": "https://blogs.vmware.com/feed/",
        "category": "Virtualization",
        "technology": "vmware",
        "description": "VMware product updates and technical articles"
    },
    "redhat_blog": {
        "name": "Red Hat Blog", 
        "url": "https://www.redhat.com/en/rss/blog",
        "category": "Linux Enterprise",
        "technology": "redhat",
        "description": "Red Hat enterprise Linux and OpenShift updates"
    },
    "rocky_linux": {
        "name": "Rocky Linux News",
        "url": "https://rockylinux.org/rss.xml",
        "category": "Linux Distribution",
        "technology": "rocky_linux", 
        "description": "Rocky Linux distribution news and updates"
    }
}

# Mots-clés pour classification - Technologies Business
TECH_KEYWORDS = {
    # CVE et sécurité générale (priorité maximale)
    "cve": [
        "cve-", "vulnerability", "exploit", "zero-day", "critical", "high severity",
        "security advisory", "patch", "update", "hotfix", "security bulletin",
        "remote code execution", "privilege escalation", "denial of service",
        "authentication bypass", "information disclosure", "buffer overflow"
    ],
    
    # Technologies utilisées dans le business
    "office365": [
        "office 365", "microsoft 365", "m365", "o365", "exchange online",
        "sharepoint online", "teams", "outlook", "onedrive", "power platform",
        "defender for office", "purview", "compliance center"
    ],
    "windows": [
        "windows server", "windows 10", "windows 11", "active directory",
        "domain controller", "group policy", "powershell", "hyper-v",
        "windows security", "defender", "wsus", "azure ad"
    ],
    "sentinelone": [
        "sentinelone", "sentinel one", "s1", "endpoint detection", "edr",
        "xdr", "autonomous security", "behavioral ai", "rollback", "threat hunting"
    ],
    "jumpcloud": [
        "jumpcloud", "jump cloud", "directory service", "ldap", "radius",
        "sso", "single sign-on", "identity management", "zero trust",
        "device management", "policy management"
    ],
    "vmware": [
        "vmware", "vsphere", "vcenter", "esxi", "vsan", "nsx", "horizon",
        "workstation", "fusion", "vrealize", "cloud director", "tanzu"
    ],
    "fortinet": [
        "fortinet", "fortigate", "fortiswitch", "fortiap", "fortiwifi",
        "fortios", "fortianalyzer", "fortimanager", "fortiguard", "ssl vpn"
    ],
    "dell": [
        "dell", "poweredge", "idrac", "openmanage", "equallogic", "compellent",
        "dell emc", "unity", "powerstore", "data domain", "avamar"
    ],
    "redhat": [
        "red hat", "redhat", "rhel", "centos", "fedora", "openshift",
        "ansible", "satellite", "jboss", "middleware", "container platform"
    ],
    "rocky_linux": [
        "rocky linux", "rocky", "enterprise linux", "centos alternative",
        "rhel compatible", "alma linux", "oracle linux"
    ],
    "rubrik": [
        "rubrik", "backup", "data protection", "cyber recovery", "zero trust",
        "immutable backup", "ransomware recovery", "cloud data management"
    ]
} 