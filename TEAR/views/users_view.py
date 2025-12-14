import flet as ft
from database import get_db_connection

def UsersView(page):
    # State for the data table
    users_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Usuario")),
            ft.DataColumn(ft.Text("Nombre Completo")),
            ft.DataColumn(ft.Text("Rol")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_users():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()

        users_table.rows.clear()
        for row in rows:
            users_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["username"])),
                        ft.DataCell(ft.Text(row["full_name"])),
                        ft.DataCell(ft.Text(row["role"])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar"),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar")
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def add_user_dialog(e):
        username_field = ft.TextField(label="Usuario")
        password_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
        fullname_field = ft.TextField(label="Nombre Completo", input_filter=ft.InputFilter(allow=True, regex_string=r"[^0-9]"))
        role_dropdown = ft.Dropdown(
            label="Rol",
            options=[
                ft.dropdown.Option("admin"),
                ft.dropdown.Option("technician"),
            ]
        )

        def save_user(e):
            if not username_field.value or not password_field.value or not fullname_field.value or not role_dropdown.value:
                page.open(ft.SnackBar(ft.Text("Todos los campos son obligatorios")))
                return

            try:
                import hashlib
                hashed_password = hashlib.sha256(password_field.value.encode()).hexdigest()
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                    (username_field.value, hashed_password, role_dropdown.value, fullname_field.value)
                )
                conn.commit()
                conn.close()
                page.close(dlg)
                load_users()
                page.open(ft.SnackBar(ft.Text("Usuario registrado exitosamente")))
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

        dlg = ft.AlertDialog(
            title=ft.Text("Registrar Usuario"),
            content=ft.Column([
                username_field,
                password_field,
                fullname_field,
                role_dropdown
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton("Guardar", on_click=save_user),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    load_users()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Usuarios", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nuevo Usuario",
                            icon="add",
                            on_click=add_user_dialog,
                            bgcolor="primary",
                            color="black"
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                ft.Container(
                    content=users_table,
                    border=ft.border.all(1, "outline"),
                    border_radius=10,
                    padding=10
                )
            ]
        )
    )
