@echo off
title TechWatchIT - Arrêt Système
echo.
echo ========================================
echo     TechWatchIT - Arrêt Système      
echo ========================================
echo.

echo 🛑 Arrêt des processus TechWatchIT...
echo.

:: Arrêter les processus Python liés à TechWatchIT
echo 🔍 Recherche des processus actifs...

:: Tuer les processus par nom de fenêtre
taskkill /f /fi "WINDOWTITLE:TechWatchIT - Automatisation*" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Automatisation arrêtée
) else (
    echo ⚠️  Aucun processus d'automatisation trouvé
)

taskkill /f /fi "WINDOWTITLE:TechWatchIT - Interface Web*" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Interface Web arrêtée
) else (
    echo ⚠️  Aucun processus d'interface web trouvé
)

:: Arrêter tous les processus Python utilisant les ports 5000
echo.
echo 🔍 Vérification des ports utilisés...

:: Trouver et tuer les processus utilisant le port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    taskkill /f /pid %%a >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Processus sur port 5000 arrêté (PID: %%a)
    )
)

:: Petite pause
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo      ✅ TECHWATCHIT ARRÊTÉ !         
echo ========================================
echo.
echo 🛑 Tous les processus ont été arrêtés
echo 🌐 Port 5000 libéré
echo.
echo Vous pouvez maintenant :
echo   • Redémarrer avec start_techwatchit.bat
echo   • Fermer cette fenêtre
echo.
echo Appuyez sur une touche pour fermer...
pause >nul 