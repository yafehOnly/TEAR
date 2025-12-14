import flet as ft
from database import get_db_connection
import datetime

def DashboardView(page):
    # Fetch Data
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM clients")
    clients_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    vehicles_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM repairs WHERE status='En Proceso'")
    active_repairs_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    total_income = cursor.fetchone()[0] or 0.0
    
    # Chart Data (Last 6 months income)
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) 
        FROM transactions 
        WHERE type='Income' 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 6
    """)
    chart_data = cursor.fetchall()
    conn.close()

    # Prepare Chart Groups
    chart_groups = []
    if chart_data:
        # Reverse to show oldest to newest
        for i, row in enumerate(reversed(chart_data)):
            chart_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=row[1],
                            width=20,
                            color="amber",
                            tooltip=f"{row[0]}: ${row[1]:.2f}",
                            border_radius=5
                        )
                    ]
                )
            )
    
    bottom_axis = ft.ChartAxis(
        labels=[
            ft.ChartAxisLabel(value=i, label=ft.Text(row[0][5:], size=10)) 
            for i, row in enumerate(reversed(chart_data))
        ]
    )

    return ft.Container(
        padding=30,
        content=ft.Column(
            [
                ft.Text("Dashboard", size=35, weight=ft.FontWeight.BOLD),
                ft.Text(f"Bienvenido, {page.session.get('full_name') or 'Usuario'}", size=16, color="grey400"),
                ft.Divider(height=30, color="transparent"),
                
                # Summary Cards
                ft.Row(
                    [
                        _build_summary_card("Clientes", str(clients_count), "people", "blue"),
                        _build_summary_card("Autos", str(vehicles_count), "directions_car", "orange"),
                        _build_summary_card("En Proceso", str(active_repairs_count), "build_circle", "red"),
                        _build_summary_card("Ingresos", f"${total_income:,.2f}", "attach_money", "green"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                    run_spacing=20,
                ),
                
                ft.Divider(height=30, color="transparent"),
                
                # Chart Section
                ft.Container(
                    padding=20,
                    bgcolor="surfacevariant",
                    border_radius=15,
                    content=ft.Column([
                        ft.Text("Ingresos Mensuales", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.BarChart(
                            bar_groups=chart_groups,
                            bottom_axis=bottom_axis,
                            left_axis=ft.ChartAxis(labels_size=40),
                            border=ft.border.all(1, "grey800"),
                            horizontal_grid_lines=ft.ChartGridLines(color="grey800", width=1, dash_pattern=[3, 3]),
                            tooltip_bgcolor="grey900",
                            max_y=max([row[1] for row in chart_data]) * 1.2 if chart_data else 1000,
                            height=300,
                        ) if chart_data else ft.Text("No hay datos suficientes para mostrar el gráfico.", color="grey500")
                    ])
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )
    )

def _build_summary_card(title, value, icon, color):
    return ft.Container(
        width=250,
        height=140,
        bgcolor="surfacevariant",
        border_radius=15,
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icon, color=color, size=30),
                            padding=10,
                            bgcolor="surfacevariant",
                            border_radius=10
                        ),
                        ft.Text(title, size=14, weight=ft.FontWeight.W_500, color="grey400")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Text(value, size=28, weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        animate=300,
    )
