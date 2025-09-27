import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Load translations
with open("translations.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

styles = getSampleStyleSheet()
normal = styles["Normal"]
bold = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")
small = ParagraphStyle("Small", parent=normal, fontSize=8)

st.title("Invoice Generator")

# Form fields
with st.form("invoice_form"):
    order_date = st.date_input("Order Date")
    order_number = st.text_input("Order Number")
    customer_name = st.text_input("Customer Name")
    customer_address = st.text_area("Customer Address")
    invoice_date = st.date_input("Invoice Date")
    invoice_number = st.text_input("Invoice Number")
    product_description = st.text_area("Product Description")
    qty = st.number_input("Quantity", min_value=1, value=1)
    unit_price = st.number_input("Unit Price", min_value=0.0, format="%.2f")
    vat_rate = st.text_input("VAT Rate", value="0 %")
    asin = st.text_input("ASIN")
    delivery_price = st.number_input("Delivery Price", min_value=0.0, format="%.2f", value=0.0)
    shipping_discount = st.number_input("Shipping Discount", format="%.2f", value=0.0)
    country = st.selectbox("Invoice Language / Country", list(translations.keys()))
    seller_name = st.text_input("Seller Name")
    seller_address_line1 = st.text_input("Seller Address Line 1")
    seller_address_line2 = st.text_input("Seller Address Line 2")
    seller_vat = st.text_input("Seller VAT")
    commercial_name = st.text_input("Commercial Name")
    commercial_address_line1 = st.text_input("Commercial Address Line 1")
    commercial_address_line2 = st.text_input("Commercial Address Line 2")
    commercial_vat = st.text_input("Commercial VAT")

    submitted = st.form_submit_button("Generate Invoice")

def build_invoice(data, lang):
    tr = translations.get(lang, translations["EN"])
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    story = []
    # Header
    story.append(Paragraph(tr["invoice"], styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(tr["shipped_from"], normal))
    story.append(Spacer(1, 12))

    # Info
    info_table = [
        [Paragraph(tr["order_date"], bold), Paragraph(str(data["order_date"]), normal)],
        [Paragraph(tr["order_number"], bold), Paragraph(data["order_number"], normal)],
        [Paragraph(tr["ordered_by"], bold), Paragraph(data["customer_name"], normal)],
        [Paragraph(tr["sold_by"], bold), Paragraph(data["seller_name"], normal)],
        [Paragraph(tr["vat"], bold), Paragraph(data["seller_vat"], normal)],
        [Paragraph(tr["invoice_number"], bold), Paragraph(data["invoice_number"], normal)],
        [Paragraph(tr["invoice_date"], bold), Paragraph(str(data["invoice_date"]), normal)],
    ]
    t = Table(info_table, colWidths=[85*mm, 75*mm])
    story.append(t)
    story.append(Spacer(1, 12))

    # Addresses
    addresses_table = [[
        [
            Paragraph(tr["billing_address"], bold),
            Paragraph(data["customer_name"], normal),
            Paragraph(data["customer_address"], normal),
            Spacer(1,6),
            Paragraph(tr["commercial_address"], bold),
            Paragraph(data["commercial_name"], normal),
            Paragraph(data["commercial_address_line1"], normal),
            Paragraph(data["commercial_address_line2"], normal),
            Paragraph(f"{tr['vat']} {data['commercial_vat']}", normal),
        ],
        [
            Paragraph(tr["shipping_address"], bold),
            Paragraph(data["customer_name"], normal),
            Paragraph(data["customer_address"], normal),
            Spacer(1,6),
            Paragraph(tr["sold_by"], bold),
            Paragraph(data["seller_name"], normal),
            Paragraph(data["seller_address_line1"], normal),
            Paragraph(data["seller_address_line2"], normal),
            Paragraph(f"{tr['vat']} {data['seller_vat']}", normal),
        ]
    ]]
    addresses = Table(addresses_table, colWidths=[85*mm, 85*mm])
    addresses.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(addresses)
    story.append(Spacer(1, 12))

    # Items
    item_headers = [
        Paragraph(tr["description"], bold),
        Paragraph(tr["qty"], bold),
        Paragraph(tr["unit_price_ht"], bold),
        Paragraph(tr["vat_rate"] + " %", bold),
        Paragraph(tr["unit_price_ttc"], bold),
        Paragraph(tr["total_ttc"], bold),
    ]
    item_row = [
        Paragraph(data["product_description"], normal),
        Paragraph(str(data["qty"]), normal),
        Paragraph(f"{data['unit_price']:.2f} €", normal),
        Paragraph(data["vat_rate"], normal),
        Paragraph(f"{data['unit_price']:.2f} €", normal),
        Paragraph(f"{data['total']:.2f} €", normal),
    ]
    asin_row = [Paragraph(f"ASIN: {data['asin']}", normal)] + [""]*5
    delivery_row = [
        Paragraph(tr["delivery"], normal),
        "1", f"{data['delivery_price']:.2f} €", "0 %", f"{data['delivery_price']:.2f} €", f"{data['delivery_price']:.2f} €"
    ]
    discount_row = [
        Paragraph(tr.get("shipping_discount", "Shipping Discount"), normal),
        "1", f"{data['shipping_discount']:.2f} €", "0 %", f"{data['shipping_discount']:.2f} €", f"{data['shipping_discount']:.2f} €"
    ] if data['shipping_discount'] != 0 else None

    rows = [item_headers, item_row, asin_row, delivery_row]
    if discount_row:
        rows.append(discount_row)

    items_table = Table(rows, colWidths=[65*mm, 15*mm, 25*mm, 20*mm, 30*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # Totals
    base_total = data["total"]
    invoice_total = base_total + data["delivery_price"] + data["shipping_discount"]

    totals_table = [
        [Paragraph(tr["totals_vat_rate"] + " %", bold),
         Paragraph(tr["totals_total_ht"], bold),
         Paragraph(tr["totals_vat"], bold)],
        [data["vat_rate"], f"{data['unit_price']:.2f} €", "0,00 €"],
        ["", tr["totals_total"], f"{invoice_total:.2f} €"],
        ["", tr["totals_invoice_total"], f"{invoice_total:.2f} €"],
    ]
    t2 = Table(totals_table, colWidths=[40*mm, 60*mm, 60*mm])
    t2.setStyle(TableStyle([
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))

    # Footer
    story.append(Paragraph(tr["customer_service"], small))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", color=colors.black))
    story.append(Spacer(1, 6))
    story.append(Paragraph(tr["legal"], small))

    doc.build(story)
    buffer.seek(0)
    return buffer

if submitted:
    # Collect all data into dict
    data = dict(
        order_date=order_date, order_number=order_number,
        customer_name=customer_name, customer_address=customer_address,
        invoice_date=invoice_date, invoice_number=invoice_number,
        product_description=product_description, qty=qty,
        unit_price=unit_price, vat_rate=vat_rate, asin=asin,
        delivery_price=delivery_price, shipping_discount=shipping_discount,
        total=qty * unit_price, country=country,
        seller_name=seller_name, seller_address_line1=seller_address_line1,
        seller_address_line2=seller_address_line2, seller_vat=seller_vat,
        commercial_name=commercial_name,
        commercial_address_line1=commercial_address_line1,
        commercial_address_line2=commercial_address_line2,
        commercial_vat=commercial_vat
    )
    pdf = build_invoice(data, country)
    st.download_button("Download Invoice PDF",
                       data=pdf,
                       file_name=f"{invoice_number}_{country}.pdf",
                       mime="application/pdf")
