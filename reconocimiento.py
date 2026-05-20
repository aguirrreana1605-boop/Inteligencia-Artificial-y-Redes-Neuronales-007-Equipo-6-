import cv2
import face_recognition
import requests
import os
import numpy as np

# --- CONFIGURACIÓN ---
URL_ESP32 = "http://192.168.1.89/mjpeg"  # <-- Cambia por la IP de tu ESP32-CAM
# URL_ESP32 = 0
print("Cargando rostros conocidos...")
rostros_conocidos = []
nombres_conocidos = []

# Cargar tu foto de referencia (Asegúrate de tener tu foto en esta ruta)
# Por ejemplo: "C:/Users/Jorge/Desktop/proyecto_puerta/Jose.jpg"
# Cargar tu foto de referencia
ruta_foto = "rostros_conocidos/Jorge.jpg"  # <-- Asegúrate de que se llame exactamente así

if os.path.exists(ruta_foto):
    imagen_jorge = face_recognition.load_image_file(ruta_foto)
    encodings_encontrados = face_recognition.face_encodings(imagen_jorge)
    
    # Validar si la IA realmente vio un rostro en la foto
    if len(encodings_encontrados) > 0:
        encoding_jorge = encodings_encontrados[0]
        rostros_conocidos.append(encoding_jorge)
        nombres_conocidos.append("Jorge")
        print("¡Rostro de Jose cargado con éxito!")
    else:
        print("Alerta: Se abrió 'Jorge.jpg' pero la IA no detectó ningún rostro en la foto. Intenta con otra imagen de frente.")
else:
    print(f"Alerta: No se encontró la foto en '{ruta_foto}'. El sistema solo detectará sin nombres.")

print("Conectando al flujo de video del ESP32-CAM...")
stream = cv2.VideoCapture(URL_ESP32)

while True:
    ret, frame = stream.read()
    if not ret:
        print("Error al recibir el video.")
        break

    # Reducir el tamaño para que procese en tiempo real más rápido
    frame_pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_frame = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

    # Localizar y codificar rostros de la cámara
    loc_rostros = face_recognition.face_locations(rgb_frame)
    encodings_rostros = face_recognition.face_encodings(rgb_frame, loc_rostros)

    for face_encoding, face_location in zip(encodings_rostros, loc_rostros):
        coincidencias = face_recognition.compare_faces(rostros_conocidos, face_encoding)
        nombre = "Desconocido"

        if True in coincidencias:
            primer_coincidencia = coincidencias.index(True)
            nombre = nombres_conocidos[primer_coincidencia]
            print(f"¡Rostro reconocido: {nombre}! Abriendo puerta...")

        # Reescalar coordenadas para dibujar el recuadro en el tamaño original
        y1, x2, y2, x1 = face_location
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

        # Dibujar cuadro y nombre
        color = (0, 255, 0) if nombre != "Desconocido" else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, nombre, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Sistema de Acceso IA", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stream.release()
cv2.destroyAllWindows()