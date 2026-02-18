from groq import Groq

client = Groq(api_key="DEIN_GROQ_API_KEY")
models = client.models.list()

for model in models.data:
    if "vision" in model.id.lower() or "pixtral" in model.id.lower():
        print(f"Verfügbares Vision-Modell: {model.id}")
