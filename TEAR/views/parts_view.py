import flet as ft
from database import get_db_connection

def PartsView(page):
    # Search field
    search_field = ft.TextField(label="Buscar refacción", suffix_icon="search", width=300)

    # Data Table
    parts_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Stock")),
            ft.DataColumn(ft.Text("Precio Base")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_parts(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM parts WHERE name LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM parts")
        rows = cursor.fetchall()
        conn.close()

        parts_table.rows.clear()
        for row in rows:
            parts_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["name"])),
                        ft.DataCell(ft.Text(str(row["stock"]))),
                        ft.DataCell(ft.Text(f"${row['base_price']:.2f}")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_part(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_part(part_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM parts WHERE id = ?", (part_id,))
            conn.commit()
            conn.close()
            load_parts()
            page.open(ft.SnackBar(ft.Text("Refacción eliminada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # Dialog components
    name = ft.TextField(label="Nombre de la Refacción")
    stock = ft.TextField(label="Stock", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"))
    base_price = ft.TextField(label="Precio Base", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]"))
    
    def open_edit_dialog(row):
        name.value = row["name"]
        stock.value = str(row["stock"])
        base_price.value = str(row["base_price"])
        
        dialog.title = ft.Text("Editar Refacción")
        save_button.on_click = lambda e: update_part(row["id"])
        page.open(dialog)

    def update_part(part_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE parts SET name=?, stock=?, base_price=? WHERE id=?",
                (name.value, int(stock.value), float(base_price.value), part_id)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_parts()
            page.open(ft.SnackBar(ft.Text("Refacción actualizada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def save_new_part(e):
        if not name.value or not base_price.value:
            page.open(ft.SnackBar(ft.Text("Nombre y Precio son obligatorios")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO parts (name, stock, base_price) VALUES (?, ?, ?)",
                (name.value, int(stock.value or 0), float(base_price.value))
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_parts()
            page.open(ft.SnackBar(ft.Text("Refacción registrada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_part)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Refacción"),
        content=ft.Column([name, stock, base_price], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        name.value = ""
        stock.value = ""
        base_price.value = ""
        
        dialog.title = ft.Text("Registrar Refacción")
        save_button.on_click = save_new_part
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_parts(search_field.value)

    search_field.on_change = on_search

    load_parts()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Refacciones", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nueva Refacción",
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
                    content=parts_table,
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
