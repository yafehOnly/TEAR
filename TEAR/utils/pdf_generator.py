from fpdf import FPDF
import os
from datetime import datetime

class PDFInvoice(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Taller Eléctrico Automotriz Reyes (TEAR)', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Dirección del Taller: Avenida Paseo Celeste No. 17, Col: San Diego, Tlapa de Comonfort', 0, 1, 'C')
        self.cell(0, 5, 'Tel: 757 118 9515', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generate_invoice_pdf(repair_data, services, parts, expenses, invoice_number):
    pdf = PDFInvoice()
    pdf.add_page()
    
    # Invoice Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'FACTURA #{invoice_number}', 0, 1, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'R')
    pdf.ln(10)
    
    # Client & Vehicle Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Información del Cliente y Vehículo', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f'Cliente: {repair_data["first_name"]} {repair_data["last_name"]}', 0, 1)
    pdf.cell(0, 5, f'Vehículo: {repair_data["brand"]} {repair_data["model"]} ({repair_data["year"]})', 0, 1)
    pdf.cell(0, 5, f'Placa: {repair_data["plate"]}', 0, 1)
    pdf.ln(10)
    
    # Services Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Servicios Realizados', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(140, 7, 'Descripción', 1)
    pdf.cell(50, 7, 'Precio', 1, 1, 'R')
    
    pdf.set_font('Arial', '', 10)
    total_services = 0
    for s in services:
        pdf.cell(140, 7, s['name'], 1)
        pdf.cell(50, 7, f"${s['price_at_moment']:.2f}", 1, 1, 'R')
        total_services += s['price_at_moment']
        
    pdf.ln(5)
    
    # Parts Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Refacciones Utilizadas', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 7, 'Descripción', 1)
    pdf.cell(20, 7, 'Cant.', 1, 0, 'C')
    pdf.cell(30, 7, 'P. Unit', 1, 0, 'R')
    pdf.cell(40, 7, 'Total', 1, 1, 'R')
    
    pdf.set_font('Arial', '', 10)
    total_parts = 0
    for p in parts:
        subtotal = p['quantity'] * p['price_at_moment']
        pdf.cell(100, 7, p['name'], 1)
        pdf.cell(20, 7, str(p['quantity']), 1, 0, 'C')
        pdf.cell(30, 7, f"${p['price_at_moment']:.2f}", 1, 0, 'R')
        pdf.cell(40, 7, f"${subtotal:.2f}", 1, 1, 'R')
        total_parts += subtotal
        
    pdf.ln(10)

    # Expenses Table
    total_expenses = 0
    if expenses:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Gastos Extra', 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(140, 7, 'Descripción', 1)
        pdf.cell(50, 7, 'Monto', 1, 1, 'R')
        
        pdf.set_font('Arial', '', 10)
        for ex in expenses:
            pdf.cell(140, 7, ex['description'], 1)
            pdf.cell(50, 7, f"${ex['amount']:.2f}", 1, 1, 'R')
            total_expenses += ex['amount']
        
        pdf.ln(10)
    
    # Totals
    grand_total = total_services + total_parts + total_expenses
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(140, 10, 'Total a Pagar:', 0, 0, 'R')
    pdf.cell(50, 10, f"${grand_total:.2f}", 0, 1, 'R')
    
    pdf.ln(20)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, '¡Gracias por su preferencia!', 0, 1, 'C')
    
    # Ensure directory exists
    if not os.path.exists("invoices"):
        os.makedirs("invoices")
        
    filename = f"invoices/factura_{invoice_number}.pdf"
    pdf.output(filename)
    return filename
