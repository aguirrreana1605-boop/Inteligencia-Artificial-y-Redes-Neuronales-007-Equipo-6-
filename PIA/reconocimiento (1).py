
# face_recognition:
# Librería especializada en reconocimiento facial.
# Internamente usa dlib y modelos de Deep Learning.
# Utiliza una red neuronal convolucional (CNN) para analizar rostros
# y convertirlos en vectores matemáticos (encodings) que representan
# características únicas de una cara.
import face_recognition

# requests:
# Librería para hacer peticiones HTTP.
# Aquí se usa para enviar una señal al ESP32
# (como si el programa "tocara" una dirección web).
import requests

# os:
# Permite interactuar con el sistema operativo.
# Aquí se usa para buscar carpetas, listar archivos y unir rutas.
import os

# re:
# Librería de expresiones regulares.
# Sirve para buscar o modificar texto usando patrones.
# Aquí se usa para quitar números de nombres de archivos.
import re

# numpy:
# Librería matemática para trabajar con arreglos numéricos.
# Aquí se usa para operaciones rápidas, como encontrar
# el valor más pequeño dentro de una lista.
import numpy as np


# ============================= CONFIGURACIÓN =============================

# URL de la cámara IP (comentada porque actualmente no se usa)
# URL_CAMARA = "http://192.168.137.59/mjpeg"

# Dirección IP del ESP32.
# Cuando el rostro sea reconocido, se enviará una petición aquí.
IP_ESP32 = "http://192.168.137.34"

# URL_CAMARA = 0 significa usar la cámara local de la computadora.
# En OpenCV, 0 normalmente representa la webcam principal.
URL_CAMARA = 0

print("Cargando rostros conocidos...")


# ============================= LISTAS VACÍAS =============================

# Aquí se guardarán los vectores matemáticos (encodings)
# de los rostros conocidos.
rostros_conocidos = []

# Aquí se guardarán los nombres correspondientes
# a cada rostro cargado.
nombres_conocidos = []


# Carpeta donde estarán TODAS las fotos de personas conocidas.
carpeta_rostros = "rostros_conocidos"


# ============================= CARGAR FOTOS =============================

# Verifica si la carpeta existe.
# os.path.exists() revisa si esa ruta está presente en el sistema.
if os.path.exists(carpeta_rostros):

    # os.listdir() obtiene todos los archivos dentro de la carpeta.
    archivos = os.listdir(carpeta_rostros)

    # Recorre cada archivo encontrado.
    for archivo in archivos:

        # Verifica si el archivo termina con extensión de imagen.
        # lower() evita problemas con mayúsculas/minúsculas.
        if archivo.lower().endswith((".jpg", ".jpeg", ".png")):

            # Une carpeta + nombre de archivo para formar la ruta completa.
            ruta = os.path.join(carpeta_rostros, archivo)

            print(f"Cargando {archivo}...")

            # Carga la imagen desde disco.
            # La convierte internamente en una matriz de píxeles.
            imagen = face_recognition.load_image_file(ruta)

            # face_encodings():
            # Detecta el rostro y genera un vector de 128 números.
            # Ese vector representa matemáticamente el rostro.
            # Esto es Deep Learning: una red neuronal ya entrenada
            # analiza rasgos faciales únicos.
            encodings = face_recognition.face_encodings(imagen)

            # Verifica que sí se haya detectado al menos un rostro.
            if len(encodings) > 0:

                # Extraer nombre quitando números.
                # Ejemplo:
                # Jorge1.jpg -> Jorge
                # Jorge2.jpg -> Jorge
                #
                # re.sub():
                # busca números (\d+) y los reemplaza por nada.
                nombre = re.sub(r'\d+', '', os.path.splitext(archivo)[0])

                # Guarda el encoding facial.
                rostros_conocidos.append(encodings[0])

                # Guarda el nombre correspondiente.
                nombres_conocidos.append(nombre)

                print(f"Rostro cargado: {nombre}")

            else:
                print(f"No se detectó rostro en {archivo}")

else:
    print("No existe la carpeta rostros_conocidos")
    exit()

print(f"Total de rostros cargados: {len(rostros_conocidos)}")


# ============================= ABRIR CÁMARA =============================

# VideoCapture abre la fuente de video.
# Puede ser:
# 0 = webcam
# URL = cámara IP
stream = cv2.VideoCapture(URL_CAMARA)

# Verifica que sí se pudo abrir.
if not stream.isOpened():
    print("No se pudo abrir la cámara.")
    exit()


# Variable de control:
# evita mandar muchas señales al ESP32 repetidamente.
puerta_abierta = False


