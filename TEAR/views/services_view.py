import flet as ft
from database import get_db_connection

def ServicesView(page):
    # Search field
    search_field = ft.TextField(label="Buscar servicio", suffix_icon="search", width=300)

    # Data Table
    services_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Precio")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_services(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM services WHERE name LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM services")
        rows = cursor.fetchall()
        conn.close()

        services_table.rows.clear()
        for row in rows:
            services_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["name"])),
                        ft.DataCell(ft.Text(row["description"])),
                        ft.DataCell(ft.Text(f"${row['price']:.2f}")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_service(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_service(service_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            conn.commit()
            conn.close()
            load_services()
            page.open(ft.SnackBar(ft.Text("Servicio eliminado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # Dialog components
    name = ft.TextField(label="Nombre del Servicio", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
    description = ft.TextField(label="Descripción", multiline=True)
    price = ft.TextField(label="Precio", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]"))
    
    def open_edit_dialog(row):
        name.value = row["name"]
        description.value = row["description"]
        price.value = str(row["price"])
        
        dialog.title = ft.Text("Editar Servicio")
        save_button.on_click = lambda e: update_service(row["id"])
        page.open(dialog)

    def update_service(service_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE services SET name=?, description=?, price=? WHERE id=?",
                (name.value, description.value, float(price.value), service_id)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_services()
            page.open(ft.SnackBar(ft.Text("Servicio actualizado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def save_new_service(e):
        if not name.value or not price.value:
            page.open(ft.SnackBar(ft.Text("Nombre y Precio son obligatorios")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO services (name, description, price) VALUES (?, ?, ?)",
                (name.value, description.value, float(price.value))
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_services()
            page.open(ft.SnackBar(ft.Text("Servicio registrado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_service)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Servicio"),
        content=ft.Column([name, description, price], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        name.value = ""
        description.value = ""
        price.value = ""
        
        dialog.title = ft.Text("Registrar Servicio")
        save_button.on_click = save_new_service
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_services(search_field.value)

    search_field.on_change = on_search

    load_services()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Servicios", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nuevo Servicio",
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
                    content=services_table,
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
