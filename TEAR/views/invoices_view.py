import flet as ft
from database import get_db_connection
from utils.pdf_generator import generate_invoice_pdf
import os
from datetime import datetime

def InvoicesView(page):
    # Search field
    search_field = ft.TextField(label="Buscar por cliente o vehículo", suffix_icon="search", width=400)

    # Data Table
    invoices_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Monto Total")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_invoices(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT i.*, c.first_name, c.last_name, v.brand, v.model 
            FROM invoices i
            JOIN repairs r ON i.repair_id = r.id
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN clients c ON v.client_id = c.id
        '''
        
        if search_query:
            query += " WHERE c.first_name LIKE ? OR c.last_name LIKE ? OR v.plate LIKE ?"
            cursor.execute(query, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute(query)
            
        rows = cursor.fetchall()
        conn.close()

        invoices_table.rows.clear()
        for row in rows:
            invoices_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(row["issue_date"])),
                        ft.DataCell(ft.Text(f"{row['first_name']} {row['last_name']}")),
                        ft.DataCell(ft.Text(f"${row['total_amount']:.2f}")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("picture_as_pdf", icon_color="red", tooltip="Ver PDF", on_click=lambda e, path=row["pdf_path"]: open_pdf(path)),
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def open_pdf(path):
        if path and os.path.exists(path):
            os.startfile(os.path.abspath(path))
        else:
            page.open(ft.SnackBar(ft.Text("El archivo PDF no existe")))

    # Dialog for generating new invoice
    repair_dropdown = ft.Dropdown(label="Seleccionar Reparación Completada", width=400)

    def load_completed_repairs():
        conn = get_db_connection()
        cursor = conn.cursor()
        # Only show completed repairs that don't have an invoice yet
        cursor.execute('''
            SELECT r.id, v.brand, v.model, c.first_name, c.last_name, r.total_cost
            FROM repairs r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN clients c ON v.client_id = c.id
            LEFT JOIN invoices i ON r.id = i.repair_id
            WHERE r.status = 'Completada' AND i.id IS NULL
        ''')
        repairs = cursor.fetchall()
        conn.close()
        
        repair_dropdown.options = [
            ft.dropdown.Option(key=str(r["id"]), text=f"#{r['id']} - {r['brand']} {r['model']} ({r['first_name']}) - ${r['total_cost']:.2f}")
            for r in repairs
        ]

    def generate_invoice(e):
        if not repair_dropdown.value:
            page.open(ft.SnackBar(ft.Text("Seleccione una reparación")))
            return

        repair_id = int(repair_dropdown.value)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Repair Data
        cursor.execute('''
            SELECT r.*, v.brand, v.model, v.year, v.plate, c.first_name, c.last_name
            FROM repairs r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN clients c ON v.client_id = c.id
            WHERE r.id = ?
        ''', (repair_id,))
        repair_data = cursor.fetchone()
        
        # Get Services
        cursor.execute('''
            SELECT s.name, rs.price_at_moment 
            FROM repair_services rs 
            JOIN services s ON rs.service_id = s.id 
            WHERE rs.repair_id = ?
        ''', (repair_id,))
        services = cursor.fetchall()
        
        # Get Parts
        cursor.execute('''
            SELECT p.name, rp.quantity, rp.price_at_moment 
            FROM repair_parts rp 
            JOIN parts p ON rp.part_id = p.id 
            WHERE rp.repair_id = ?
        ''', (repair_id,))
        parts = cursor.fetchall()

        # Get Expenses
        cursor.execute('''
            SELECT description, amount 
            FROM repair_expenses 
            WHERE repair_id = ?
        ''', (repair_id,))
        expenses = cursor.fetchall()
        
        # Create Invoice Record
        issue_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO invoices (repair_id, issue_date, total_amount) VALUES (?, ?, ?)",
            (repair_id, issue_date, repair_data["total_cost"])
        )
        invoice_id = cursor.lastrowid
        
        # Generate PDF
        pdf_path = generate_invoice_pdf(repair_data, services, parts, expenses, invoice_id)
        
        # Update Invoice with PDF Path
        cursor.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?", (pdf_path, invoice_id))
        
        # Add Income Transaction
        cursor.execute(
            "INSERT INTO transactions (type, amount, description, date, related_repair_id) VALUES (?, ?, ?, ?, ?)",
            ('Income', repair_data["total_cost"], f"Factura #{invoice_id} - Reparación #{repair_id}", issue_date, repair_id)
        )
        
        conn.commit()
        conn.close()
        
        page.close(dialog)
        load_invoices()
        page.open(ft.SnackBar(ft.Text("Factura generada exitosamente")))
        
        # Open the PDF automatically
        open_pdf(pdf_path)

    generate_button = ft.ElevatedButton("Generar Factura", on_click=generate_invoice)
    
    dialog = ft.AlertDialog(
        title=ft.Text("Generar Nueva Factura"),
        content=ft.Column([
            ft.Text("Solo se muestran reparaciones completadas sin facturar."),
            repair_dropdown
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            generate_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        load_completed_repairs()
        repair_dropdown.value = None
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_invoices(search_field.value)

    search_field.on_change = on_search

    load_invoices()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Facturas", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nueva Factura",
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
                    content=invoices_table,
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
