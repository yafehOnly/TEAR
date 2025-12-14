from fpdf import FPDF
import os
from datetime import datetime

class FinancialReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Taller Eléctrico Automotriz Reyes (TEAR)', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Dirección del Taller: Avenida Paseo Celeste No. 17, Col: San Diego, Tlapa de Comonfort', 0, 1, 'C')
        self.cell(0, 5, 'Tel: 757 118 9515', 0, 1, 'C')
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte Financiero Oficial', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

from database import get_db_connection

def generate_financial_report(start_date, end_date, repair_income_ignored, transactions_raw, expenses, period_name):
    # --- Fetch Invoices Data (Ingresos por Reparaciones) ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.issue_date as date, i.total_amount as amount, i.id, 
               c.first_name, c.last_name, v.brand, v.model
        FROM invoices i
        JOIN repairs r ON i.repair_id = r.id
        JOIN vehicles v ON r.vehicle_id = v.id
        JOIN clients c ON v.client_id = c.id
        WHERE i.issue_date >= ? AND i.issue_date <= ?
    ''', (start_date, end_date))
    invoices_data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # --- Filter Transactions (Otros Ingresos) ---
    # Exclude transactions that are related to repairs (related_repair_id IS NOT NULL)
    # This ensures "Otros Ingresos" are truly extra income.
    other_income_transactions = [t for t in transactions_raw if not t.get('related_repair_id')]

    pdf = FinancialReportPDF()
    pdf.add_page()
    
    # --- Period Info ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Periodo: {period_name}', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f'Desde: {start_date}  Hasta: {end_date}', 0, 1, 'L')
    pdf.ln(5)
    
    # --- Data Processing ---
    # Calculate totals
    total_invoices_income = sum(i['amount'] for i in invoices_data)
    total_other_income = sum(t['amount'] for t in other_income_transactions)
    total_expenses = sum(e['amount'] for e in expenses)
    
    total_income = total_invoices_income + total_other_income
    net_balance = total_income - total_expenses
    
    # --- Executive Summary ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, 'Resumen Ejecutivo', 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 11)
    
    # Helper for summary rows
    def summary_row(label, amount, is_bold=False, color=None):
        if is_bold: pdf.set_font('Arial', 'B', 11)
        else: pdf.set_font('Arial', '', 11)
        
        if color: pdf.set_text_color(*color)
        else: pdf.set_text_color(0, 0, 0)
            
        pdf.cell(140, 8, label, 1)
        pdf.cell(50, 8, f"${amount:,.2f}", 1, 1, 'R')
        
        pdf.set_text_color(0, 0, 0) # Reset

    summary_row('Ingresos por Reparaciones (Facturas)', total_invoices_income)
    summary_row('Otros Ingresos', total_other_income)
    summary_row('Gastos Totales', total_expenses)
    
    # Net Balance Row
    balance_color = (0, 128, 0) if net_balance >= 0 else (255, 0, 0)
    summary_row('Balance Neto', net_balance, is_bold=True, color=balance_color)
    
    pdf.ln(10)
    
    # --- Detailed Sections ---
    
    # 1. Invoices Detail
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, 'Detalle de Ingresos por Reparaciones (Facturas)', 1, 1, 'L', fill=True)
    
    if invoices_data:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Fecha', 1)
        pdf.cell(60, 8, 'Vehículo', 1)
        pdf.cell(60, 8, 'Cliente', 1)
        pdf.cell(40, 8, 'Monto', 1, 1, 'R')
        
        pdf.set_font('Arial', '', 9)
        for i in invoices_data:
            pdf.cell(30, 8, i['date'], 1)
            pdf.cell(60, 8, f"{i['brand']} {i['model']}", 1)
            pdf.cell(60, 8, f"{i['first_name']} {i['last_name']}", 1)
            pdf.cell(40, 8, f"${i['amount']:,.2f}", 1, 1, 'R')
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'No hay facturas registradas en este periodo.', 1, 1, 'C')
        
    pdf.ln(10)
    
    # 2. Other Income Detail
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, 'Otros Ingresos', 1, 1, 'L', fill=True)
    
    if other_income_transactions:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Fecha', 1)
        pdf.cell(120, 8, 'Descripción', 1)
        pdf.cell(40, 8, 'Monto', 1, 1, 'R')
        
        pdf.set_font('Arial', '', 9)
        for t in other_income_transactions:
            pdf.cell(30, 8, t['date'], 1)
            
            # Truncate desc
            desc = t['description']
            if len(desc) > 75: desc = desc[:72] + "..."
            pdf.cell(120, 8, desc, 1)
            
            pdf.cell(40, 8, f"${t['amount']:,.2f}", 1, 1, 'R')
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'No hay otros ingresos registrados en este periodo.', 1, 1, 'C')

    pdf.ln(10)

    # 3. Expenses Detail
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, 'Gastos', 1, 1, 'L', fill=True)
    
    if expenses:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Fecha', 1)
        pdf.cell(30, 8, 'Periodo', 1)
        pdf.cell(90, 8, 'Descripción', 1)
        pdf.cell(40, 8, 'Monto', 1, 1, 'R')
        
        pdf.set_font('Arial', '', 9)
        for e in expenses:
            pdf.cell(30, 8, e['date'], 1)
            pdf.cell(30, 8, e['period_type'], 1)
            
            # Truncate desc
            desc = e['description']
            if len(desc) > 55: desc = desc[:52] + "..."
            pdf.cell(90, 8, desc, 1)
            
            pdf.cell(40, 8, f"${e['amount']:,.2f}", 1, 1, 'R')
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'No hay gastos registrados en este periodo.', 1, 1, 'C')

    # --- Save PDF ---
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    filename = f"reports/reporte_financiero_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename
