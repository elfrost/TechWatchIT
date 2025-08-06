#!/usr/bin/env python3
"""
Script de démarrage pour l'automatisation complète de TechWatchIT
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.automation_scheduler import TechWatchITAutomation
import argparse

def main():
    parser = argparse.ArgumentParser(description='TechWatchIT - Système d\'automatisation')
    parser.add_argument('--task', '-t', 
                       choices=['fetch', 'process', 'analyze', 'report', 'maintenance', 'backup'],
                       help='Exécuter une tâche spécifique manuellement')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Démarrer en mode automatique (daemon)')
    
    args = parser.parse_args()
    
    automation = TechWatchITAutomation()
    
    if args.task:
        # Mode manuel - exécuter une tâche spécifique
        print(f"🔧 Exécution manuelle de la tâche: {args.task}")
        automation.run_manual_task(args.task)
        
    elif args.daemon:
        # Mode daemon - automatisation complète
        print("🚀 Démarrage du système d'automatisation TechWatchIT")
        print("💡 Appuyez sur Ctrl+C pour arrêter")
        try:
            automation.start_automation()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
            
    else:
        # Mode interactif
        print("🤖 TechWatchIT - Système d'Automatisation")
        print("=" * 50)
        print("Choisissez une option:")
        print("1. Démarrer l'automatisation complète")
        print("2. Récupérer les flux RSS maintenant")
        print("3. Traiter les nouveaux articles")
        print("4. Générer les analyses détaillées")
        print("5. Générer le rapport quotidien")
        print("6. Effectuer la maintenance")
        print("7. Effectuer une sauvegarde")
        print("0. Quitter")
        
        while True:
            try:
                choice = input("\nVotre choix (0-7): ").strip()
                
                if choice == '0':
                    print("👋 Au revoir!")
                    break
                    
                elif choice == '1':
                    print("🚀 Démarrage de l'automatisation...")
                    print("💡 Appuyez sur Ctrl+C pour arrêter")
                    try:
                        automation.start_automation()
                    except KeyboardInterrupt:
                        print("\n🛑 Automatisation arrêtée")
                        
                elif choice == '2':
                    automation.run_manual_task('fetch')
                    
                elif choice == '3':
                    automation.run_manual_task('process')
                    
                elif choice == '4':
                    automation.run_manual_task('analyze')
                    
                elif choice == '5':
                    automation.run_manual_task('report')
                    
                elif choice == '6':
                    automation.run_manual_task('maintenance')
                    
                elif choice == '7':
                    automation.run_manual_task('backup')
                    
                else:
                    print("❌ Choix invalide. Veuillez entrer un nombre entre 0 et 7.")
                    
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    main() 