# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TechWatchIT is an IT security monitoring platform built in Python that aggregates RSS feeds, classifies articles using AI, and provides automated alerts. The system is designed to run on Windows with WAMP server (MySQL) and integrates with OpenAI for content classification and summarization.

## Common Development Commands

### Setup and Installation
```bash
# Windows setup script (creates venv, installs deps, initializes DB)
setup.bat

# Manual setup alternative
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Database Operations
```bash
# Initialize database schema
python scripts/setup_db.py

# Test MySQL connection
python scripts/test_mysql.py

# Test specific components
python check_mysql.py
python check_openai.py
```

### Main Application Commands
```bash
# Initialize database
python main.py --init

# Fetch RSS feeds only
python main.py --fetch

# Process articles with AI
python main.py --process

# Send daily digest
python main.py --digest

# Check critical alerts
python main.py --alerts

# Run complete pipeline (fetch + process + alerts)
python main.py --pipeline

# Show system status
python main.py --status

# Launch web API and dashboard
python main.py --api
```

### Development and Testing
```bash
# Code formatting
black src/ config/ scripts/

# Linting
flake8 src/ config/ scripts/

# Run tests (if available)
pytest tests/

# Start web server for development
python src/api.py
```

## Architecture Overview

### Core Components
- **main.py**: Main orchestrator with CLI interface for all operations
- **config/config.py**: Centralized configuration management with RSS feeds definitions
- **src/database.py**: MySQL database manager with connection pooling
- **src/fetch_feeds.py**: RSS/JSON feed collector with error handling
- **src/classifier.py**: AI-powered article classification (OpenAI GPT-4o)
- **src/summarizer.py**: Intelligent article summarization
- **src/api.py**: Flask REST API with dashboard endpoints

### Database Schema (MySQL)
- **raw_articles**: Original RSS feed articles
- **processed_articles**: AI-classified and summarized articles  
- **rss_sources**: RSS feed source configurations
- **fetch_log**: Collection history and statistics
- **alert_notifications**: Alert delivery tracking
- **daily_stats**: Aggregated daily statistics

### Technology Stack
- **Backend**: Python 3.12+ with Flask/Flask-CORS
- **Database**: MySQL via PyMySQL (WAMP environment)
- **AI Integration**: OpenAI API (GPT-4o-mini for cost efficiency)
- **Web Frontend**: Bootstrap 5 responsive dashboard
- **Email**: SMTP (Office 365 configuration)
- **Dependencies**: feedparser, beautifulsoup4, requests, python-dotenv

### RSS Sources Monitored
The system monitors security-focused sources including:
- Official vendor advisories (Fortinet, VMware, Dell, Microsoft)
- Security research blogs (SentinelOne, Rapid7, Malwarebytes)
- Threat intelligence feeds (SANS ISC, US-CERT, CISA)
- Vulnerability databases (Exploit-DB, NVD alternatives)
- Enterprise security (Rubrik, JumpCloud)

## Configuration Management

### Environment Variables (.env)
Key configuration items that must be set:
- `OPENAI_API_KEY`: Required for AI classification and summarization
- `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE`: MySQL connection parameters
- `SMTP_USERNAME/PASSWORD/SERVER`: Email notification configuration
- `API_HOST/PORT`: Web API server configuration
- `ALERT_RECIPIENTS`: Comma-separated email list for critical alerts

### RSS Feed Configuration
RSS feeds are defined in `config/config.py` under `RSS_FEEDS` dictionary. Each feed includes:
- name, url, category, technology, description
- Technology classification (exploits, fortinet, vmware, etc.)
- Priority and categorization for processing

## Development Patterns

### Error Handling
All network operations should include comprehensive error handling:
```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    self.logger.error(f"Network error for {source}: {str(e)}")
    return []
```

### Database Operations
Use context manager for MySQL connections:
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM raw_articles")
    results = cursor.fetchall()
```

### Logging Standards
- Use `Config.setup_logging()` for consistent logging setup
- Log levels: INFO (normal operations), WARNING (data issues), ERROR (failures), CRITICAL (security alerts)
- All logs saved to `logs/app.log` with UTF-8 encoding

### AI Integration
- Primary: OpenAI GPT-4o-mini for cost-effective classification
- Fallback: Keyword-based classification using `TECH_KEYWORDS`
- Classification includes: technology, severity, impact score, CVSS rating
- Summarization: Generate ≤6 sentence TL;DR with actionable insights

## Testing and Quality

### Code Standards
- Follow Black formatting (88 character line limit)
- Use Google-style docstrings for public functions
- Snake_case for functions/variables, PascalCase for classes
- Type hints where appropriate

### Testing Approach
- Test individual components: `python scripts/test_mysql.py`, `python scripts/test_openai.py`
- Manual integration testing via main.py commands
- Validate data integrity after operations

## Deployment Notes

### WAMP Environment Requirements
- Windows environment with WAMP server installed
- MySQL service running (green icon in WAMP tray)
- PHP/phpMyAdmin accessible for database management
- Port 3306 available for MySQL connections

### File Structure Expectations
- `logs/` directory for application logs
- `data/` directory for temporary data storage
- `web/` directory contains dashboard HTML templates
- Virtual environment in `venv/` directory

### Security Considerations
- No hardcoded API keys or passwords
- Use environment variables for all sensitive configuration
- Input validation on all external data (RSS feeds, user input)
- Timeout limits on all network requests

## Common Issues and Solutions

### MySQL Connection Failures
- Verify WAMP server is running (green tray icon)
- Check MySQL service status in WAMP interface
- Test with: `python scripts/test_mysql.py`
- Ensure firewall allows port 3306

### OpenAI API Issues
- Verify API key in .env file
- Check quota limits on OpenAI platform
- Test with: `python scripts/test_openai.py`
- System falls back to keyword classification if API fails

### RSS Feed Collection Issues
- Individual feed failures don't stop the entire process
- Check logs for specific feed error messages
- Validate feed URLs manually if needed
- Network timeouts are set to 30 seconds per feed