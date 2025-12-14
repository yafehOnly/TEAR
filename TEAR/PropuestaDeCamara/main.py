import flet as ft
from puente_camara import GestorCamaraMovil # Importamos nuestra clase
import time

def main(page: ft.Page):
    page.title = "Taller Automotriz - Registro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 500
    page.window.height = 700

    # Instanciamos nuestra clase helper
    # Las fotos se guardarán en la carpeta "evidencias_taller"
    gestor = GestorCamaraMovil(directorio_guardado="evidencias_taller")

    # --- Elementos de la UI ---
    txt_titulo = ft.Text("Registro de Daños", size=24, weight="bold")
    
    # Campo para simular el ID del auto o cliente
    txt_id_auto = ft.TextField(label="ID Auto / Placa", value="Nissan_Versa_001")
    
    img_qr = ft.Image(width=200, height=200, visible=False)
    txt_instrucciones = ft.Text("Presiona el botón para vincular cámara...", color="grey")
    
    img_resultado = ft.Image(width=300, height=300, fit=ft.ImageFit.CONTAIN, visible=False)
    
    # --- Lógica ---

    def al_recibir_foto(ruta_foto):
        """Esta función se ejecuta automáticamente cuando el celular sube la foto"""
        print(f"Foto recibida en: {ruta_foto}")
        
        # Actualizamos la UI
        # IMPORTANTE: Como esto viene de otro hilo (Flask), a veces es necesario actualizar
        img_qr.visible = False
        txt_instrucciones.value = f"¡Foto capturada exitosamente!\nGuardada en: {ruta_foto}"
        txt_instrucciones.color = "green"
        
        # Truco para refrescar la imagen si se sobreescribe el mismo archivo (añadir timestamp)
        img_resultado.src = f"{ruta_foto}?v={time.time()}" 
        img_resultado.visible = True
        
        page.update()

    def btn_vincular_click(e):
        # 1. Definir nombre del archivo basado en el input
        nombre_foto = f"{txt_id_auto.value}_evidencia.jpg"
        
        # 2. Llamar a nuestra clase para iniciar proceso
        ruta_qr, url_servidor = gestor.iniciar_servicio(
            nombre_archivo_destino=nombre_foto,
            callback=al_recibir_foto
        )
        
        # 3. Mostrar el QR en pantalla
        img_qr.src = ruta_qr
        img_qr.visible = True
        txt_instrucciones.value = f"Escanea el QR. \nSi no funciona, entra en el navegador a:\n{url_servidor}"
        txt_instrucciones.color = "black"
        img_resultado.visible = False
        
        page.update()

    btn_accion = ft.ElevatedButton(
        "Usar Celular como Cámara", 
        icon="camera_alt", 
        on_click=btn_vincular_click,
        bgcolor="blue", color="white"
    )

    # --- Layout ---
    page.add(
        ft.Column([
            txt_titulo,
            txt_id_auto,
            ft.Divider(),
            btn_accion,
            txt_instrucciones,
            img_qr,
            ft.Divider(),
            ft.Text("Vista previa:"),
            img_resultado
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
