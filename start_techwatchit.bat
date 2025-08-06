@echo off
title TechWatchIT - Démarrage Système Complet
echo.
echo ========================================
echo     TechWatchIT - Démarrage Système    
echo ========================================
echo.
echo 🚀 Initialisation du système...
echo.

:: Vérifier que Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python et réessayer
    pause
    exit /b 1
)

:: Vérifier que nous sommes dans le bon répertoire
if not exist "src\api.py" (
    echo ❌ ERREUR: Script lancé depuis le mauvais répertoire
    echo Veuillez placer ce script dans le dossier TechWatchIT
    pause
    exit /b 1
)

echo ✅ Python détecté
echo ✅ Répertoire TechWatchIT confirmé
echo.

:: Démarrer l'automatisation en arrière-plan
echo 🤖 Démarrage de l'automatisation TechWatchIT...
start "TechWatchIT - Automatisation" /min cmd /c "python start_automation.py --daemon"

:: Attendre 3 secondes
timeout /t 3 /nobreak >nul

:: Démarrer l'API Web
echo 🌐 Démarrage de l'interface web...
start "TechWatchIT - Interface Web" cmd /c "python src/api.py"

:: Attendre 8 secondes pour que l'API démarre
echo ⏳ Attente du démarrage des services (8 secondes)...
timeout /t 8 /nobreak >nul

:: Ouvrir le navigateur automatiquement
echo 🌐 Ouverture du dashboard dans le navigateur...
start "" "http://localhost:5000/dashboard"

echo.
echo ========================================
echo       ✅ TechWatchIT DÉMARRÉ !        
echo ========================================
echo.
echo 📊 Dashboard      : http://localhost:5000/dashboard
echo 📝 Blog          : http://localhost:5000/blog
echo ✅ Santé API     : http://localhost:5000/health
echo.
echo 🤖 Automatisation : Active (récupération RSS + traitement IA)
echo 🌐 Interface Web  : Active sur port 5000
echo.
echo ⚠️  Pour arrêter le système :
echo     - Fermez toutes les fenêtres TechWatchIT
echo     - Ou appuyez Ctrl+C dans chaque terminal
echo.
echo Appuyez sur une touche pour fermer cette fenêtre...
pause >nul 