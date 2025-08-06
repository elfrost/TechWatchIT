@echo off
echo.
echo ========================================
echo    TechWatchIT - Configuration automatique
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: Python n'est pas installé ou n'est pas dans le PATH
    echo Installez Python 3.12+ depuis https://python.org
    pause
    exit /B 1
)

echo ✅ Python détecté
python --version

echo.
echo 📁 Création de l'environnement virtuel...
python -m venv venv

echo.
echo 🔧 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo 📦 Installation des dépendances...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 📂 Création des répertoires nécessaires...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "web" mkdir web
if not exist "web\static" mkdir web\static
if not exist "web\static\css" mkdir web\static\css
if not exist "web\static\js" mkdir web\static\js
if not exist "web\templates" mkdir web\templates
if not exist "scripts" mkdir scripts

echo.
echo 📝 Création du fichier .env depuis le template...
if not exist ".env" (
    copy "env.example" ".env" >nul 2>&1
    echo ⚠️  Fichier .env créé. Vous devez remplir vos clés API !
) else (
    echo ℹ️  Fichier .env déjà existant
)

echo.
echo 🧪 Test de connexion MySQL sur TEST-WAMP...
python scripts/test_mysql.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Échec du test MySQL. Vérifiez votre configuration WAMP.
    pause
    exit /b 1
)

echo.
echo 🔑 Test de la clé API OpenAI...
python scripts/test_openai.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ⚠️  Clé API OpenAI requise pour continuer
    pause
)

echo.
echo 🗄️ Initialisation de la base de données MySQL...
python scripts/setup_db.py

echo.
echo 🗄️  Initialisation de la base de données...
python src\fetch_feeds.py

echo.
echo ========================================
echo    Configuration terminée !
echo ========================================
echo.
echo 📋 Prochaines étapes:
echo    1. Éditez le fichier .env avec vos clés API
echo    2. Testez la récupération: python src\fetch_feeds.py
echo    3. Lancez l'API: python src\api.py
echo.
echo 🌐 URLs de test:
echo    - API: http://localhost:5000
echo    - Dashboard: http://localhost:8080
echo.
pause 