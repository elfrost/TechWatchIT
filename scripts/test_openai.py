#!/usr/bin/env python3
"""
Script de test pour vérifier la clé API OpenAI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config.config import Config

def test_openai_api():
    """Tester la clé API OpenAI"""
    print("🧪 Test de la clé API OpenAI")
    print("=" * 50)
    
    try:
        # Vérifier la clé API
        api_key = Config.OPENAI_API_KEY
        if not api_key:
            print("❌ Clé API OpenAI manquante dans .env")
            print("💡 Ajoutez : OPENAI_API_KEY=sk-proj-votre-clé")
            return False
        
        if not api_key.startswith(('sk-', 'sk-proj-')):
            print(f"⚠️  Format de clé suspect : {api_key[:10]}...")
            print("💡 Format attendu : sk-proj-... ou sk-...")
        
        print(f"🔑 Clé API : {api_key[:10]}...{api_key[-4:]}")
        print(f"🤖 Modèle de test : {Config.OPENAI_MODEL}")
        
        # Initialiser le client OpenAI avec la nouvelle API
        client = OpenAI(api_key=api_key)
        
        # Test simple avec le modèle configuré
        print("\n🔄 Test de requête simple...")
        
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un assistant de test."},
                {"role": "user", "content": "Réponds juste 'OK TEST' pour confirmer que l'API fonctionne."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Réponse OpenAI : '{result}'")
        
        # Vérifier les détails de facturation
        usage = response.usage
        print(f"\n📊 Utilisation des tokens :")
        print(f"   • Input : {usage.prompt_tokens} tokens")
        print(f"   • Output : {usage.completion_tokens} tokens")
        print(f"   • Total : {usage.total_tokens} tokens")
        
        # Calculer le coût approximatif
        model_pricing = {
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4o": {"input": 2.50, "output": 10.00}
        }
        
        if Config.OPENAI_MODEL in model_pricing:
            pricing = model_pricing[Config.OPENAI_MODEL]
            cost = (usage.prompt_tokens * pricing["input"] / 1_000_000) + \
                   (usage.completion_tokens * pricing["output"] / 1_000_000)
            print(f"💰 Coût de ce test : ${cost:.6f} (~{cost*4.5:.6f}€)")
        
        print(f"\n🎉 API OpenAI fonctionnelle avec {Config.OPENAI_MODEL} !")
        print(f"📋 Prêt pour TechWatchIT")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "authentication" in error_msg or "invalid_api_key" in error_msg:
            print("❌ Erreur d'authentification OpenAI")
            print("💡 Vérifications :")
            print("   1. Clé API correcte dans .env")
            print("   2. Compte OpenAI actif")
            print("   3. Crédit disponible sur le compte")
            print("   4. Clé pas expirée/révoquée")
        elif "rate_limit" in error_msg:
            print("❌ Limite de taux dépassée")
            print("💡 Attendez quelques minutes avant de réessayer")
        elif "quota" in error_msg or "insufficient" in error_msg:
            print("❌ Quota insuffisant")
            print("💡 Ajoutez du crédit sur : https://platform.openai.com/account/billing")
        else:
            print(f"❌ Erreur inattendue : {e}")
            print("💡 Vérifiez votre connexion internet et la configuration")
            
        return False

def show_api_info():
    """Afficher les informations sur l'API OpenAI"""
    print("\n" + "="*50)
    print("📚 Comment obtenir une clé API OpenAI :")
    print()
    print("1. 🌐 Allez sur : https://platform.openai.com")
    print("2. 📝 Créez un compte (gratuit)")
    print("3. 🔑 Générez une clé : https://platform.openai.com/api-keys")
    print("4. 💳 Ajoutez du crédit ($5 minimum)")
    print("5. 📋 Copiez la clé dans votre fichier .env")
    print()
    print("🔐 Format de clé attendu :")
    print("   sk-proj-abc123... (nouveau format)")
    print("   sk-abc123...      (ancien format)")
    print()
    print("💰 Budget recommandé pour TechWatchIT :")
    print("   • gpt-4o-mini : ~$0.025/semaine ($5 = ~4 ans !)")
    print("   • gpt-4.1-mini : ~$0.066/semaine ($5 = ~18 mois)")

if __name__ == "__main__":
    try:
        success = test_openai_api()
        
        if not success:
            show_api_info()
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Test interrompu")
    except ImportError as e:
        print(f"❌ Module manquant : {e}")
        print("💡 Installez les dépendances : pip install -r requirements.txt") 