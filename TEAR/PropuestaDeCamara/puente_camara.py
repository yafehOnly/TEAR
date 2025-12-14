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
            <style>
                body { font-family: sans-serif; text-align: center; padding: 20px; background: #f4f4f4; }
                .btn-upload {
                    background-color: #28a745; color: white; padding: 20px;
                    border: none; border-radius: 10px; font-size: 20px;
                    width: 100%; margin-top: 20px; cursor: pointer;
                }
                .input-file { 
                    font-size: 18px; padding: 10px; margin: 20px 0; 
                    width: 100%; background: white; border-radius: 5px;
                }
                h2 { color: #333; }
            </style>
        </head>
        <body>
            <h2>📸 Subir Evidencia</h2>
            <p>Toma una foto del daño o selecciona una de la galería.</p>
            <form method="post" enctype="multipart/form-data">
                <input class="input-file" type="file" name="file" accept="image/*" capture="environment">
                <br>
                <input class="btn-upload" type="submit" value="Enviar Foto al Sistema">
            </form>
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
        ruta_qr = os.path.join(self.directorio, "temp_qr_code.png")
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
        