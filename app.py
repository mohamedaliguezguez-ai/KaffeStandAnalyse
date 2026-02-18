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

from PIL import ImageEnhance

def process_and_encode_image(image_file, max_size=(512, 512)):
    img = PIL.Image.open(image_file)
    img.thumbnail(max_size, PIL.Image.LANCZOS)
    
    # Optional: Kontrast leicht erhöhen, um den Pegel deutlicher zu machen
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2) 
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90) # Qualität etwas hochgeschraubt
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# --- SYSTEM PROMPT ---

SYSTEM_PROMPT = """
Du bist ein industrielles Bildverarbeitungs-Modul. Deine Aufgabe ist die präzise Füllstandsmessung.

Schritt-für-Schritt-Analyse:
1. **Material-Check:** Prüfe, ob es sich wirklich um frischen Kaffee oder Schaum handelt. 
   - Unterscheide klar zwischen einer gefüllten Tasse und Schmutzrückständen oder Verfärbungen am Glasrand. 
   - Wenn nur Schmutz/Reste ohne echtes Volumen erkannt werden -> Füllstand 0%.

2. **Geometrische Vermessung:** - Nutze den sichtbaren Glasdurchmesser als Referenzmaßstab (Standardglas ca. 7-8cm).
   - Ermittle den vertikalen Abstand zwischen der Oberkante (Rim) und der Flüssigkeitsoberfläche (Liquid Level).

3. **Logik-Auswertung:**
   - Abstand > 5cm: Glas ist fast leer oder weniger als halb voll.
   - Abstand ca. 3-4cm: Glas ist moderat gefüllt.
   - Abstand <= 2cm: Das Glas gilt als VOLL.

Antworte ausschließlich im JSON-Format:
{
  "analysis": "Beschreibe kurz: Kaffee/Schaum erkannt? Schmutz ausgeschlossen? Geschätzter Abstand in cm?",
  "estimated_distance_cm": float,
  "fill_percent": int,
  "action": "CONTINUE" | "STOP",
  "confidence": float
}

Regel: Wenn der Abstand <= 2cm ist, setze fill_percent auf >= 90% und action auf "STOP".
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






