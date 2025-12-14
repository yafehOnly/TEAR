import flet as ft
from database import get_db_connection
from datetime import datetime, timedelta
from utils.financial_report_generator import generate_financial_report
import os
import threading
import subprocess
from functools import partial

def FinancesView(page):
    # --- UI Components ---
    
    # Extra Income Table (Mini Table)
    income_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Monto")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        heading_row_height=40,
        data_row_min_height=40,
        column_spacing=20,
    )

    # Expense Table (Main Table)
    expenses_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Tipo Periodo")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Monto")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    # Summary Cards
    income_text = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color="green")
    expense_text = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color="red")
    balance_text = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD, color="blue")

    # --- Data Loading (completely synchronous, no threads) ---
    def load_data():
        try:
            # Fast DB query
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE type='Income' ORDER BY date DESC")
            income_rows_data = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
            expense_rows_data = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # Build UI rows
            new_income_rows = []
            total_income = 0
            for row in income_rows_data:
                amount = row["amount"]
                total_income += amount
                new_income_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(row["date"])),
                            ft.DataCell(ft.Text(row["description"])),
                            ft.DataCell(ft.Text(f"${amount:.2f}")),
                            ft.DataCell(
                                ft.IconButton(
                                    "delete", 
                                    icon_color="red", 
                                    tooltip="Eliminar", 
                                    icon_size=20,
                                    on_click=partial(handle_delete_income, row["id"])
                                )
                            ),
                        ]
                    )
                )

            new_expense_rows = []
            total_expense = 0
            for row in expense_rows_data:
                amount = row["amount"]
                total_expense += amount
                new_expense_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row["id"]))),
                            ft.DataCell(ft.Text(row["date"])),
                            ft.DataCell(ft.Text(row["period_type"])),
                            ft.DataCell(ft.Text(row["description"])),
                            ft.DataCell(ft.Text(f"${amount:.2f}")),
                            ft.DataCell(
                                ft.IconButton(
                                    "delete", 
                                    icon_color="red", 
                                    tooltip="Eliminar",
                                    on_click=partial(handle_delete_expense, row["id"])
                                )
                            ),
                        ]
                    )
                )

            # Update data (batch update) - wrapped in try-except
            try:
                income_table.rows = new_income_rows
                expenses_table.rows = new_expense_rows
                income_text.value = f"${total_income:.2f}"
                expense_text.value = f"${total_expense:.2f}"
                balance_text.value = f"${total_income - total_expense:.2f}"
            except:
                # View no longer active, silently ignore
                pass
            
        except Exception as ex:
            print(f"Error loading data: {ex}")

    # --- Deletion Logic ---
    def handle_delete_income(item_id, e):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        load_data()
        try:
            page.update()
        except:
            pass

    def handle_delete_expense(item_id, e):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        load_data()
        try:
            page.update()
        except:
            pass

    # --- Add Dialogs ---
    inc_amount_field = ft.TextField(label="Monto", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]"))
    inc_desc_field = ft.TextField(label="Descripción", multiline=True)
    inc_date_field = ft.TextField(label="Fecha (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))

    def add_income(e):
        if not inc_amount_field.value or not inc_desc_field.value:
            page.open(ft.SnackBar(ft.Text("Monto y Descripción son obligatorios")))
            return
        
        amt = float(inc_amount_field.value)
        desc = inc_desc_field.value
        dt = inc_date_field.value
        
        # Save to DB (fast operation)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (type, amount, description, date) VALUES (?, ?, ?, ?)",
            ("Income", amt, desc, dt)
        )
        conn.commit()
        conn.close()
        
        # Reset fields
        inc_amount_field.value = ""
        inc_desc_field.value = ""
        page.close(income_dialog)
        
        # Reload and update (single batch update)
        load_data()
        try:
            page.update()
        except:
            pass

    income_dialog = ft.AlertDialog(
        title=ft.Text("Registrar Ingreso Extra"),
        content=ft.Column([inc_amount_field, inc_desc_field, inc_date_field], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(income_dialog, 'open', False), page.update())),
            ft.ElevatedButton("Guardar", on_click=add_income),
        ],
    )

    # Expense Dialog
    exp_amount_field = ft.TextField(label="Monto", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]"))
    exp_desc_field = ft.TextField(label="Descripción", multiline=True)
    exp_period_dropdown = ft.Dropdown(
        label="Tipo de Periodo",
        options=[
            ft.dropdown.Option("Semanal"),
            ft.dropdown.Option("Mensual"),
            ft.dropdown.Option("Único"),
        ],
        value="Único"
    )
    exp_date_field = ft.TextField(label="Fecha (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))

    def add_expense(e):
        if not exp_amount_field.value or not exp_desc_field.value:
            page.open(ft.SnackBar(ft.Text("Monto y Descripción son obligatorios")))
            return
        
        amt = float(exp_amount_field.value)
        desc = exp_desc_field.value
        period = exp_period_dropdown.value
        dt = exp_date_field.value
        
        # Save to DB (fast operation)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, period_type, description, date) VALUES (?, ?, ?, ?)",
            (amt, period, desc, dt)
        )
        conn.commit()
        conn.close()
        
        # Reset fields
        exp_amount_field.value = ""
        exp_desc_field.value = ""
        page.close(expense_dialog)
        
        # Reload and update (single batch update)
        load_data()
        try:
            page.update()
        except:
            pass

    expense_dialog = ft.AlertDialog(
        title=ft.Text("Registrar Gasto"),
        content=ft.Column([exp_amount_field, exp_period_dropdown, exp_desc_field, exp_date_field], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(expense_dialog, 'open', False), page.update())),
            ft.ElevatedButton("Guardar", on_click=add_expense),
        ],
    )

    def open_income_dialog(e):
        page.dialog = income_dialog
        page.open(income_dialog)
        page.update()

    def open_expense_dialog(e):
        page.dialog = expense_dialog
        page.open(expense_dialog)
        page.update()

    # --- Report Generation (only threading here, for PDF generation) ---
    report_type_dropdown = ft.Dropdown(
        label="Tipo de Reporte",
        options=[ft.dropdown.Option("Semanal"), ft.dropdown.Option("Mensual")],
        value="Mensual",
        on_change=lambda e: toggle_report_inputs(e)
    )
    
    report_month_dropdown = ft.Dropdown(
        label="Mes",
        options=[
            ft.dropdown.Option("01", "Enero"), ft.dropdown.Option("02", "Febrero"),
            ft.dropdown.Option("03", "Marzo"), ft.dropdown.Option("04", "Abril"),
            ft.dropdown.Option("05", "Mayo"), ft.dropdown.Option("06", "Junio"),
            ft.dropdown.Option("07", "Julio"), ft.dropdown.Option("08", "Agosto"),
            ft.dropdown.Option("09", "Septiembre"), ft.dropdown.Option("10", "Octubre"),
            ft.dropdown.Option("11", "Noviembre"), ft.dropdown.Option("12", "Diciembre"),
        ],
        value=datetime.now().strftime("%m")
    )
    
    report_year_field = ft.TextField(label="Año", value=datetime.now().strftime("%Y"), width=100)
    report_week_date = ft.TextField(label="Fecha (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"), visible=False)

    def toggle_report_inputs(e):
        is_monthly = report_type_dropdown.value == "Mensual"
        report_month_dropdown.visible = is_monthly
        report_year_field.visible = is_monthly
        report_week_date.visible = not is_monthly
        page.update()

    def open_pdf_report(path):
        try:
            if os.name == 'nt': 
                os.startfile(path)
            else: 
                subprocess.Popen(['xdg-open', path])
        except Exception as e: 
            print(f"Error opening PDF: {e}")

    def generate_report(e):
        report_type = report_type_dropdown.value
        start_date = ""
        end_date = ""
        period_name = ""
        
        if report_type == "Mensual":
            year = report_year_field.value
            month = report_month_dropdown.value
            start_date = f"{year}-{month}-01"
            if month == "12": 
                end_date_obj = datetime(int(year)+1, 1, 1)
            else: 
                end_date_obj = datetime(int(year), int(month)+1, 1)
            end_date = (end_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
            period_name = f"Mensual - {month}/{year}"
        else:
            try:
                ref_date = datetime.strptime(report_week_date.value, "%Y-%m-%d")
                start_of_week = ref_date - timedelta(days=ref_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                start_date = start_of_week.strftime("%Y-%m-%d")
                end_date = end_of_week.strftime("%Y-%m-%d")
                period_name = f"Semanal ({start_date} al {end_date})"
            except ValueError:
                return

        def run_generation():
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM transactions WHERE type='Income' AND date >= ? AND date <= ?", (start_date, end_date))
                transactions = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT r.total_cost, r.start_date, r.end_date, v.plate, v.brand, v.model, c.first_name, c.last_name
                    FROM repairs r
                    JOIN vehicles v ON r.vehicle_id = v.id
                    JOIN clients c ON v.client_id = c.id
                    WHERE r.status = 'Completada' 
                    AND (r.end_date >= ? AND r.end_date <= ?)
                ''', (start_date, end_date))
                repair_income = [dict(row) for row in cursor.fetchall()]

                cursor.execute("SELECT * FROM expenses WHERE date >= ? AND date <= ?", (start_date, end_date))
                expenses = [dict(row) for row in cursor.fetchall()]
                conn.close()

                pdf_path = generate_financial_report(start_date, end_date, repair_income, transactions, expenses, period_name)
                
                page.open(ft.SnackBar(
                    content=ft.Text("Reporte generado exitosamente"),
                    action="Abrir PDF",
                    on_action=lambda e: open_pdf_report(os.path.abspath(pdf_path))
                ))
                
            except Exception as ex:
                print(f"Error generating report: {ex}")
                page.open(ft.SnackBar(ft.Text(f"Error al generar reporte: {str(ex)}")))
                
            finally:
                page.close(report_dialog)

        threading.Thread(target=run_generation, daemon=True).start()

    report_dialog = ft.AlertDialog(
        title=ft.Text("Generar Reporte Financiero"),
        content=ft.Column([report_type_dropdown, report_month_dropdown, report_year_field, report_week_date], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(report_dialog, 'open', False), page.update())),
            ft.ElevatedButton("Generar", on_click=generate_report),
        ],
    )

    def open_report_dialog(e):
        page.dialog = report_dialog
        page.open(report_dialog)
        page.update()

    # Initial load
    load_data()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Finanzas", size=30, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.ElevatedButton("Nuevo Ingreso Extra", icon="add", on_click=open_income_dialog, bgcolor="green", color="white"),
                            ft.ElevatedButton("Nuevo Gasto", icon="remove", on_click=open_expense_dialog, bgcolor="red", color="white"),
                            ft.ElevatedButton("Generar Reporte", icon="picture_as_pdf", on_click=open_report_dialog, bgcolor="secondary", color="white")
                        ])
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                ft.Row(
                    [
                        ft.Container(content=ft.Column([ft.Text("Ingresos Extras"), income_text]), bgcolor="surfacevariant", padding=15, border_radius=10, expand=True),
                        ft.Container(content=ft.Column([ft.Text("Gastos Totales"), expense_text]), bgcolor="surfacevariant", padding=15, border_radius=10, expand=True),
                        ft.Container(content=ft.Column([ft.Text("Balance (Extras - Gastos)"), balance_text]), bgcolor="surfacevariant", padding=15, border_radius=10, expand=True),
                    ],
                    spacing=20
                ),
                ft.Container(height=20),
                
                # Extra Income Section
                ft.Text("Ingresos Extras", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=income_table,
                    padding=10,
                    border=ft.border.all(1, "outline"),
                    border_radius=10,
                    height=200,
                ),
                
                ft.Container(height=20),
                
                # Expenses Section
                ft.Text("Gastos", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=expenses_table,
                    padding=10,
                    border=ft.border.all(1, "outline"),
                    border_radius=10,
                    expand=True
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    )
