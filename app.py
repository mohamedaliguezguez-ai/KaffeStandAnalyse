import streamlit as st
import PIL.Image
import json
import base64
import io
from groq import Groq # Neu: Groq Bibliothek nutzen

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kaffee-KI Prototyp (Groq)", page_icon="☕")
st.title("☕ Kaffee-KI: Füllstand-Wächter")

# --- SIDEBAR: EINSTELLUNGEN ---
st.sidebar.header("Konfiguration")
api_key = st.sidebar.text_input("Groq API Key eingeben", type="password")
# Groq Vision Modell (Llama 3.2 ist sehr stark in Bildanalyse)
model_id = "llama-3.2-90b-vision"


# Hilfsfunktion: Bild für Groq in Base64 umwandeln
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist ein präzises Messmodul für eine Kaffeemaschine.
Deine Aufgabe: Analysiere das Bild der Tasse.
1. Finde den inneren Boden der Tasse (0%) und den oberen Rand (100%).
2. Bestimme den aktuellen Stand der Flüssigkeit (Kaffee).
3. Gib NUR ein JSON-Objekt zurück:
{
  "fill_percent": int,
  "action": "CONTINUE" | "SLOW" | "STOP",
  "confidence": float
}
Sicherheitsregel: Wenn der Stand > 90% ist, gib "STOP" aus.
"""

# --- HAUPTTEIL ---
if not api_key:
    st.warning("Bitte gib deinen Groq API-Key in der Seitenleiste ein, um zu starten.")
else:
    # Groq Client initialisieren
    client = Groq(api_key=api_key)

    img_file = st.camera_input("Foto der Tasse machen")

    if img_file:
        # Bild in Base64 konvertieren für die API
        base64_image = encode_image(img_file)
        
        with st.spinner('Groq KI analysiert Füllstand...'):
            try:
                # Groq API Abfrage (OpenAI-kompatibles Format)
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": SYSTEM_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    response_format={"type": "json_object"} # Erzwingt JSON-Ausgabe
                )
                
                # Ergebnis parsen
                res = json.loads(response.choices[0].message.content)
                
                # Visualisierung
                st.subheader(f"Füllstand: {res['fill_percent']}%")
                st.progress(res['fill_percent'] / 100)
                
                if res['action'] == "STOP":
                    st.error("🛑 STOPP! Tasse ist voll.")
                elif res['action'] == "SLOW":
                    st.warning("⚠️ LANGSAMER füllen...")
                else:
                    st.success("✅ Füllvorgang läuft...")
                
                with st.expander("KI-Details anzeigen"):
                    st.json(res)

            except Exception as e:
                st.error(f"Fehler bei der Groq-Anfrage: {e}")

st.info("Tipp: Halte das Handy stabil. Groq ist extrem schnell!")
