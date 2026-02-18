import streamlit as st
import PIL.Image
import json
import base64
import io
import time
from groq import Groq

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kaffee-KI Prototyp", page_icon="☕", layout="centered")
st.title("☕ Kaffee-KI: Füllstand-Wächter")

# --- KONFIGURATION ---
MODEL_ID = "meta-llama/llama-4-maverick-17b-128e-instruct"

st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Groq API Key eingeben", type="password")

# --- FUNKTIONEN ---

def process_and_encode_image(image_file, max_size=(512, 512)):
    """
    Verkleinert das Bild auf max. 512px und wandelt es in Base64 um.
    Das spart massiv Token und beschleunigt die Antwortzeit.
    """
    img = PIL.Image.open(image_file)
    
    # Proportionale Verkleinerung
    img.thumbnail(max_size, PIL.Image.LANCZOS)
    
    # In Buffer speichern (JPEG spart im Vergleich zu PNG zusätzlich Platz)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

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
    
    # Kamera-Widget
    img_file = st.camera_input("Foto der Tasse machen")

    # Platzhalter für eine saubere UI (überschreibt alte Werte)
    info_area = st.empty()
    progress_area = st.empty()
    status_msg = st.empty()

    if img_file:
        # 1. Bild optimieren & verkleinern
        base64_image = process_and_encode_image(img_file)
        
        with st.spinner('Llama 4 analysiert...'):
            try:
                # 2. KI-Anfrage senden
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
                
                # 3. Ergebnis verarbeiten
                res = json.loads(response.choices[0].message.content)
                fill = res.get('fill_percent', 0)
                action = res.get('action', 'CONTINUE')

                # 4. Anzeige aktualisieren
                info_area.subheader(f"Aktueller Füllstand: {fill}%")
                progress_area.progress(min(fill / 100, 1.0))
                
                # 5. Logik für Stop oder Wiederholung
                if fill >= 90 or action == "STOP":
                    status_msg.error(f"🛑 STOPP! Ziel erreicht ({fill}%).")
                    st.balloons()
                    # Hier stoppt die App, da kein st.rerun() aufgerufen wird
                else:
                    status_msg.success(f"✅ Stand: {fill}%. Nächstes Foto in 2 Sekunden...")
                with st.expander("KI-Details (Rohdaten)"):
                    st.json(res)

            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")


