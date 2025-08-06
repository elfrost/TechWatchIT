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

# Configuration des flux RSS de départ
RSS_FEEDS = {
    # === SOURCES OFFICIELLES DE SÉCURITÉ ===
    "defend_edge": {
        "name": "Defend Edge Vulnerability Summaries",
        "url": "https://www.defendedge.com/feed/",
        "category": "Official Security Advisory",
        "technology": "exploits",
        "description": "Weekly vulnerability summaries and security advisories"
    },
    "nvd_alternative": {
        "name": "Alternative CVE Feed",
        "url": "https://open-source-security-software.net/cves.atom",
        "category": "Vulnerability Database",
        "technology": "exploits",
        "description": "Alternative feed for recent CVE vulnerabilities"
    },
    "sans_isc": {
        "name": "SANS Internet Storm Center",
        "url": "https://isc.sans.edu/rssfeed.xml",
        "category": "Security Alert",
        "technology": "exploits",
        "description": "SANS ISC threat intelligence and security alerts"
    },
    
    # === SOURCES SPÉCIALISÉES EXPLOITS ===
    "exploit_db": {
        "name": "Exploit Database",
        "url": "https://www.exploit-db.com/rss.xml",
        "category": "Exploit Database",
        "technology": "exploits",
        "description": "Latest exploits and proof-of-concept code"
    },
    "rapid7_blog": {
        "name": "Rapid7 Security Blog",
        "url": "https://blog.rapid7.com/rss/",
        "category": "Security Research",
        "technology": "exploits",
        "description": "Rapid7 vulnerability research and security intelligence"
    },
    "tenable_blog": {
        "name": "Tenable Security Blog",
        "url": "https://www.tenable.com/blog/rss.xml",
        "category": "Security Research",
        "technology": "exploits",
        "description": "Tenable vulnerability research and security analysis"
    },
    
    # === SOURCES THREAT INTELLIGENCE ===
    "cyware_alerts": {
        "name": "Cyware Threat Intelligence",
        "url": "https://cyware.com/rss/threat-briefings",
        "category": "Threat Intelligence",
        "technology": "exploits",
        "description": "Daily threat intelligence and security briefings"
    },
    "bleeping_computer": {
        "name": "Bleeping Computer Security",
        "url": "https://www.bleepingcomputer.com/feed/",
        "category": "Security News",
        "technology": "exploits",
        "description": "Breaking security news and vulnerability reports"
    },
    "krebs_security": {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "Security Investigation",
        "technology": "exploits",
        "description": "In-depth security investigations and breach reports"
    },
    "dark_reading": {
        "name": "Dark Reading",
        "url": "https://www.darkreading.com/rss/all.xml",
        "category": "Security Analysis",
        "technology": "exploits",
        "description": "Enterprise security news and analysis"
    },
    
    # === NOUVELLES SOURCES FIABLES ===
    "the_hacker_news": {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "category": "Security News",
        "technology": "exploits",
        "description": "Latest hacking news and cybersecurity updates"
    },
    "security_affairs": {
        "name": "Security Affairs",
        "url": "https://securityaffairs.com/feed",
        "category": "Security News",
        "technology": "exploits",
        "description": "Information security and cybersecurity news"
    },
    "threatpost": {
        "name": "Threatpost",
        "url": "https://threatpost.com/feed/",
        "category": "Threat Intelligence",
        "technology": "exploits",
        "description": "Independent news source for cybersecurity threats"
    },
    
    # === SOURCES CONSTRUCTEURS (AMÉLIORÉES) ===
    "fortinet": {
        "name": "Fortinet PSIRT",
        "url": "https://www.fortiguard.com/rss/ir.xml",
        "category": "Security Advisory",
        "technology": "fortinet",
        "description": "Fortinet Product Security Incident Response Team advisories"
    },
    "vmware_security": {
        "name": "VMware Security Advisories",
        "url": "https://www.vmware.com/security/advisories.xml",
        "category": "Security Advisory",
        "technology": "vmware",
        "description": "VMware security advisories and vulnerability reports"
    },
    "dell_security": {
        "name": "Dell Security Advisory",
        "url": "https://www.dell.com/support/security/rss.xml",
        "category": "Security Advisory",
        "technology": "dell",
        "description": "Dell security advisories and product updates"
    },
    "microsoft_security": {
        "name": "Microsoft Security Updates",
        "url": "https://www.microsoft.com/security/blog/feed/",
        "category": "Security Update",
        "technology": "microsoft",
        "description": "Microsoft security updates and vulnerability research"
    },
    

    
    # === SOURCES ENTREPRISE ===
    "sentinelone": {
        "name": "SentinelOne Security Research",
        "url": "https://www.sentinelone.com/feed/",
        "category": "Security Research",
        "technology": "sentinelone",
                "description": "SentinelOne cybersecurity research and threat intelligence"
    },
    "rubrik_blog": {
        "name": "Rubrik Security Blog",
        "url": "https://www.rubrik.com/blog/feed/",
        "category": "Data Security",
        "technology": "rubrik",
        "description": "Rubrik data security and cyber recovery insights"
    },
    "jumpcloud_blog": {
        "name": "JumpCloud Security Blog",
        "url": "https://jumpcloud.com/blog/feed/",
        "category": "Identity Security",
        "technology": "jumpcloud",
        "description": "JumpCloud identity and access management security insights"
    },
    
    # === SOURCES ANALYSE MALWARE ===
    "malwarebytes_labs": {
        "name": "Malwarebytes Labs",
        "url": "https://www.malwarebytes.com/blog/feed/",
        "category": "Malware Analysis",
        "technology": "exploits",
        "description": "Malware analysis and threat research"
    },
    
    # === SOURCES GOUVERNEMENTALES ===
    "us_cert": {
        "name": "US-CERT Current Activity",
        "url": "https://www.cisa.gov/uscert/ncas/current-activity.xml",
        "category": "Government Advisory",
        "technology": "exploits",
        "description": "US-CERT current security activities and alerts"
    },
    "cisa_advisories": {
        "name": "CISA Security Advisories",
        "url": "https://www.cisa.gov/uscert/ncas/alerts.xml",
        "category": "Government Advisory",
        "technology": "exploits",
        "description": "CISA security advisories and alerts"
    }
}

