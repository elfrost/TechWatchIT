#!/usr/bin/env python3

from config.config import Config

print('🔍 Vérification configuration OpenAI:')
print(f'✅ API Key: {"Configurée" if Config.OPENAI_API_KEY else "❌ Non configurée"} {Config.OPENAI_API_KEY[:20] if Config.OPENAI_API_KEY else ""}...')
print(f'✅ Modèle: {Config.OPENAI_MODEL}')
print(f'✅ Modèle classifier: {Config.OPENAI_MODEL_CLASSIFIER}')
print(f'✅ Modèle summarizer: {Config.OPENAI_MODEL_SUMMARIZER}')
print(f'✅ Max tokens: {Config.OPENAI_MAX_TOKENS}') 