import flet as ft
from database import init_db, get_db_connection
from components.sidebar import Sidebar
from views.dashboard_view import DashboardView
from views.users_view import UsersView
from views.clients_view import ClientsView
from views.vehicles_view import VehiclesView
from views.services_view import ServicesView
from views.parts_view import PartsView
from views.technicians_view import TechniciansView
from views.tools_view import ToolsView
from views.repairs_view import RepairsView
from views.invoices_view import InvoicesView
from views.finances_view import FinancesView

def main(page: ft.Page):
    # Initialize Database
    init_db()

    # Page configuration for Flet 0.28.3
    page.title = "TEAR - Taller Eléctrico Automotriz Reyes"
    page.padding = 0
    page.window.min_width = 1000
    page.window.min_height = 700
    page.window.width = 1200
    page.window.height = 800
    
    # Custom Theme Colors (Flet 0.28.3 compatible)
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="amber",
            primary_container="amber900",
            secondary="blue",
            background="grey900",
            surface="grey800",
            surface_variant="grey800",  # For cards
        )
    )

    def navigate(route):
        page.go(route)

    def login(e, username_field, password_field):
        username = username_field.value
        password = password_field.value
        
        import hashlib
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, hashed_password))
        user = cursor.fetchone()
        conn.close()

        if user:
            page.session.set("user_id", user["id"])
            page.session.set("role", user["role"])
            page.session.set("full_name", user["full_name"])
            page.go("/dashboard")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Credenciales incorrectas"))
            page.snack_bar.open = True
            page.update()

    def route_change(route):
        page.views.clear()
        
        # Content area based on route
        content = ft.Container(expand=True)
        
        if page.route == "/":
            # Login View (Full Screen, no Sidebar)
            username_field = ft.TextField(label="Usuario", width=300)
            password_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300)
            
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("TEAR", size=40, weight=ft.FontWeight.BOLD, color="primary"),
                                    ft.Text("Sistema de Gestión del Taller Electrico Automotriz Reyes", size=16),
                                    ft.Container(height=20),
                                    username_field,
                                    password_field,
                                    ft.Container(height=20),
                                    ft.ElevatedButton(
                                        "Iniciar Sesión", 
                                        on_click=lambda e: login(e, username_field, password_field), 
                                        width=300, 
                                        height=50
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            expand=True,
                            bgcolor="background"
                        )
                    ],
                    padding=0
                )
            )
        else:
            # Check if user is logged in
            if not page.session.get("user_id"):
                page.go("/")
                return

            user_role = page.session.get("role")
            restricted_routes = ["/services", "/finances", "/users", "/technicians"]

            if user_role == "technician" and page.route in restricted_routes:
                page.open(ft.SnackBar(ft.Text("Acceso denegado: Solo administradores pueden acceder a esta sección")))
                # Change route to dashboard instead of navigating, to avoid blank screen
                page.route = "/dashboard"

            # Main App Layout (Sidebar + Content)
            if page.route == "/dashboard":
                content = DashboardView(page)
            elif page.route == "/users":
                content = UsersView(page)
            elif page.route == "/clients":
                content = ClientsView(page)
            elif page.route == "/vehicles":
                content = VehiclesView(page)
            elif page.route == "/services":
                content = ServicesView(page)
            elif page.route == "/parts":
                content = PartsView(page)
            elif page.route == "/technicians":
                content = TechniciansView(page)
            elif page.route == "/tools":
                content = ToolsView(page)
            elif page.route == "/repairs":
                content = RepairsView(page)
            elif page.route == "/invoices":
                content = InvoicesView(page)
            elif page.route == "/finances":
                content = FinancesView(page)
            else:
                content = ft.Text(f"Ruta no encontrada: {page.route}")

            page.views.append(
                ft.View(
                    page.route,
                    [
                        ft.Row(
                            [
                                Sidebar(page, navigate),
                                ft.VerticalDivider(width=1),
                                ft.Container(content=content, expand=True, padding=0)
                            ],
                            expand=True,
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH
                        )
                    ],
                    padding=0,
                    bgcolor="background"
                )
            )
        
        page.update()

    def view_pop(view):
        if len(page.views) > 0:
            page.views.pop()
        if len(page.views) > 0:
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/dashboard")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets"
    )