# Mots-clés pour la classification fallback (AMÉLIORÉS)
TECH_KEYWORDS = {
    "exploits": [
        "exploit", "vulnerability", "cve", "zero-day", "malware", "ransomware", 
        "backdoor", "trojan", "botnet", "apt", "breach", "attack", "compromise",
        "phishing", "injection", "overflow", "privilege escalation", "rce",
        "remote code execution", "denial of service", "dos", "ddos", "critical",
        "patch", "security advisory", "threat", "campaign", "actor", "attribution"
    ],
    "fortinet": ["fortinet", "fortigate", "fortios", "fortianalyzer", "fortimanager", "fortimail", "fortiweb"],
    "vmware": ["vmware", "vcenter", "vsphere", "esxi", "vsan", "nsx", "horizon", "workstation"],
    "dell": ["dell", "emc", "poweredge", "idrac", "openmanage", "data domain", "unity"],
    "microsoft": ["microsoft", "windows", "office", "exchange", "sharepoint", "azure", "active directory"],
        "sentinelone": ["sentinelone", "sentinel one", "s1", "endpoint protection", "edr"],
    "rubrik": ["rubrik", "data protection", "backup", "cyber recovery", "zero trust data security"],
    "jumpcloud": ["jumpcloud", "jump cloud", "identity", "directory service", "ldap", "sso", "single sign-on"],
    "ransomware": [
        "ransomware", "crypto", "encryption", "ransom", "lockbit", "conti", "maze",
        "ryuk", "sodinokibi", "revil", "darkside", "blackmatter", "hive", "royal"
    ],
    "malware": [
        "malware", "virus", "worm", "spyware", "adware", "rootkit", "keylogger",
        "stealer", "loader", "dropper", "rat", "remote access", "c2", "command control"
    ]
} 