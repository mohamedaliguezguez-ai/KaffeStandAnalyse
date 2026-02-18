def process_and_encode_image(image_file, max_size=(512, 512)):
    """Öffnet das Bild, verkleinert es und gibt den Base64-String zurück."""
    # 1. Bild mit PIL öffnen
    img = PIL.Image.open(image_file)
    
    # 2. Bild verkleinern (behält das Seitenverhältnis bei)
    img.thumbnail(max_size, PIL.Image.LANCZOS)
    
    # 3. Das verkleinerte Bild in einen Buffer speichern
    buffer = io.BytesIO()
    # Wir speichern es als JPEG mit moderater Kompression für noch weniger Bytes
    img.save(buffer, format="JPEG", quality=85) 
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# --- IM HAUPTTEIL ---
if img_file:
    # Hier rufen wir die neue Funktion auf
    base64_image = process_and_encode_image(img_file)
    
    with st.spinner('Llama 4 analysiert das optimierte Bild...'):
        # ... Rest deines Codes bleibt gleich
        # Nur zum Testen:
st.image(io.BytesIO(base64.b64decode(base64_image)), caption="Dieses Bild sieht die KI")
