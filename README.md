# TechWatchIT 🔍

**Business-Focused Technology Monitoring Platform**

Centralized IT monitoring platform for Windows with RSS feed aggregation, AI-powered classification, and automated security alerts. Designed specifically for business technology stacks with **CVE priority**.

## 🎯 Purpose

Monitor your actual business technologies for:
- **Critical security vulnerabilities (CVE)**
- **Product updates and patches**  
- **Security advisories and threats**
- **Technology-specific news and changes**

## 🏢 Supported Technologies

### 🚨 Security & CVE (Priority)
- **CISA** - Government security alerts
- **SANS ISC** - Threat intelligence  
- **Security News** - Latest vulnerabilities

### 💼 Business Technology Stack
- **Office 365** - Microsoft 365 updates and security
- **Windows** - Server/desktop security patches
- **SentinelOne** - Endpoint detection and response
- **JumpCloud** - Identity and access management
- **VMware** - Virtualization platform updates
- **Red Hat / Rocky Linux** - Enterprise Linux distributions

## 🚀 Quick Start

### Prerequisites
- **Windows** with WAMP server (MySQL active)
- **Python 3.11+** installed
- **OpenAI API Key** for AI classification
- **SMTP credentials** for email alerts (optional)

### One-Click Installation & Launch
```bash
# Clone the repository
git clone https://github.com/elfrost/TechWatchIT.git
cd TechWatchIT

# Run the program (handles everything automatically)
run_techwatchit.bat
```

The BAT file will:
1. ✅ Check Python installation
2. 📦 Create virtual environment 
3. 📋 Install dependencies
4. ⚙️ Setup configuration
5. 🚀 Launch interactive menu

## 📋 Features

### 🔄 Automated RSS Collection
- **12 curated sources** (100% functional)
- **Business-focused technologies**
- **CVE priority monitoring**
- **Automatic duplicate detection**

### 🤖 AI-Powered Analysis
- **OpenAI GPT-4o classification** 
- **Technology-specific categorization**
- **Keyword fallback system**
- **Smart summarization**

### 📊 Professional Storage
- **MySQL database** (WAMP integration)
- **Structured data schema**
- **Historical tracking**
- **Performance statistics**

### 🌐 Web Dashboard
- **Bootstrap 5 responsive interface**
- **Real-time filtering by technology**
- **CVE priority highlighting**
- **Export capabilities**

### 📧 Alert System
- **Critical CVE notifications**
- **Daily digest emails**
- **SMTP integration**
- **Customizable thresholds**

## ⚙️ Configuration

### Environment Variables (.env)
```env
# OpenAI API for AI classification/summaries
OPENAI_API_KEY=your_openai_api_key_here

# MySQL Configuration (WAMP)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=techwatchit

# SMTP Configuration (Optional)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your_email@company.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME=TechWatchIT Alert System

# Alert Configuration
ALERT_THRESHOLD_CVSS=9.0
ALERT_RECIPIENTS=admin@company.com,security@company.com
DAILY_DIGEST_TIME=08:00

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
```

## 🎮 Usage

### Interactive Menu (Recommended)
```bash
run_techwatchit.bat
```

### Command Line Interface
```bash
# Complete pipeline (fetch + process + alerts)
python main.py --pipeline

# Individual operations
python main.py --init            # Initialize database
python main.py --fetch           # Fetch RSS feeds
python main.py --process         # Process with AI
python main.py --digest          # Send daily digest
python main.py --alerts          # Check critical alerts
python main.py --status          # System status
python main.py --api             # Launch web dashboard
```

### Web Dashboard
```
http://localhost:5000
```

## 📁 Project Structure

```
TechWatchIT/
├── config/
│   ├── __init__.py
│   └── config.py                 # Centralized configuration
├── src/
│   ├── __init__.py
│   ├── api.py                    # Flask REST API
│   ├── classifier.py             # AI classification
│   ├── database.py               # MySQL manager
│   ├── fetch_feeds.py            # RSS collector
│   └── summarizer.py             # AI summarization
├── scripts/
│   ├── alert_handler.py          # Critical alerts
│   ├── daily_digest.py           # Email digest
│   ├── setup_db.py               # Database setup
│   ├── test_mysql.py             # MySQL test
│   └── test_openai.py            # OpenAI test
├── web/
│   ├── dashboard.html            # Main interface
│   └── blog_dashboard.html       # Blog interface
├── main.py                       # Main orchestrator
├── run_techwatchit.bat          # One-click launcher
├── requirements.txt              # Python dependencies
├── setup.bat                     # Manual setup
├── env.example                   # Environment template
└── README.md                     # This file
```

