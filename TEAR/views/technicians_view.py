import flet as ft
from database import get_db_connection

def TechniciansView(page):
    # Search field
    search_field = ft.TextField(label="Buscar técnico", suffix_icon="search", width=300)

    # Data Table
    technicians_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Apellido")),
            ft.DataColumn(ft.Text("Teléfono")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_technicians(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM technicians WHERE first_name LIKE ? OR last_name LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT * FROM technicians")
        rows = cursor.fetchall()
        conn.close()

        technicians_table.rows.clear()
        for row in rows:
            technicians_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["first_name"])),
                        ft.DataCell(ft.Text(row["last_name"])),
                        ft.DataCell(ft.Text(row["phone"])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_technician(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_technician(tech_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM technicians WHERE id = ?", (tech_id,))
            conn.commit()
            conn.close()
            load_technicians()
            page.open(ft.SnackBar(ft.Text("Técnico eliminado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # Dialog components
    first_name = ft.TextField(label="Nombre", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
    last_name = ft.TextField(label="Apellido", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
    phone = ft.TextField(label="Teléfono", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"))
    
    def open_edit_dialog(row):
        first_name.value = row["first_name"]
        last_name.value = row["last_name"]
        phone.value = row["phone"]
        
        dialog.title = ft.Text("Editar Técnico")
        save_button.on_click = lambda e: update_technician(row["id"])
        page.open(dialog)

    def update_technician(tech_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE technicians SET first_name=?, last_name=?, phone=? WHERE id=?",
                (first_name.value, last_name.value, phone.value, tech_id)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_technicians()
            page.open(ft.SnackBar(ft.Text("Técnico actualizado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def save_new_technician(e):
        if not first_name.value or not last_name.value:
            page.open(ft.SnackBar(ft.Text("Nombre y Apellido son obligatorios")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO technicians (first_name, last_name, phone) VALUES (?, ?, ?)",
                (first_name.value, last_name.value, phone.value)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_technicians()
            page.open(ft.SnackBar(ft.Text("Técnico registrado")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_technician)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Técnico"),
        content=ft.Column([first_name, last_name, phone], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        first_name.value = ""
        last_name.value = ""
        phone.value = ""
        
        dialog.title = ft.Text("Registrar Técnico")
        save_button.on_click = save_new_technician
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_technicians(search_field.value)

    search_field.on_change = on_search

    load_technicians()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Técnicos", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nuevo Técnico",
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
                    content=technicians_table,
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
