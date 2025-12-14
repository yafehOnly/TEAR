import flet as ft
from database import get_db_connection
from datetime import datetime

def RepairsView(page):
    # Search field
    search_field = ft.TextField(label="Buscar por placa o cliente", suffix_icon="search", width=400)

    # Data Table
    repairs_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Vehículo")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Detalles Generales")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Costo Total")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[]
    )

    def load_repairs(search_query=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT r.*, v.plate, v.brand, v.model, c.first_name, c.last_name 
            FROM repairs r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN clients c ON v.client_id = c.id
        '''
        
        if search_query:
            query += " WHERE v.plate LIKE ? OR c.first_name LIKE ? OR c.last_name LIKE ?"
            cursor.execute(query, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute(query)
            
        rows = cursor.fetchall()
        conn.close()

        repairs_table.rows.clear()
        for row in rows:
            status_color = "orange" if row["status"] == "En Proceso" else ("green" if row["status"] == "Completada" else "red")
            repairs_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["id"]))),
                        ft.DataCell(ft.Text(f"{row['brand']} {row['model']} ({row['plate']})")),
                        ft.DataCell(ft.Text(f"{row['first_name']} {row['last_name']}")),
                        ft.DataCell(ft.Text(row["general_details"])),
                        ft.DataCell(ft.Container(content=ft.Text(row["status"], color="white"), bgcolor=status_color, padding=5, border_radius=5)),
                        ft.DataCell(ft.Text(f"${row['total_cost']:.2f}")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton("edit", icon_color="blue", tooltip="Editar/Detalles", on_click=lambda e, r=row: open_edit_dialog(r)),
                                ft.IconButton("delete", icon_color="red", tooltip="Eliminar", on_click=lambda e, id=row["id"]: delete_repair(id))
                            ])
                        ),
                    ]
                )
            )
        page.update()

    def delete_repair(repair_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM repairs WHERE id = ?", (repair_id,))
            cursor.execute("DELETE FROM repair_services WHERE repair_id = ?", (repair_id,))
            cursor.execute("DELETE FROM repair_parts WHERE repair_id = ?", (repair_id,))
            cursor.execute("DELETE FROM repair_expenses WHERE repair_id = ?", (repair_id,))
            conn.commit()
            conn.close()
            load_repairs()
            page.open(ft.SnackBar(ft.Text("Reparación eliminada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error al eliminar: {str(ex)}")))

    # --- Dialog Components ---
    vehicle_dropdown = ft.Dropdown(label="Vehículo")
    technician_dropdown = ft.Dropdown(label="Técnico Responsable")
    status_dropdown = ft.Dropdown(
        label="Estado",
        options=[
            ft.dropdown.Option("En Proceso"),
            ft.dropdown.Option("Completada"),
            ft.dropdown.Option("Cancelada"),
        ],
        value="En Proceso"
    )
    general_details = ft.TextField(label="Detalles Generales", multiline=True)
    
    # Lists for services, parts, and expenses in the dialog
    selected_services = []
    selected_parts = []
    selected_expenses = []
    
    services_list_view = ft.ListView(expand=True, height=150, spacing=10)
    parts_list_view = ft.ListView(expand=True, height=150, spacing=10)
    expenses_list_view = ft.ListView(expand=True, height=150, spacing=10)
    
    service_dropdown = ft.Dropdown(label="Agregar Servicio", expand=True)
    part_dropdown = ft.Dropdown(label="Agregar Refacción", expand=True, on_change=lambda e: update_part_price_field(e))
    part_qty = ft.TextField(label="Cant.", width=60, value="1")
    part_price = ft.TextField(label="Precio Unit.", width=100, value="0.00")

    expense_desc = ft.TextField(label="Descripción Gasto", expand=True)
    expense_amount = ft.TextField(label="Monto", width=100, value="0.00")

    def update_part_price_field(e):
        if not part_dropdown.value: return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT base_price FROM parts WHERE id = ?", (part_dropdown.value,))
        res = cursor.fetchone()
        conn.close()
        if res:
            part_price.value = str(res["base_price"])
            page.update()

    def load_dropdowns():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vehicles
        cursor.execute("SELECT v.id, v.brand, v.model, v.plate, c.first_name, c.last_name FROM vehicles v JOIN clients c ON v.client_id = c.id")
        vehicles = cursor.fetchall()
        vehicle_dropdown.options = [
            ft.dropdown.Option(key=str(v["id"]), text=f"{v['brand']} {v['model']} - {v['plate']} ({v['first_name']})")
            for v in vehicles
        ]
        
        # Technicians
        cursor.execute("SELECT id, first_name, last_name FROM technicians")
        techs = cursor.fetchall()
        technician_dropdown.options = [
            ft.dropdown.Option(key=str(t["id"]), text=f"{t['first_name']} {t['last_name']}")
            for t in techs
        ]
        
        # Services
        cursor.execute("SELECT id, name, price FROM services")
        services = cursor.fetchall()
        service_dropdown.options = [
            ft.dropdown.Option(key=str(s["id"]), text=f"{s['name']} (${s['price']})")
            for s in services
        ]
        
        # Parts
        cursor.execute("SELECT id, name, base_price, stock FROM parts")
        parts = cursor.fetchall()
        part_dropdown.options = [
            ft.dropdown.Option(key=str(p["id"]), text=f"{p['name']} (${p['base_price']}) - Stock: {p['stock']}")
            for p in parts
        ]
        
        conn.close()

    def add_service_to_list(e):
        if not service_dropdown.value: return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_dropdown.value,))
        service = cursor.fetchone()
        conn.close()
        
        selected_services.append({
            "id": service["id"],
            "name": service["name"],
            "price": service["price"]
        })
        update_services_list()

    def add_part_to_list(e):
        if not part_dropdown.value: return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parts WHERE id = ?", (part_dropdown.value,))
        part = cursor.fetchone()
        conn.close()
        
        try:
            price = float(part_price.value)
        except ValueError:
            price = part["base_price"]

        selected_parts.append({
            "id": part["id"],
            "name": part["name"],
            "price": price,
            "quantity": int(part_qty.value)
        })
        update_parts_list()

    def add_expense_to_list(e):
        if not expense_desc.value or not expense_amount.value: return
        try:
            amount = float(expense_amount.value)
        except ValueError:
            return
            
        selected_expenses.append({
            "description": expense_desc.value,
            "amount": amount
        })
        expense_desc.value = ""
        expense_amount.value = "0.00"
        update_expenses_list()

        page.update()

    def update_expenses_list():
        expenses_list_view.controls.clear()
        for ex in selected_expenses:
            expenses_list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(ex["description"]),
                    subtitle=ft.Text(f"${ex['amount']:.2f}"),
                    trailing=ft.IconButton("delete", on_click=lambda e, x=ex: remove_expense(x))
                )
            )
        page.update()

    def update_services_list():
        services_list_view.controls.clear()
        for s in selected_services:
            services_list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(s["name"]),
                    subtitle=ft.Text(f"${s['price']}"),
                    trailing=ft.IconButton("delete", on_click=lambda e, x=s: remove_service(x))
                )
            )
        page.update()

    def update_parts_list():
        parts_list_view.controls.clear()
        for p in selected_parts:
            parts_list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{p['name']} (x{p['quantity']})"),
                    subtitle=ft.Text(f"${p['price'] * p['quantity']}"),
                    trailing=ft.IconButton("delete", on_click=lambda e, x=p: remove_part(x))
                )
            )
        page.update()

    def remove_service(s):
        selected_services.remove(s)
        update_services_list()

    def remove_part(p):
        selected_parts.remove(p)
        update_parts_list()

    def remove_expense(ex):
        selected_expenses.remove(ex)
        update_expenses_list()

    def calculate_total():
        total = 0
        for s in selected_services:
            total += s["price"]
        for p in selected_parts:
            total += p["price"] * p["quantity"]
        for ex in selected_expenses:
            total += ex["amount"]
        return total

    def save_repair(repair_id=None):
        if not vehicle_dropdown.value or not technician_dropdown.value:
            page.open(ft.SnackBar(ft.Text("Vehículo y Técnico son obligatorios")))
            return

        total_cost = calculate_total()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if repair_id:
                # Update existing
                cursor.execute(
                    "UPDATE repairs SET vehicle_id=?, technician_id=?, status=?, general_details=?, total_cost=? WHERE id=?",
                    (vehicle_dropdown.value, technician_dropdown.value, status_dropdown.value, general_details.value, total_cost, repair_id)
                )
                # Clear old relations to re-insert (simplest way)
                cursor.execute("DELETE FROM repair_services WHERE repair_id=?", (repair_id,))
                cursor.execute("DELETE FROM repair_parts WHERE repair_id=?", (repair_id,))
                cursor.execute("DELETE FROM repair_expenses WHERE repair_id=?", (repair_id,))
                new_id = repair_id
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO repairs (vehicle_id, technician_id, status, general_details, start_date, total_cost) VALUES (?, ?, ?, ?, ?, ?)",
                    (vehicle_dropdown.value, technician_dropdown.value, status_dropdown.value, general_details.value, current_date, total_cost)
                )
                new_id = cursor.lastrowid

            # Insert Services
            for s in selected_services:
                cursor.execute("INSERT INTO repair_services (repair_id, service_id, price_at_moment) VALUES (?, ?, ?)",
                               (new_id, s["id"], s["price"]))
            
            # Insert Parts
            for p in selected_parts:
                cursor.execute("INSERT INTO repair_parts (repair_id, part_id, quantity, price_at_moment) VALUES (?, ?, ?, ?)",
                               (new_id, p["id"], p["quantity"], p["price"]))
                # Update stock ? (Optional logic: decrease stock)
                # cursor.execute("UPDATE parts SET stock = stock - ? WHERE id = ?", (p["quantity"], p["id"]))

            # Insert Expenses
            for ex in selected_expenses:
                cursor.execute("INSERT INTO repair_expenses (repair_id, description, amount) VALUES (?, ?, ?)",
                               (new_id, ex["description"], ex["amount"]))

            conn.commit()
            conn.close()
            page.close(dialog)
            load_repairs()
            page.open(ft.SnackBar(ft.Text("Reparación guardada")))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    save_button = ft.ElevatedButton("Guardar Reparación", on_click=lambda e: save_repair(current_repair_id))
    
    dialog = ft.AlertDialog(
        title=ft.Text("Detalles de Reparación"),
        content=ft.Container(
            width=600,
            content=ft.Column([
                vehicle_dropdown,
                technician_dropdown,
                status_dropdown,
                general_details,
                ft.Divider(),
                ft.Text("Servicios", weight=ft.FontWeight.BOLD),
                ft.Row([service_dropdown, ft.IconButton("add", on_click=add_service_to_list)]),
                services_list_view,
                ft.Divider(),
                ft.Divider(),
                ft.Text("Refacciones", weight=ft.FontWeight.BOLD),
                ft.Row([part_dropdown, part_qty, part_price, ft.IconButton("add", on_click=add_part_to_list)]),
                parts_list_view,
                ft.Divider(),
                ft.Text("Gastos Extra", weight=ft.FontWeight.BOLD),
                ft.Row([expense_desc, expense_amount, ft.IconButton("add", on_click=add_expense_to_list)]),
                expenses_list_view
            ], scroll=ft.ScrollMode.AUTO, height=500)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
            save_button,
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    current_repair_id = None

    def open_add_dialog(e):
        nonlocal current_repair_id
        current_repair_id = None
        load_dropdowns()
        vehicle_dropdown.value = None
        technician_dropdown.value = None
        status_dropdown.value = "En Proceso"
        general_details.value = ""
        selected_services.clear()
        selected_parts.clear()
        selected_expenses.clear()
        update_services_list()
        update_parts_list()
        update_expenses_list()
        
        dialog.title = ft.Text("Nueva Reparación")
        page.open(dialog)

    def open_edit_dialog(row):
        nonlocal current_repair_id
        current_repair_id = row["id"]
        load_dropdowns()
        
        vehicle_dropdown.value = str(row["vehicle_id"])
        technician_dropdown.value = str(row["technician_id"])
        status_dropdown.value = row["status"]
        general_details.value = row["general_details"]
        
        # Load existing services/parts for this repair
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT rs.*, s.name FROM repair_services rs JOIN services s ON rs.service_id = s.id WHERE rs.repair_id = ?", (row["id"],))
        db_services = cursor.fetchall()
        selected_services.clear()
        for s in db_services:
            selected_services.append({"id": s["service_id"], "name": s["name"], "price": s["price_at_moment"]})
            
        cursor.execute("SELECT rp.*, p.name FROM repair_parts rp JOIN parts p ON rp.part_id = p.id WHERE rp.repair_id = ?", (row["id"],))
        db_parts = cursor.fetchall()
        selected_parts.clear()
        for p in db_parts:
            selected_parts.append({"id": p["part_id"], "name": p["name"], "price": p["price_at_moment"], "quantity": p["quantity"]})
            
        conn.close()
        
        update_services_list()
        update_parts_list()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repair_expenses WHERE repair_id = ?", (row["id"],))
        db_expenses = cursor.fetchall()
        selected_expenses.clear()
        for ex in db_expenses:
            selected_expenses.append({"description": ex["description"], "amount": ex["amount"]})
        conn.close()
        update_expenses_list()
        
        dialog.title = ft.Text(f"Editar Reparación #{row['id']}")
        page.open(dialog)

    # Search handler
    def on_search(e):
        load_repairs(search_field.value)

    search_field.on_change = on_search

    load_repairs()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Gestión de Reparaciones", size=30, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Nueva Reparación",
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
                    content=repairs_table,
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
