import flet as ft
from database import get_db_connection

def ClientsView(page):
    # Search field
    search_field = ft.TextField(label="Buscar por teléfono", suffix_icon="search", width=300)

    # Data Table
    clients_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Apellido")),
            ft.DataColumn(ft.Text("Teléfono")),
            ft.DataColumn(ft.Text("Dirección")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_clients(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM clients WHERE phone LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM clients")
        rows = cursor.fetchall()
        conn.close()

        clients_table.rows.clear()
        for row in rows:
            clients_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["first_name"])),
                        ft.DataCell(ft.Text(row["last_name"])),
                        ft.DataCell(ft.Text(row["phone"])),
                        ft.DataCell(ft.Text(row["address"])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_client(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_client(client_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            conn.close()
            load_clients()
            page.open(ft.SnackBar(ft.Text("Cliente eliminado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    def open_edit_dialog(row):
        # Pre-fill data for editing
        first_name.value = row["first_name"]
        last_name.value = row["last_name"]
        phone.value = row["phone"]
        address.value = row["address"]
        
        # Change save action to update
        dialog.title = ft.Text("Editar Cliente")
        save_button.on_click = lambda e: update_client(row["id"])
        
        # Flet 0.28.3 correct way to open dialogs
        page.open(dialog)

    def update_client(client_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clients SET first_name=?, last_name=?, phone=?, address=? WHERE id=?",
                (first_name.value, last_name.value, phone.value, address.value, client_id)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_clients()
            page.open(ft.SnackBar(ft.Text("Cliente actualizado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    # Dialog components
    first_name = ft.TextField(label="Nombre", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
    last_name = ft.TextField(label="Apellido", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
    phone = ft.TextField(label="Teléfono", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"))
    address = ft.TextField(label="Dirección", multiline=True)
    
    def save_new_client(e):
        if not first_name.value or not last_name.value or not phone.value:
            page.open(ft.SnackBar(ft.Text("Nombre, Apellido y Teléfono son obligatorios")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clients (first_name, last_name, phone, address) VALUES (?, ?, ?, ?)",
                (first_name.value, last_name.value, phone.value, address.value)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_clients()
            page.open(ft.SnackBar(ft.Text("Cliente registrado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_client)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Cliente"),
        content=ft.Column([first_name, last_name, phone, address], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = dialog

    def open_add_dialog(e):
        # Clear fields
        first_name.value = ""
        last_name.value = ""
        phone.value = ""
        address.value = ""
        
        dialog.title = ft.Text("Registrar Cliente")
        save_button.on_click = save_new_client
        
        # Flet 0.28.3 correct way to open dialogs
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_clients(search_field.value)

    search_field.on_change = on_search

    load_clients()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Clientes", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nuevo Cliente",
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
                    content=clients_table,
                    border=ft.border.all(1, "outline"),
                    border_radius=10,
                    padding=10,
                    expand=True,
                    # scroll=ft.ScrollMode.AUTO # DataTable handles its own scrolling usually, but container might need it
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    )