# ============================= BUCLE PRINCIPAL =============================

while True:

    # Lee un frame (imagen) de la cámara.
    # ret = indica si se pudo leer
    # frame = imagen capturada
    ret, frame = stream.read()

    if not ret:
        print("Error leyendo cámara.")
        break


    # ============================= PREPROCESAMIENTO =============================

    # Reduce el tamaño de la imagen al 25%.
    # Esto acelera muchísimo el reconocimiento facial
    # porque hay menos píxeles que procesar.
    frame_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # OpenCV trabaja en formato BGR
    # face_recognition trabaja en RGB
    # Por eso se convierte el orden de colores.
    rgb_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)


    # ============================= DETECCIÓN FACIAL =============================

    # face_locations():
    # Detecta dónde están los rostros dentro de la imagen.
    # Devuelve coordenadas:
    # arriba, derecha, abajo, izquierda
    locations = face_recognition.face_locations(rgb_small)

    # face_encodings():
    # Para cada rostro detectado, genera su vector de 128 características.
    encodings_actuales = face_recognition.face_encodings(
        rgb_small,
        locations
    )


    # Recorre cada rostro encontrado.
    for face_encoding, face_location in zip(encodings_actuales, locations):


        # ============================= COMPARACIÓN =============================

        # compare_faces():
        # Compara el rostro actual contra TODOS los conocidos.
        #
        # tolerance:
        # entre más bajo, más estricto.
        # Aquí 0.5 significa reconocimiento más preciso.
        matches = face_recognition.compare_faces(
            rostros_conocidos,
            face_encoding,
            tolerance=0.5
        )

        # face_distance():
        # Calcula qué tan parecidos son matemáticamente.
        # Mientras menor sea la distancia,
        # más parecido es el rostro.
        face_distances = face_recognition.face_distance(
            rostros_conocidos,
            face_encoding
        )

        # Nombre por defecto
        nombre = "Desconocido"


        # Si sí hay rostros guardados
        if len(face_distances) > 0:

            # np.argmin():
            # encuentra la posición del valor más pequeño.
            # O sea: el rostro más parecido.
            best_match_index = np.argmin(face_distances)

            # Verifica si ese rostro realmente pasó
            # el umbral de reconocimiento.
            if matches[best_match_index]:
                nombre = nombres_conocidos[best_match_index]


                # ============================= ESP32 =============================

                # Evita mandar muchas veces la señal
                if not puerta_abierta:

                    print(f"Bienvenido {nombre}")

                    try:

                        # requests.get():
                        # Hace una petición HTTP al ESP32.
                        # Es como visitar:
                        # http://IP/abrir
                        #
                        # timeout=1:
                        # si tarda más de 1 segundo, cancela.
                        requests.get(
                            f"{IP_ESP32}/abrir",
                            timeout=1
                        )

                        print("Comando enviado al ESP32")

                        # Marca que ya se abrió.
                        puerta_abierta = True

                    except:
                        print("No se pudo conectar al ESP32")


        # ============================= ESCALAR COORDENADAS =============================

        # Como la imagen se hizo pequeña (25%),
        # hay que regresar coordenadas al tamaño real.
        y1, x2, y2, x1 = face_location

        y1 *= 4
        x2 *= 4
        y2 *= 4
        x1 *= 4


        # ============================= COLOR DEL CUADRO =============================

        # Verde = reconocido
        # Rojo = desconocido
        color = (0, 255, 0) if nombre != "Desconocido" else (0, 0, 255)


        # ============================= DIBUJAR CUADRO =============================

        # rectangle():
        # Dibuja un rectángulo sobre el rostro.
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )


        # ============================= ESCRIBIR NOMBRE =============================

        # putText():
        # Escribe texto encima del cuadro.
        cv2.putText(
            frame,
            nombre,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )


    # ============================= RESET =============================

    # Si ya no hay ningún rostro en cámara,
    # se reinicia el sistema para permitir
    # volver a abrir la puerta en la próxima detección.
    if len(locations) == 0:
        puerta_abierta = False


    # ============================= MOSTRAR VENTANA =============================

    # Muestra el video procesado en tiempo real.
    cv2.imshow("Sistema IA", frame)


    # ============================= SALIR =============================

    # waitKey(1):
    # espera 1 milisegundo por una tecla.
    #
    # ord('q'):
    # convierte la letra q a código numérico.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# ============================= LIBERAR RECURSOS =============================

# Cierra la cámara
stream.release()

# Cierra ventanas de OpenCV
cv2.destroyAllWindows()