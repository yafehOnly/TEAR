import flet as ft
from database import get_db_connection
from utils.camera_bridge import GestorCamaraMovil
import time
import os
from datetime import datetime, timedelta

def VehiclesView(page):
    # Initialize Camera Manager
    # Photos will be saved in 'assets/vehicle_photos'
    camera_manager = GestorCamaraMovil(directorio_guardado="assets/vehicle_photos")

    # Search field
    search_field = ft.TextField(label="Buscar por placa o teléfono de cliente", suffix_icon="search", width=400)

    # Data Table
    vehicles_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Marca")),
            ft.DataColumn(ft.Text("Modelo")),
            ft.DataColumn(ft.Text("Año")),
            ft.DataColumn(ft.Text("Placa")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Foto")), # New column
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_vehicles(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT v.*, c.first_name, c.last_name, c.phone 
            FROM vehicles v
            JOIN clients c ON v.client_id = c.id
        '''
        
        if search_query:
            query += " WHERE v.plate LIKE ? OR c.phone LIKE ?"
            cursor.execute(query, (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute(query)
            
        rows = cursor.fetchall()
        conn.close()

        vehicles_table.rows.clear()
        for row in rows:
            photo_icon = ft.Icon("photo_camera", color="grey")
            # Check if photo_path exists and is not None
            has_photo = False
            try:
                if row["photo_path"]:
                    has_photo = True
            except IndexError:
                pass

            if has_photo: # Check if photo exists
                photo_icon = ft.IconButton(
                    "photo", 
                    icon_color="blue", 
                    tooltip="Ver Foto",
                    on_click=lambda e, path=row["photo_path"]: show_photo_dialog(path)
                )

            vehicles_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["brand"])),
                        ft.DataCell(ft.Text(row["model"])),
                        ft.DataCell(ft.Text(str(row["year"]))),
                        ft.DataCell(ft.Text(row["plate"])),
                        ft.DataCell(ft.Text(f"{row['first_name']} {row['last_name']}")),
                        ft.DataCell(photo_icon),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("history", icon_color="orange", tooltip="Historial", on_click=lambda e, id=row["id"]: show_history_dialog(id)),
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_vehicle(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def show_photo_dialog(path):
        # Dialog to show the photo
        photo_dlg = ft.AlertDialog(
            title=ft.Text("Evidencia Fotográfica"),
            content=ft.Image(src=path, width=400, height=400, fit=ft.ImageFit.CONTAIN),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(photo_dlg))],
        )
        page.open(photo_dlg)

    def show_history_dialog(vehicle_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicle_history WHERE vehicle_id = ? ORDER BY created_at DESC", (vehicle_id,))
        history_rows = cursor.fetchall()
        conn.close()

        history_list = ft.ListView(expand=True, spacing=10, padding=20)
        
        if not history_rows:
            history_list.controls.append(ft.Text("No hay historial registrado para este vehículo."))
        
        for row in history_rows:
            img_control = ft.Container()
            if row["photo_path"] and os.path.exists(row["photo_path"]):
                img_control = ft.Image(src=row["photo_path"], width=200, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10)
            
            # Convert UTC to Mexico City time (UTC-6)
            # SQLite stores as "YYYY-MM-DD HH:MM:SS"
            try:
                utc_time = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
                mexico_time = utc_time - timedelta(hours=6)
                formatted_time = mexico_time.strftime("%d/%m/%Y %I:%M %p")
            except ValueError:
                formatted_time = row['created_at'] # Fallback if format is different

            history_list.controls.append(
                ft.Container(
                    padding=10,
                    bgcolor="surfacevariant",
                    border_radius=10,
                    content=ft.Column([
                        ft.Text(f"Fecha: {formatted_time}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Detalles: {row['description']}"),
                        img_control
                    ])
                )
            )

        history_dlg = ft.AlertDialog(
            title=ft.Text("Historial de Detalles"),
            content=ft.Container(width=500, height=600, content=history_list),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(history_dlg))],
        )
        page.open(history_dlg)

    def delete_vehicle(vehicle_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
            cursor.execute("DELETE FROM vehicle_history WHERE vehicle_id = ?", (vehicle_id,)) # Clean history
            conn.commit()
            conn.close()
            load_vehicles()
            page.open(ft.SnackBar(ft.Text("Vehículo eliminado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # Dialog components
    brand = ft.TextField(label="Marca")
    model = ft.TextField(label="Modelo")
    year = ft.TextField(label="Año", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"))
    plate = ft.TextField(label="Placa")
    details = ft.TextField(label="Detalles (Golpes, rayones, etc.)", multiline=True)
    client_dropdown = ft.Dropdown(label="Cliente Propietario")
    
    # Camera UI components
    img_qr = ft.Image(width=150, height=150, visible=False)
    txt_instrucciones = ft.Text("Presiona 'Vincular Cámara' para añadir foto...", color="grey", size=12)
    img_resultado = ft.Image(width=200, height=200, fit=ft.ImageFit.CONTAIN, visible=False)
    current_photo_path = None # Variable to store the path of the taken photo

    def on_photo_received(path):
        nonlocal current_photo_path
        current_photo_path = path
        print(f"Foto recibida: {path}")
        
        # Update UI
        img_qr.visible = False
        txt_instrucciones.value = "¡Foto capturada exitosamente!"
        txt_instrucciones.color = "green"
        
        # Refresh image with timestamp to avoid cache
        img_resultado.src = f"{path}?v={time.time()}"
        img_resultado.visible = True
        page.update()

    def btn_vincular_click(e):
        if not plate.value:
            page.open(ft.SnackBar(ft.Text("Primero ingresa la placa para nombrar la foto")))
            return

        # Use timestamp to ensure unique filename for history
        filename = f"{plate.value}_{int(time.time())}_evidencia.jpg"
        
        ruta_qr, url = camera_manager.iniciar_servicio(
            nombre_archivo_destino=filename,
            callback=on_photo_received
        )
        
        img_qr.src = ruta_qr
        img_qr.visible = True
        txt_instrucciones.value = f"Escanea el QR con tu celular.\nO entra a: {url}"
        txt_instrucciones.color = "black"
        img_resultado.visible = False
        page.update()

    btn_camera = ft.ElevatedButton(
        "Vincular Cámara", 
        icon="camera_alt", 
        on_click=btn_vincular_click,
        bgcolor="bluegrey100",
        color="black"
    )

    def load_clients_for_dropdown():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, phone FROM clients")
        clients = cursor.fetchall()
        conn.close()
        
        client_dropdown.options = [
            ft.dropdown.Option(key=str(c["id"]), text=f"{c['first_name']} {c['last_name']} ({c['phone']})")
            for c in clients
        ]

    def open_edit_dialog(row):
        nonlocal current_photo_path
        load_clients_for_dropdown()
        brand.value = row["brand"]
        model.value = row["model"]
        year.value = str(row["year"])
        plate.value = row["plate"]
        details.value = row["details"]
        client_dropdown.value = str(row["client_id"])
        
        # Load existing photo if any
        try:
            current_photo_path = row["photo_path"]
        except IndexError:
            current_photo_path = None
        if current_photo_path and os.path.exists(current_photo_path):
            img_resultado.src = current_photo_path
            img_resultado.visible = True
            txt_instrucciones.value = "Foto actual cargada."
        else:
            img_resultado.visible = False
            txt_instrucciones.value = "Sin foto registrada."
            
        img_qr.visible = False
        
        dialog.title = ft.Text("Editar Vehículo")
        save_button.on_click = lambda e: update_vehicle(row["id"])
        page.open(dialog)

    def update_vehicle(vehicle_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE vehicles SET client_id=?, brand=?, model=?, year=?, plate=?, details=?, photo_path=? WHERE id=?",
                (client_dropdown.value, brand.value, model.value, year.value, plate.value, details.value, current_photo_path, vehicle_id)
            )
            
            # Add to history if there are details or a photo
            # We add to history on every edit to track state changes
            cursor.execute(
                "INSERT INTO vehicle_history (vehicle_id, description, photo_path) VALUES (?, ?, ?)",
                (vehicle_id, details.value, current_photo_path)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_vehicles()
            page.open(ft.SnackBar(ft.Text("Vehículo actualizado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def save_new_vehicle(e):
        if not brand.value or not model.value or not plate.value or not client_dropdown.value:
            page.open(ft.SnackBar(ft.Text("Marca, Modelo, Placa y Cliente son obligatorios")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO vehicles (client_id, brand, model, year, plate, details, photo_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (client_dropdown.value, brand.value, model.value, year.value, plate.value, details.value, current_photo_path)
            )
            new_id = cursor.lastrowid
            
            # Insert initial history
            cursor.execute(
                "INSERT INTO vehicle_history (vehicle_id, description, photo_path) VALUES (?, ?, ?)",
                (new_id, details.value, current_photo_path)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_vehicles()
            page.open(ft.SnackBar(ft.Text("Vehículo registrado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_vehicle)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Vehículo"),
        content=ft.Container(
            width=500,
            content=ft.Column([
                client_dropdown, 
                brand, 
                model, 
                year, 
                plate, 
                details,
                ft.Divider(),
                ft.Text("Evidencia Fotográfica", weight=ft.FontWeight.BOLD),
                btn_camera,
                txt_instrucciones,
                img_qr,
                img_resultado
            ], scroll=ft.ScrollMode.AUTO, height=500)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        nonlocal current_photo_path
        load_clients_for_dropdown()
        brand.value = ""
        model.value = ""
        year.value = ""
        plate.value = ""
        details.value = ""
        client_dropdown.value = None
        
        # Reset camera UI
        current_photo_path = None
        img_qr.visible = False
        img_resultado.visible = False
        txt_instrucciones.value = "Presiona 'Vincular Cámara' para añadir foto..."
        txt_instrucciones.color = "grey"
        
        dialog.title = ft.Text("Registrar Vehículo")
        save_button.on_click = save_new_vehicle
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_vehicles(search_field.value)

    search_field.on_change = on_search

    load_vehicles()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Automóviles", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nuevo Automóvil",
                            icon="add",
                            on_click=open_add_dialog,
                            bgcolor="primary",
                            color="black"
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                ft.Row([search_field], alignment=ft.MainAxisAlignment.END),
                ft.Container(
                    content=vehicles_table,
                    border=ft.border.all(1, "outline"),
                    border_radius=10,
                    padding=10,
                    expand=True,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    )
