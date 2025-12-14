import flet as ft
from database import get_db_connection

def ToolsView(page):
    # Search field
    search_field = ft.TextField(label="Buscar herramienta", suffix_icon="search", width=300)

    # Data Table
    tools_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_tools(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM tools WHERE name LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM tools")
        rows = cursor.fetchall()
        conn.close()

        tools_table.rows.clear()
        for row in rows:
            tools_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["name"])),
                        ft.DataCell(ft.Text(row["description"])),
                        ft.DataCell(ft.Text(str(row["quantity"]))),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_tool(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_tool(tool_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
            conn.commit()
            conn.close()
            load_tools()
            page.open(ft.SnackBar(ft.Text("Herramienta eliminada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # Dialog components
    name = ft.TextField(label="Nombre de la Herramienta")
    description = ft.TextField(label="Descripción", multiline=True)
    quantity = ft.TextField(label="Cantidad", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"))
    
    def open_edit_dialog(row):
        name.value = row["name"]
        description.value = row["description"]
        quantity.value = str(row["quantity"])
        
        dialog.title = ft.Text("Editar Herramienta")
        save_button.on_click = lambda e: update_tool(row["id"])
        page.open(dialog)

    def update_tool(tool_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tools SET name=?, description=?, quantity=? WHERE id=?",
                (name.value, description.value, int(quantity.value), tool_id)
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_tools()
            page.open(ft.SnackBar(ft.Text("Herramienta actualizada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def save_new_tool(e):
        if not name.value:
            page.open(ft.SnackBar(ft.Text("El nombre es obligatorio")))
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tools (name, description, quantity) VALUES (?, ?, ?)",
                (name.value, description.value, int(quantity.value or 1))
            )
            conn.commit()
            conn.close()
            page.close(dialog)
            load_tools()
            page.open(ft.SnackBar(ft.Text("Herramienta registrada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar", on_click=save_new_tool)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Registrar Herramienta"),
        content=ft.Column([name, description, quantity], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        name.value = ""
        description.value = ""
        quantity.value = ""
        
        dialog.title = ft.Text("Registrar Herramienta")
        save_button.on_click = save_new_tool
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_tools(search_field.value)

    search_field.on_change = on_search

    load_tools()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Herramientas", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nueva Herramienta",
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
                    content=tools_table,
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
