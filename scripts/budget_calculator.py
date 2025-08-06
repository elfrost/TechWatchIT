#!/usr/bin/env python3
"""
Calculateur de budget OpenAI pour TechWatchIT
Estimation des coûts selon le volume et le modèle
"""

def calculate_weekly_cost():
    """Calculer les coûts hebdomadaires pour différents modèles"""
    
    print("💰 TechWatchIT - Calculateur de budget OpenAI")
    print("=" * 60)
    
    # Paramètres d'estimation
    articles_per_week = 60  # Estimation basée sur 7 feeds RSS
    tokens_input_per_article = 1950  # Classification + Résumé
    tokens_output_per_article = 200  # Réponses courtes
    
    total_input_tokens = articles_per_week * tokens_input_per_article / 1_000_000  # En millions
    total_output_tokens = articles_per_week * tokens_output_per_article / 1_000_000  # En millions
    
    print(f"📊 Estimation basée sur :")
    print(f"   • {articles_per_week} articles/semaine")
    print(f"   • {tokens_input_per_article} tokens input/article")
    print(f"   • {tokens_output_per_article} tokens output/article")
    print(f"   • Total : {total_input_tokens:.3f}M input + {total_output_tokens:.3f}M output")
    print()
    
    # Tarifs des modèles (prix par 1M tokens)
    models = {
        "gpt-4o-mini": {
            "input": 0.15,
            "output": 0.60,
            "quality": "Bonne",
            "usage": "🧪 Test/Démo"
        },
        "gpt-4.1-mini": {
            "input": 0.40,
            "output": 1.60,
            "quality": "Très bonne",
            "usage": "⭐ Production"
        },
        "gpt-4.1": {
            "input": 2.00,
            "output": 8.00,
            "quality": "Excellente",
            "usage": "🏢 Entreprise"
        },
        "gpt-4o": {
            "input": 2.50,
            "output": 10.00,
            "quality": "Excellente",
            "usage": "🔬 Recherche"
        }
    }
    
    print("💸 Coûts hebdomadaires par modèle :")
    print("-" * 60)
    
    results = []
    for model, pricing in models.items():
        input_cost = total_input_tokens * pricing["input"]
        output_cost = total_output_tokens * pricing["output"]
        weekly_cost = input_cost + output_cost
        monthly_cost = weekly_cost * 4.33  # 4.33 semaines/mois
        yearly_cost = weekly_cost * 52
        
        results.append({
            "model": model,
            "weekly_cost": weekly_cost,
            "monthly_cost": monthly_cost,
            "yearly_cost": yearly_cost,
            "quality": pricing["quality"],
            "usage": pricing["usage"]
        })
        
        print(f"{model:15} | {pricing['usage']:12} | ${weekly_cost:6.3f}/sem | ${monthly_cost:7.2f}/mois | ${yearly_cost:7.2f}/an")
    
    print("-" * 60)
    
    # Recommandations
    print("\n🏆 Recommandations :")
    print()
    
    best_test = min(results, key=lambda x: x["weekly_cost"])
    print(f"✅ **Pour débuter/tester** :")
    print(f"   • Modèle : {best_test['model']}")
    print(f"   • Budget : ${best_test['weekly_cost']:.3f}/semaine (~{best_test['weekly_cost']*4.5:.2f}€/mois)")
    print(f"   • Avantage : Ultra économique, parfait pour validation")
    print()
    
    production = next(x for x in results if x["model"] == "gpt-4.1-mini")
    print(f"⭐ **Pour la production** :")
    print(f"   • Modèle : {production['model']}")
    print(f"   • Budget : ${production['weekly_cost']:.3f}/semaine (~{production['monthly_cost']*4.5:.2f}€/mois)")
    print(f"   • Avantage : Meilleur rapport qualité/prix")
    print()
    
    enterprise = next(x for x in results if x["model"] == "gpt-4.1")
    print(f"🏢 **Pour l'entreprise** :")
    print(f"   • Modèle : {enterprise['model']}")
    print(f"   • Budget : ${enterprise['weekly_cost']:.3f}/semaine (~{enterprise['monthly_cost']*4.5:.2f}€/mois)")
    print(f"   • Avantage : Qualité maximale, analyses approfondies")
    print()
    
    # Comparaison avec autres coûts IT
    print("💡 **Perspective coûts IT** :")
    print(f"   • TechWatchIT (gpt-4o-mini) : ~{best_test['yearly_cost']*4.5:.0f}€/an")
    print(f"   • Licence antivirus entreprise : ~50-100€/poste/an")
    print(f"   • Formation sécurité : ~500-1000€/personne/an")
    print(f"   • Audit sécurité : ~5000-15000€/an")
    print(f"   ➡️  TechWatchIT = ~1% du coût d'un audit sécurité !")
    
    return results

def calculate_custom_budget(articles_per_week, model_name="gpt-4o-mini"):
    """Calculer le budget pour un volume personnalisé"""
    
    models = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4o": {"input": 2.50, "output": 10.00}
    }
    
    if model_name not in models:
        return None
    
    tokens_input_per_article = 1950
    tokens_output_per_article = 200
    
    total_input_tokens = articles_per_week * tokens_input_per_article / 1_000_000
    total_output_tokens = articles_per_week * tokens_output_per_article / 1_000_000
    
    pricing = models[model_name]
    input_cost = total_input_tokens * pricing["input"]
    output_cost = total_output_tokens * pricing["output"]
    weekly_cost = input_cost + output_cost
    
    return {
        "articles_per_week": articles_per_week,
        "model": model_name,
        "weekly_cost": weekly_cost,
        "monthly_cost": weekly_cost * 4.33,
        "yearly_cost": weekly_cost * 52
    }

if __name__ == "__main__":
    calculate_weekly_cost()
    
    print("\n" + "="*60)
    print("🧮 Calculateur personnalisé :")
    
    try:
        articles = int(input("Nombre d'articles par semaine (60 par défaut) : ") or 60)
        model = input("Modèle (gpt-4o-mini par défaut) : ") or "gpt-4o-mini"
        
        result = calculate_custom_budget(articles, model)
        if result:
            print(f"\n📊 Résultat personnalisé :")
            print(f"   • {result['articles_per_week']} articles/semaine avec {result['model']}")
            print(f"   • ${result['weekly_cost']:.3f}/semaine")
            print(f"   • ${result['monthly_cost']:.2f}/mois")
            print(f"   • ${result['yearly_cost']:.2f}/an")
        else:
            print("❌ Modèle non reconnu")
            
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
    except Exception as e:
        print(f"❌ Erreur : {e}") 