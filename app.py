import streamlit as st
import PIL.Image
import json
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kaffee-KI Prototyp", page_icon="☕")
st.title("☕ Kaffee-KI: Füllstand-Wächter")

# --- SIDEBAR: EINSTELLUNGEN ---
st.sidebar.header("Konfiguration")
api_key = st.sidebar.text_input("Gemini API Key eingeben", type="password")
model_id = "gemini-1.5-flash" # Schnell & kostenlos

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
    st.warning("Bitte gib deinen API-Key in der Seitenleiste ein, um zu starten.")
else:
    client = genai.Client(api_key=api_key)

    # Kamera-Eingabe (öffnet auf dem Handy direkt die Kamera)
    img_file = st.camera_input("Foto der Tasse machen")

    if img_file:
        # Bild für Gemini vorbereiten
        img = PIL.Image.open(img_file)
        
        with st.spinner('KI analysiert Füllstand...'):
            try:
                # API Abfrage
                response = client.models.generate_content(
                    model=model_id,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json"
                    ),
                    contents=[img]
                )
                
                # Ergebnis parsen
                res = json.loads(response.text)
                
                # Visualisierung
                st.subheader(f"Füllstand: {res['fill_percent']}%")
                
                # Status-Balken
                st.progress(res['fill_percent'] / 100)
                
                # Empfehlung anzeigen
                if res['action'] == "STOP":
                    st.error("🛑 STOPP! Tasse ist voll.")
                elif res['action'] == "SLOW":
                    st.warning("⚠️ LANGSAMER füllen...")
                else:
                    st.success("✅ Füllvorgang läuft...")
                
                # Detail-Info
                with st.expander("KI-Details anzeigen"):
                    st.json(res)

            except Exception as e:
                st.error(f"Fehler: {e}")

st.info("Tipp: Halte das Handy stabil und achte auf gute Beleuchtung.")