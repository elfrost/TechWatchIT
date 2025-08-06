#!/usr/bin/env python3
"""
Script pour démarrer le système TechWatchIT complet
API Web + Automatisation en parallèle
"""

import sys
import os
import threading
import time
from multiprocessing import Process

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_api():
    """Démarrer l'API Flask"""
    print("🌐 Démarrage de l'API Web...")
    os.system("python src/api.py")

def start_automation():
    """Démarrer l'automatisation"""
    print("🤖 Démarrage de l'automatisation...")
    time.sleep(5)  # Attendre que l'API démarre
    from scripts.automation_scheduler import TechWatchITAutomation
    automation = TechWatchITAutomation()
    automation.start_automation()

def main():
    print("🚀 TechWatchIT - Démarrage du système complet")
    print("=" * 60)
    print("🌐 API Web : http://localhost:5000")
    print("📊 Dashboard : http://localhost:5000/dashboard")
    print("📝 Blog : http://localhost:5000/blog")
    print("🤖 Automatisation : Activée")
    print("=" * 60)
    print("💡 Appuyez sur Ctrl+C pour arrêter le système complet")
    print()

    try:
        # Démarrer l'API dans un processus séparé
        api_process = Process(target=start_api)
        api_process.start()
        
        # Attendre un peu puis démarrer l'automatisation
        print("⏳ Démarrage de l'API en cours...")
        time.sleep(8)
        
        print("🤖 Démarrage de l'automatisation...")
        automation = start_automation()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du système demandé...")
        if 'api_process' in locals():
            api_process.terminate()
            api_process.join()
        print("✅ Système arrêté proprement")

if __name__ == "__main__":
    main() 