import os
import socket
import threading
import qrcode
from flask import Flask, request
import logging

# Desactivar logs molestos de Flask en la consola
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class GestorCamaraMovil:
    def __init__(self, directorio_guardado="evidencias"):
        """
        Inicializa el gestor.
        :param directorio_guardado: Carpeta donde se guardarán las fotos.
        """
        self.app = Flask(__name__)
        self.directorio = directorio_guardado
        self.puerto = 5000
        self.callback_exito = None # Función a ejecutar cuando llega la foto
        self.nombre_archivo_actual = "evidencia_temp.jpg"
        
        # Crear directorio si no existe
        os.makedirs(self.directorio, exist_ok=True)
        
        # Configurar rutas de Flask
        self._configurar_rutas()
        
        # Variable para controlar el hilo del servidor
        self.server_thread = None

    def _obtener_ip_local(self):
        """Detecta la IP de la máquina en la red local (Wifi/Ethernet/USB Tethering)"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Intentamos conectar a una IP pública (no envía datos, solo consulta ruta)
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def _configurar_rutas(self):
        """Define qué pasa cuando el celular entra a la web"""
        
        # HTML simple con botón gigante para el celular
        HTML_TEMPLATE = """
        <!doctype html>
        <html lang="es">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta charset="UTF-8">
            <title>Subir Evidencia - TEAR</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    text-align: center; 
                    padding: 20px; 
                    background-color: #2b2b2b;
                    color: #e0e0e0;
                    margin: 0;
                }
                
                .brand-container { margin-bottom: 20px; padding-top: 20px; }
                .brand-title { color: #ffc107; font-size: 36px; font-weight: bold; margin: 0; letter-spacing: 2px; }
                .brand-subtitle { color: #a0a0a0; font-size: 14px; margin-top: 5px; }

                /* Ocultamos el input original feo */
                input[type="file"] {
                    display: none;
                }

                /* Creamos nuestro propio botón de "Seleccionar" */
                .custom-file-upload {
                    display: inline-block;
                    padding: 20px;
                    width: 85%;
                    cursor: pointer;
                    background-color: #3e3e3e;
                    border: 2px dashed #666;
                    border-radius: 8px;
                    color: #ffffff;
                    font-size: 18px;
                    margin-top: 20px;
                    transition: background 0.3s;
                }

                .custom-file-upload:hover {
                    background-color: #4a4a4a;
                    border-color: #ffc107;
                }

                /* Botón de Enviar (Amarillo) */
                .btn-submit {
                    background-color: #ffc107;
                    color: #1a1a1a;
                    padding: 18px;
                    border: none; 
                    border-radius: 8px; 
                    font-size: 18px;
                    font-weight: bold;
                    width: 95%; /* Un poco más ancho */
                    margin-top: 30px; 
                    cursor: pointer;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                    display: none; /* Se oculta hasta que haya foto */
                }
                
                #file-name {
                    margin-top: 15px;
                    font-style: italic;
                    color: #ffc107;
                    height: 20px;
                }
            </style>
        </head>
        <body>
            
            <div class="brand-container">
                <div style="font-size: 40px;">📁</div> 
                <h1 class="brand-title">TEAR</h1>
                <div class="brand-subtitle">Taller Eléctrico Automotriz "Reyes"</div>
            </div>

            <h3>Nueva Evidencia</h3>
            <p style="color:#aaa;">Paso 1: Captura la imagen</p>
            
            <form method="post" enctype="multipart/form-data">
                <label for="file-upload" class="custom-file-upload">
                    Tocar aquí para tomar foto
                </label>
                <input id="file-upload" type="file" name="file" accept="image/*" capture="environment" onchange="mostrarBotonEnviar()">
                
                <div id="file-name"></div>

                <input id="submit-btn" class="btn-submit" type="submit" value="GUARDAR FOTO EN SISTEMA">
            </form>

            <script>
                function mostrarBotonEnviar() {
                    var input = document.getElementById('file-upload');
                    var fileNameDisplay = document.getElementById('file-name');
                    var submitBtn = document.getElementById('submit-btn');
                    var label = document.querySelector('.custom-file-upload');

                    if (input.files && input.files.length > 0) {
                        // Cambiar texto de estado
                        fileNameDisplay.textContent = "Foto capturada exitosamente";
                        
                        // Cambiar estilo del botón de cámara para indicar que ya se usó
                        label.style.borderColor = "#ffc107";
                        label.style.backgroundColor = "#2b2b2b";
                        label.innerHTML = "¿Cambiar foto?";
                        
                        // Mostrar el botón de guardar
                        submitBtn.style.display = "inline-block";
                    }
                }
            </script>
        </body>
        </html>
        """

        @self.app.route('/', methods=['GET', 'POST'])
        def index():
            if request.method == 'POST':
                if 'file' not in request.files:
                    return "No se encontró archivo"
                file = request.files['file']
                if file.filename == '':
                    return "No seleccionaste archivo"
                
                if file:
                    ruta_completa = os.path.join(self.directorio, self.nombre_archivo_actual)
                    file.save(ruta_completa)
                    
                    # Notificar a Flet que ya tenemos la foto
                    if self.callback_exito:
                        self.callback_exito(ruta_completa)
                        
                    return """
                    <div style="text-align:center; padding:50px; font-family:sans-serif;">
                        <h1 style="color:green;">✅ ¡Listo!</h1>
                        <p>La foto se ha guardado en el sistema.</p>
                        <p>Ya puedes cerrar esta ventana.</p>
                    </div>
                    """
            return HTML_TEMPLATE

    def iniciar_servicio(self, nombre_archivo_destino, callback):
        """
        Arranca el servidor y genera el QR.
        :param nombre_archivo_destino: Ej: 'cliente_juan_golpe1.jpg'
        :param callback: Función que recibe (ruta_foto) cuando termina
        :return: Ruta de la imagen del código QR generado
        """
        self.nombre_archivo_actual = nombre_archivo_destino
        self.callback_exito = callback
        
        ip = self._obtener_ip_local()
        url = f"http://{ip}:{self.puerto}"
        
        # Generar QR
        qr = qrcode.make(url)
        # Usar timestamp para evitar caché del navegador/Flet
        import time
        timestamp_qr = int(time.time())
        ruta_qr = os.path.join(self.directorio, f"temp_qr_code_{timestamp_qr}.png")
        qr.save(ruta_qr)
        
        # Iniciar Flask en hilo secundario si no está corriendo
        # Nota: Flask no se detiene fácilmente, así que usamos daemon=True
        # para que se cierre cuando cierres la app principal.
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(
                target=lambda: self.app.run(host='0.0.0.0', port=self.puerto, use_reloader=False),
                daemon=True
            )
            self.server_thread.start()
            print(f"--- Servidor escuchando en {url} ---")
            
        return ruta_qr, url
        