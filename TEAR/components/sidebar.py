import flet as ft

def Sidebar(page, on_nav_change):
    def create_nav_button(text, icon, route, is_logout=False):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color="red400" if is_logout else "amber400", size=20),
                    ft.Text(text, color="white", size=14, weight=ft.FontWeight.W_500),
                ],
                spacing=20,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=10,
            ink=True,
            on_click=lambda e: on_nav_change(route),
            bgcolor="transparent",
        )

    return ft.Container(
        width=280,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["grey900", "black"],
        ),
        padding=10,
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Icon("auto_fix_high", size=40, color="amber"),
                        ft.Text("TEAR", size=30, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Taller Reyes", size=14, color="grey400"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(vertical=30),
                    alignment=ft.alignment.center
                ),
                ft.Divider(color="grey800"),
                # Navigation Buttons directly in the main column
                create_nav_button("Dashboard", "dashboard", "/dashboard"),
                create_nav_button("Clientes", "people", "/clients"),
                create_nav_button("Automóviles", "directions_car", "/vehicles"),
                create_nav_button("Servicios", "build", "/services"),
                create_nav_button("Refacciones", "settings", "/parts"),
                create_nav_button("Técnicos", "person", "/technicians"),
                create_nav_button("Reparaciones", "car_repair", "/repairs"),
                create_nav_button("Facturas", "receipt", "/invoices"),
                create_nav_button("Finanzas", "attach_money", "/finances"),
                create_nav_button("Herramientas", "construction", "/tools"),
                create_nav_button("Usuarios", "supervised_user_circle", "/users"),
                
                ft.Container(expand=True), # Push logout to bottom
                
                ft.Divider(color="grey800"),
                create_nav_button("Cerrar Sesión", "logout", "/", is_logout=True),
            ],
            spacing=5,
        )
    )
