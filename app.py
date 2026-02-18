import streamlit as st
import PIL.Image
import json
import base64
import io
import time  # Neu für die Pause
from groq import Groq

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kaffee-KI Prototyp", page_icon="☕")
st.title("☕ Kaffee-KI: Füllstand-Wächter")

# --- KONFIGURATION ---
MODEL_ID = "meta-llama/llama-4-maverick-17b-128e-instruct"

st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Groq API Key eingeben", type="password")

# Session State initialisieren, um den Loop zu steuern
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

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
Regel: Wenn der Stand >= 90% ist, gib "STOP" aus. Antworte ausschließlich im JSON-Format.
"""

# --- HAUPTTEIL ---
if not api_key:
    st.warning("Bitte gib deinen Groq API-Key in der Seitenleiste ein.")
else:
    client = Groq(api_key=api_key)
    
    # Kamera-Input
    img_file = st.camera_input("Foto der Tasse machen")

    # Platzhalter für Statusmeldungen, damit sie nicht immer unten angehängt werden
    status_placeholder = st.empty()
    progress_placeholder = st.empty()

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
                
                res = json.loads(response.choices[0].message.content)
                fill = res.get('fill_percent', 0)
                action = res.get('action', 'STOP')

                # Anzeige der Ergebnisse
                status_placeholder.subheader(f"Füllstand: {fill}%")
                progress_placeholder.progress(fill / 100)
                
                if action == "STOP" or fill >= 90:
                    st.error("🛑 STOPP! Tasse ist voll (>= 90%).")
                    st.session_state.monitoring = False # Stop den Prozess
                    st.balloons() # Kleiner Erfolgseffekt
                else:
                    st.success(f"✅ Stand okay ({fill}%). Nächste Messung in 2 Sek...")
                    st.session_state.monitoring = True
                    
                    # Die Magie: 2 Sekunden warten und App neu starten
                    time.sleep(2)
                    st.rerun() 

                with st.expander("KI-Details"):
                    st.json(res)

            except Exception as e:
                st.error(f"Fehler: {e}")
