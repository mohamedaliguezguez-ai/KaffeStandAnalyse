import streamlit as st
import PIL.Image
import json
import base64
import io
from groq import Groq

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kaffee-KI Prototyp", page_icon="☕")
st.title("☕ Kaffee-KI: Füllstand-Wächter")

# --- KONFIGURATION ---
# Wir nutzen dein erfolgreich getestetes Modell!
MODEL_ID = "meta-llama/llama-4-maverick-17b-128e-instruct"

st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Groq API Key eingeben", type="password")

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist ein Messmodul. Analysiere das Bild der Kaffeetasse.
Gib NUR ein JSON-Objekt zurück:
{
  "fill_percent": int,
  "action": "CONTINUE" | "STOP",
  "confidence": float
}
Regel: Wenn der Stand > 90% ist, gib "STOP" aus. Antworte ausschließlich im JSON-Format.
"""

# --- HAUPTTEIL ---
if not api_key:
    st.warning("Bitte gib deinen Groq API-Key in der Seitenleiste ein.")
else:
    client = Groq(api_key=api_key)
    img_file = st.camera_input("Foto der Tasse machen")

    if img_file:
        base64_image = encode_image(img_file)
        
        with st.spinner('Llama 4 analysiert...'):
            try:
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": SYSTEM_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Ergebnis parsen
                res = json.loads(response.choices[0].message.content)
                
                # Anzeige der Ergebnisse
                st.subheader(f"Füllstand: {res['fill_percent']}%")
                st.progress(res['fill_percent'] / 100)
                
                if res['action'] == "STOP":
                    st.error("🛑 STOPP! Tasse voll.")
                else:
                    st.success("✅ Füllen...")
                
                with st.expander("KI-Details"):
                    st.json(res)

            except Exception as e:
                st.error(f"Fehler: {e}")