## 🔧 Advanced Configuration

### Adding New RSS Sources
Edit `config/config.py`:
```python
RSS_FEEDS = {
    "new_source": {
        "name": "Source Name",
        "url": "https://example.com/rss.xml",
        "category": "Security Update",
        "technology": "your_tech",
        "description": "Source description"
    }
}
```

### Technology Keywords
Customize classification in `config/config.py`:
```python
TECH_KEYWORDS = {
    "your_tech": [
        "keyword1", "keyword2", "product-name", 
        "vulnerability-type", "specific-terms"
    ]
}
```

## 📊 Database Schema

### Core Tables
- **raw_articles** - Original RSS feed data
- **processed_articles** - AI-classified content
- **rss_sources** - Feed source management
- **fetch_log** - Collection history
- **alert_notifications** - Alert tracking
- **daily_stats** - Performance metrics

### Access Database
```
http://localhost/phpmyadmin
User: root
Password: (empty)
Database: techwatchit
```

## 🔐 Security Best Practices

### API Keys
- Store in `.env` file only
- Never commit to version control
- Use environment-specific keys
- Rotate keys regularly

### Database Security
- Use strong MySQL passwords in production
- Restrict database access
- Regular backups
- Monitor access logs

### Network Security
- Configure firewall rules
- Use HTTPS in production
- Restrict API access
- Monitor traffic patterns

## 🧪 Testing

### System Tests
```bash
# Test MySQL connection
python scripts/test_mysql.py

# Test OpenAI API
python scripts/test_openai.py

# System status check
python main.py --status
```

### RSS Source Validation
All configured sources are automatically tested for:
- HTTP connectivity (200 status)
- Valid RSS/XML format
- Content availability
- Article structure

## 🚨 Troubleshooting

### Common Issues

#### MySQL Connection Failed
```
✅ Check WAMP server status (green icon)
✅ Verify MySQL service is running
✅ Test: python scripts/test_mysql.py
✅ Check firewall on port 3306
```

#### OpenAI API Errors
```
✅ Verify API key in .env file
✅ Check quota limits on OpenAI platform
✅ Test: python scripts/test_openai.py
✅ System uses keyword fallback if API fails
```

#### RSS Feed Failures
```
✅ Individual feed failures don't stop processing
✅ Check logs for specific error messages
✅ Validate feed URLs manually
✅ Network timeouts set to 30 seconds per feed
```

#### Unicode Display Errors (Windows)
```
✅ Set console to UTF-8: chcp 65001
✅ Use Windows Terminal instead of Command Prompt
✅ Some emojis may not display correctly in older terminals
```

## 📈 Performance Expectations

### Collection Metrics
- **RSS Sources**: 12 sources (100% functional)
- **Articles per cycle**: ~170 articles
- **Processing time**: < 5 minutes/complete pipeline
- **Success rate**: 100% (verified sources)

### Resource Usage
- **Memory**: ~200MB during processing
- **Storage**: ~10MB/month (database growth)
- **API calls**: ~50-100 OpenAI requests/cycle
- **Network**: ~5MB download/cycle

## 🤝 Contributing

### Feature Requests
1. **Technology coverage** - Request new RSS sources
2. **Classification improvement** - Suggest keyword additions
3. **Alert enhancements** - Custom notification rules
4. **Dashboard features** - UI/UX improvements

### Issue Reporting
Include:
- Operating system version
- Python version
- Error messages/logs
- Steps to reproduce
- Expected vs actual behavior

## 📝 License

MIT License - See LICENSE file for details

## 🆘 Support

### Documentation
- **CLAUDE.md** - Claude Code integration guide
- **BUSINESS_CONFIG.md** - Business technology focus
- **Logs directory** - Detailed operation logs

### Community
- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - General questions and sharing

### Professional Support
For enterprise deployments, custom integrations, or professional support, please contact through GitHub.

---

**TechWatchIT** - Professional IT monitoring for your business technologies 🚀