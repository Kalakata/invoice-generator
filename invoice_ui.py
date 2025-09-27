import streamlit as st
import pandas as pd
import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io, base64, datetime

# Load translations
with open("translations.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

# ===== Session-Based Data Logging System =====
def add_to_session_log(order_info, products, pdf_bytes):
    """Add invoice data to session state for current session"""
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "invoice_number": order_info.get("invoice_number", ""),
        "order_number": order_info.get("order_number", ""),
        "customer_info": {
            "customer_name": order_info.get("customer_name", ""),
            "customer_vat": order_info.get("customer_vat", "")
        },
        "seller_info": {
            "seller_name": order_info.get("seller_name", ""),
            "seller_vat": order_info.get("seller_vat", "")
        },
        "order_details": {
            "order_date": str(order_info.get("order_date", "")),
            "invoice_date": str(order_info.get("invoice_date", ""))
        },
        "addresses": {
            "commercial_address": order_info.get("commercial_address", ""),
            "shipping_address": order_info.get("shipping_address", "")
        },
        "payment_info": {
            "payment_reference": order_info.get("payment_ref", ""),
            "currency": order_info.get("currency", ""),
            "language": order_info.get("language", "")
        },
        "delivery_info": {
            "delivery_charges": order_info.get("delivery_charges", 0),
            "delivery_discount_percent": order_info.get("delivery_discount_percent", 0),
            "delivery_discount_amount": order_info.get("delivery_discount_amount", 0),
            "promotion_description": order_info.get("promotion_description", "")
        },
        "products": [
            {
                "description": product.get("product_description", ""),
                "asin": product.get("asin", ""),
                "quantity": product.get("qty", 0),
                "unit_price_ht": product.get("unit_price", 0),
                "unit_price_ttc": product.get("unit_price_ttc", 0),
                "vat_rate": product.get("vat_rate", 0)
            }
            for product in products
        ],
        "totals": {
            "total_products": len(products),
            "pdf_size_bytes": len(pdf_bytes),
            "pdf_generated": True
        }
    }
    
    # Initialize session log if it doesn't exist
    if "invoice_log" not in st.session_state:
        st.session_state["invoice_log"] = []
    
    # Add new entry to session
    st.session_state["invoice_log"].append(log_entry)

styles = getSampleStyleSheet()
normal = styles["Normal"]
bold = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")
small = ParagraphStyle("Small", parent=normal, fontSize=8)

# Modern color scheme
class ModernColors:
    # Primary colors
    PRIMARY_BLUE = colors.HexColor('#2E86AB')      # Professional blue
    SECONDARY_BLUE = colors.HexColor('#A23B72')    # Accent color
    DARK_GREY = colors.HexColor('#2C3E50')         # Dark text
    LIGHT_GREY = colors.HexColor('#ECF0F1')        # Light background
    WHITE = colors.HexColor('#FFFFFF')             # Pure white
    BORDER_GREY = colors.HexColor('#BDC3C7')       # Subtle borders
    
    # Status colors
    SUCCESS_GREEN = colors.HexColor('#27AE60')     # Success/payment
    WARNING_ORANGE = colors.HexColor('#F39C12')    # Warning
    ERROR_RED = colors.HexColor('#E74C3C')         # Error

# Modern paragraph styles
modern_title = ParagraphStyle("ModernTitle", parent=normal, 
                             fontName="Helvetica-Bold", fontSize=24, 
                             textColor=ModernColors.DARK_GREY,
                             spaceAfter=20)

modern_header = ParagraphStyle("ModernHeader", parent=normal,
                              fontName="Helvetica-Bold", fontSize=14,
                              textColor=ModernColors.PRIMARY_BLUE,
                              spaceAfter=8)

modern_subheader = ParagraphStyle("ModernSubheader", parent=normal,
                                 fontName="Helvetica-Bold", fontSize=12,
                                 textColor=ModernColors.DARK_GREY,
                                 spaceAfter=6)

modern_text = ParagraphStyle("ModernText", parent=normal,
                            fontName="Helvetica", fontSize=10,
                            textColor=ModernColors.DARK_GREY,
                            spaceAfter=4)

modern_small = ParagraphStyle("ModernSmall", parent=normal,
                             fontName="Helvetica", fontSize=9,
                             textColor=colors.HexColor('#7F8C8D'),
                             spaceAfter=4)

def build_invoice(order_info, items, lang="FR"):
    tr = translations.get(lang, translations["FR"])
    currency = order_info.get("currency", "EUR")
    currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£", "CAD": "C$", "AUD": "A$"}[currency]
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    story = []

    # ===== Modern Header =====
    story.append(Paragraph(tr["invoice"], modern_title))
    
    # Payment status with modern styling - only show if payment reference exists and is not empty
    if order_info.get("payment_ref") and order_info["payment_ref"].strip():
        payment_style = ParagraphStyle("PaymentStatus", parent=normal,
                                      fontName="Helvetica-Bold", fontSize=12,
                                      textColor=ModernColors.SUCCESS_GREEN,
                                      spaceAfter=4)
        story.append(Paragraph("✓ Payé", payment_style))
        story.append(Paragraph(f"{tr['payment_ref']} {order_info['payment_ref']}", modern_text))
    
    # Modern header info table
    header_data = [
        [Paragraph(f"{tr['sold_by']}", modern_subheader), 
         Paragraph(f"{tr['invoice_date']}", modern_subheader),
         Paragraph(f"{tr['invoice_number']}", modern_subheader)],
        [Paragraph(order_info.get('seller_name', ''), modern_text),
         Paragraph(str(order_info.get('invoice_date', '')), modern_text),
         Paragraph(order_info.get('invoice_number', ''), modern_text)]
    ]
    
    header_table = Table(header_data, colWidths=[60*mm, 60*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), ModernColors.LIGHT_GREY),
        ("GRID", (0,0), (-1,-1), 0.5, ModernColors.BORDER_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [ModernColors.WHITE, ModernColors.LIGHT_GREY]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 16))
    
    # Customer name with modern styling
    story.append(Paragraph(order_info.get("customer_name", ""), modern_header))
    story.append(Spacer(1, 12))

    # ===== Modern Customer Information =====
    if order_info.get("commercial_address") or order_info.get("shipping_address"):
        customer_info = [
            [Paragraph(tr["commercial_address"], modern_subheader), 
             Paragraph(tr["shipping_address"], modern_subheader), 
             Paragraph(tr["sold_by"], modern_subheader)]
        ]
        
        # Add customer/seller information with proper formatting
        commercial_text = order_info.get("commercial_address", "")
        shipping_text = order_info.get("shipping_address", "")
        if order_info.get("customer_vat"):
            shipping_text += f"\nTVA {order_info['customer_vat']}"
        seller_text = f"{order_info['seller_name']}\n{order_info['seller_vat']}"
        
        customer_info.append([
            Paragraph(commercial_text, modern_text),
            Paragraph(shipping_text, modern_text), 
            Paragraph(seller_text, modern_text)
        ])
        
        customer_table = Table(customer_info, colWidths=[60*mm, 60*mm, 60*mm])
        customer_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), ModernColors.PRIMARY_BLUE),
            ("TEXTCOLOR", (0,0), (-1,0), ModernColors.WHITE),
            ("GRID", (0,0), (-1,-1), 0.5, ModernColors.BORDER_GREY),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 12),
            ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [ModernColors.WHITE, ModernColors.LIGHT_GREY]),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 16))

    # ===== Modern Order Information =====
    story.append(Paragraph("Informations de la commande", modern_header))
    story.append(Spacer(1, 8))
    
    order_info_table = [
        [Paragraph(tr["order_date"], modern_subheader), str(order_info["order_date"])],
        [Paragraph(tr["order_number"], modern_subheader), str(order_info["order_number"])],
        [Paragraph(tr["ordered_by"], modern_subheader), order_info["customer_name"]],
    ]
    
    order_table = Table(order_info_table, colWidths=[85*mm, 85*mm])
    order_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), ModernColors.LIGHT_GREY),
        ("GRID", (0,0), (-1,-1), 0.5, ModernColors.BORDER_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [ModernColors.WHITE, ModernColors.LIGHT_GREY]),
    ]))
    story.append(order_table)
    story.append(Spacer(1, 16))
    
    # ===== Modern Invoice Details =====
    story.append(Paragraph("Détails de la facture", modern_header))
    story.append(Spacer(1, 8))

    # ===== Modern Items Table =====
    headers = [tr["description"], tr["qty"], tr["unit_price_ht"], tr["vat_rate"], tr["unit_price_ttc"], tr["total_ttc"]]
    # Convert headers to modern paragraph objects
    headers = [Paragraph(header, modern_subheader) for header in headers]
    rows = [headers]
    total_ht = 0
    total_vat = 0
    total_ttc = 0
    vat_breakdown = {}  # To track VAT by rate

    for _, item in items.iterrows():
        qty = float(item["qty"])
        unit_price = float(item["unit_price"])
        unit_price_ttc = float(item.get("unit_price_ttc", unit_price * (1 + float(item["vat_rate"])/100)))
        vat_rate = float(item["vat_rate"])
        line_ht = qty * unit_price
        line_vat = line_ht * (vat_rate / 100)
        line_ttc = line_ht + line_vat

        # Build product description with ASIN if available
        product_desc = item["product_description"]
        if item.get("asin"):
            product_desc += f"\nASIN: {item['asin']}"
        
        rows.append([
            Paragraph(product_desc, modern_text),
            Paragraph(str(qty), modern_text),
            Paragraph(f"{unit_price:.2f} {currency_symbol}", modern_text),
            Paragraph(f"{vat_rate:.1f} %", modern_text),
            Paragraph(f"{unit_price_ttc:.2f} {currency_symbol}", modern_text),
            Paragraph(f"{line_ttc:.2f} {currency_symbol}", modern_text)
        ])

        total_ht += line_ht
        total_vat += line_vat
        total_ttc += line_ttc
        
        # Track VAT by rate for breakdown
        if vat_rate not in vat_breakdown:
            vat_breakdown[vat_rate] = {"ht": 0, "vat": 0}
        vat_breakdown[vat_rate]["ht"] += line_ht
        vat_breakdown[vat_rate]["vat"] += line_vat

    # Add shipping line with discounts if delivery charges > 0
    delivery_charges = float(order_info.get("delivery_charges", 0))
    delivery_discount_percent = float(order_info.get("delivery_discount_percent", 0))
    delivery_discount_amount = float(order_info.get("delivery_discount_amount", 0))
    
    if delivery_charges > 0:
        # Calculate discount
        discount_from_percent = delivery_charges * (delivery_discount_percent / 100)
        total_discount = max(discount_from_percent, delivery_discount_amount)
        final_delivery_charges = max(0, delivery_charges - total_discount)
        
        # Build delivery description with discount info
        delivery_desc = tr["delivery"]
        if order_info.get("promotion_description"):
            delivery_desc += f"\n{order_info['promotion_description']}"
        
        # Add discount line if there's a discount
        if total_discount > 0:
            discount_desc = tr.get("shipping_discount", "Promotion")
            if delivery_discount_percent > 0:
                discount_desc += f" (-{delivery_discount_percent:.1f}%)"
            elif delivery_discount_amount > 0:
                discount_desc += f" (-{delivery_discount_amount:.2f} {currency_symbol})"
            
            rows.append([
                Paragraph(delivery_desc, modern_text),
                Paragraph("1", modern_text),
                Paragraph(f"{delivery_charges:.2f} {currency_symbol}", modern_text),
                Paragraph("0.0 %", modern_text),
                Paragraph(f"{delivery_charges:.2f} {currency_symbol}", modern_text),
                Paragraph(f"{delivery_charges:.2f} {currency_symbol}", modern_text)
            ])
            
            discount_style = ParagraphStyle("Discount", parent=modern_text,
                                          textColor=ModernColors.SECONDARY_BLUE,
                                          fontName="Helvetica-Bold")
            rows.append([
                Paragraph(discount_desc, discount_style),
                Paragraph("1", modern_text),
                Paragraph(f"-{total_discount:.2f} {currency_symbol}", discount_style),
                Paragraph("0.0 %", modern_text),
                Paragraph(f"-{total_discount:.2f} {currency_symbol}", discount_style),
                Paragraph(f"-{total_discount:.2f} {currency_symbol}", discount_style)
            ])
        else:
            rows.append([
                Paragraph(delivery_desc, modern_text),
                Paragraph("1", modern_text),
                Paragraph(f"{delivery_charges:.2f} {currency_symbol}", modern_text),
                Paragraph("0.0 %", modern_text),
                Paragraph(f"{final_delivery_charges:.2f} {currency_symbol}", modern_text),
                Paragraph(f"{final_delivery_charges:.2f} {currency_symbol}", modern_text)
            ])
        total_ttc += final_delivery_charges

    items_table = Table(rows, colWidths=[70*mm, 15*mm, 25*mm, 20*mm, 25*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), ModernColors.PRIMARY_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), ModernColors.WHITE),
        ("GRID", (0,0), (-1,-1), 0.5, ModernColors.BORDER_GREY),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [ModernColors.WHITE, ModernColors.LIGHT_GREY]),
        ("LINEBELOW", (0,0), (-1,0), 2, ModernColors.PRIMARY_BLUE),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # ===== Modern Totals =====
    story.append(Spacer(1, 16))
    
    # Invoice Total with modern styling
    total_style = ParagraphStyle("InvoiceTotal", parent=modern_title,
                                fontName="Helvetica-Bold", fontSize=18,
                                textColor=ModernColors.PRIMARY_BLUE,
                                spaceAfter=16)
    story.append(Paragraph(f"{tr['totals_invoice_total']} {total_ttc:.2f} {currency_symbol}", total_style))
    
    # VAT breakdown table with modern styling
    vat_breakdown_table = [
        [Paragraph(tr["totals_vat_rate"], modern_subheader), 
         Paragraph(tr["totals_total_ht"], modern_subheader),
         Paragraph(tr["totals_vat"], modern_subheader), 
         Paragraph(tr["totals_total"], modern_subheader)]
    ]
    
    for vat_rate, amounts in sorted(vat_breakdown.items()):
        vat_breakdown_table.append([
            Paragraph(f"{vat_rate:.1f} %", modern_text),
            Paragraph(f"{amounts['ht']:.2f} {currency_symbol}", modern_text),
            Paragraph(f"{amounts['vat']:.2f} {currency_symbol}", modern_text),
            Paragraph(f"{amounts['ht'] + amounts['vat']:.2f} {currency_symbol}", modern_text)
        ])
    
    vat_table = Table(vat_breakdown_table, colWidths=[35*mm, 45*mm, 35*mm, 35*mm])
    vat_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), ModernColors.SECONDARY_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), ModernColors.WHITE),
        ("GRID", (0,0), (-1,-1), 0.5, ModernColors.BORDER_GREY),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [ModernColors.WHITE, ModernColors.LIGHT_GREY]),
    ]))
    story.append(vat_table)
    
    # ===== Modern Footer =====
    story.append(Spacer(1, 24))
    
    # Footer divider
    story.append(Paragraph("─" * 80, ParagraphStyle("Divider", parent=normal, 
                                                   textColor=ModernColors.BORDER_GREY,
                                                   fontSize=8)))
    story.append(Spacer(1, 12))
    
    # Shipping information
    story.append(Paragraph(tr["shipped_from"], modern_small))
    story.append(Spacer(1, 8))
    
    # Customer service information
    story.append(Paragraph(tr["customer_service"], modern_small))
    story.append(Spacer(1, 8))
    
    # Legal mentions
    story.append(Paragraph(tr["legal"], modern_small))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ============ STREAMLIT APP ============
st.title("Invoice Generator (Multi-Product, UI Input)")

# Sample data button for testing
if st.button("📝 Load Sample Data for Testing", type="secondary"):
    st.session_state["sample_data_loaded"] = True
    st.rerun()

if st.button("🗑️ Clear All Data", type="secondary"):
    # Clear all data including sample data flags
    st.session_state.clear()
    st.rerun()

# Show sample data status
if st.session_state.get("sample_data_loaded"):
    st.success("✅ Sample data loaded! You can now test the invoice generation or clear data to start fresh.")
else:
    st.write("Enter invoice details:")

# Language and Currency selection
st.subheader("Language & Currency Settings")
col1, col2 = st.columns(2)
with col1:
    language_options = {
        "FR": "🇫🇷 French (Français)",
        "EN": "🇬🇧 English", 
        "IT": "🇮🇹 Italian (Italiano)",
        "ES": "🇪🇸 Spanish (Español)",
        "DE": "🇩🇪 German (Deutsch)"
    }
    default_lang = 0 if not st.session_state.get("sample_data_loaded") else 1  # English for sample
    language = st.selectbox("Select Language", options=list(language_options.keys()), 
                           format_func=lambda x: language_options[x], index=default_lang)
with col2:
    default_currency = 0 if not st.session_state.get("sample_data_loaded") else 0  # EUR for sample
    currency = st.selectbox("Select Currency", ["EUR", "USD", "GBP", "CAD", "AUD"], index=default_currency)

currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£", "CAD": "C$", "AUD": "A$"}[currency]

order_info = {}
order_info["currency"] = currency
order_info["language"] = language
# Customer Information
st.subheader("Customer Information")
col1, col2 = st.columns(2)
with col1:
    default_customer = "" if not st.session_state.get("sample_data_loaded") else "TechCorp Solutions Ltd"
    order_info["customer_name"] = st.text_input("Customer Name", value=default_customer)
with col2:
    default_vat = "" if not st.session_state.get("sample_data_loaded") else "GB123456789"
    order_info["customer_vat"] = st.text_input("Customer VAT Number", value=default_vat)

# Order Information
st.subheader("Order Information")
col1, col2 = st.columns(2)
with col1:
    default_order = "" if not st.session_state.get("sample_data_loaded") else "ORD-2024-001234"
    order_info["order_number"] = st.text_input("Order Number", value=default_order)
    order_info["order_date"] = st.date_input("Order Date", datetime.date.today())
with col2:
    default_invoice = "" if not st.session_state.get("sample_data_loaded") else "INV-2024-005678"
    order_info["invoice_number"] = st.text_input("Invoice Number", value=default_invoice)
    order_info["invoice_date"] = st.date_input("Invoice Date", datetime.date.today())

# Seller Information
st.subheader("Seller Information")
col1, col2 = st.columns(2)
with col1:
    default_seller = "Nikilko2017 LTD" if not st.session_state.get("sample_data_loaded") else "Digital Innovations Inc"
    order_info["seller_name"] = st.text_input("Seller Name", value=default_seller)
with col2:
    # VAT number dropdown with country abbreviations (including Bulgaria)
    vat_options = {
        "CZ685067700": "CZ685067700 (CZ)",
        "FR21852738061": "FR21852738061 (FR)",
        "DE320122686": "DE320122686 (DE)",
        "IE4434643EH": "IE4434643EH (IE)",
        "IT00240439992": "IT00240439992 (IT)",
        "PL5263292882": "PL5263292882 (PL)",
        "ESN0681960A": "ESN0681960A (ES)",
        "SE502097371401": "SE502097371401 (SE)",
        "GB296824649": "GB296824649 (GB)",
        "BG204646515": "BG204646515 (BG)"
    }
    
    default_vat = "FR21852738061" if not st.session_state.get("sample_data_loaded") else "FR21852738061"
    
    # Make dropdown editable by allowing custom input
    selected_vat = st.selectbox("Seller VAT Number", 
                               options=list(vat_options.keys()),
                               format_func=lambda x: vat_options[x],
                               index=list(vat_options.keys()).index(default_vat),
                               help="Select from dropdown or type custom VAT number")
    
    # Add custom VAT input option
    custom_vat = st.text_input("Or enter custom VAT number:", 
                              placeholder="e.g., AT123456789",
                              help="Enter any custom VAT number if not in dropdown")
    
    # Use custom VAT if provided, otherwise use selected from dropdown
    if custom_vat.strip():
        order_info["seller_vat"] = custom_vat.strip()
        st.success(f"Using custom VAT: {custom_vat.strip()}")
    else:
        order_info["seller_vat"] = selected_vat

# Additional fields from translations
st.subheader("Additional Information")
default_payment = "" if not st.session_state.get("sample_data_loaded") else "PAY-REF-789456123"
order_info["payment_ref"] = st.text_input("Payment Reference", value=default_payment)

default_commercial = "" if not st.session_state.get("sample_data_loaded") else "Digital Innovations Inc\n123 Business Avenue\nSuite 456\nParis, 75001\nFrance"
order_info["commercial_address"] = st.text_area("Commercial Address (Company Name, Address, Country)", 
                                               height=80, 
                                               placeholder="Company Name\nAddress Line 1\nAddress Line 2\nCountry Code",
                                               value=default_commercial)

default_shipping = "" if not st.session_state.get("sample_data_loaded") else "TechCorp Solutions Ltd\n456 Tech Street\nLondon, SW1A 1AA\nUnited Kingdom"
order_info["shipping_address"] = st.text_area("Shipping Address (Customer Address)", 
                                             height=80, 
                                             placeholder="Customer Name\nAddress Line 1\nAddress Line 2\nCity, Postal Code\nCountry Code",
                                             value=default_shipping)

# Delivery/Shipping section with promotions
st.subheader("Delivery/Shipping & Promotions")
col1, col2, col3 = st.columns(3)
with col1:
    default_delivery = 0.0 if not st.session_state.get("sample_data_loaded") else 15.00
    order_info["delivery_charges"] = st.number_input(f"Delivery/Shipping Charges ({currency_symbol})", min_value=0.0, value=default_delivery)
with col2:
    default_discount_percent = 0.0 if not st.session_state.get("sample_data_loaded") else 20.0
    order_info["delivery_discount_percent"] = st.number_input("Delivery Discount (%)", min_value=0.0, max_value=100.0, value=default_discount_percent)
with col3:
    default_discount_amount = 0.0 if not st.session_state.get("sample_data_loaded") else 0.0
    order_info["delivery_discount_amount"] = st.number_input(f"Delivery Discount Amount ({currency_symbol})", min_value=0.0, value=default_discount_amount)

# Promotion description
default_promotion = "" if not st.session_state.get("sample_data_loaded") else "20% off shipping for orders over €100"
order_info["promotion_description"] = st.text_input("Promotion Description", 
                                                   placeholder="e.g., Free shipping over €50",
                                                   value=default_promotion)

# ===== Add multiple products =====
st.subheader("Products")

if "products" not in st.session_state:
    st.session_state["products"] = []

# Load sample products if sample data is requested
if st.session_state.get("sample_data_loaded") and not st.session_state.get("sample_products_loaded"):
    sample_products = [
        {
            "product_description": "Professional Wireless Mouse - Ergonomic Design",
            "asin": "B08XYZ1234",
            "qty": 2,
            "unit_price": 45.99,
            "unit_price_ttc": 55.19,
            "vat_rate": 20.0
        },
        {
            "product_description": "USB-C to HDMI Adapter - 4K Support",
            "asin": "B09ABC5678",
            "qty": 1,
            "unit_price": 25.50,
            "unit_price_ttc": 30.60,
            "vat_rate": 20.0
        },
        {
            "product_description": "Bluetooth Mechanical Keyboard - RGB Backlit",
            "asin": "B10DEF9012",
            "qty": 1,
            "unit_price": 89.99,
            "unit_price_ttc": 107.99,
            "vat_rate": 20.0
        }
    ]
    st.session_state["products"] = sample_products
    st.session_state["sample_products_loaded"] = True

with st.form("add_product_form"):
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        desc = st.text_input("Description", key="desc")
    with col2:
        asin = st.text_input("ASIN", key="asin", placeholder="B0DM8LG11X")
    with col3:
        qty = st.number_input("Qty", min_value=1, value=1, key="qty")
    with col4:
        unit_price = st.number_input(f"Unit Price HT ({currency_symbol})", min_value=0.0, value=10.0, key="price")
    with col5:
        unit_price_ttc = st.number_input(f"Unit Price TTC ({currency_symbol})", min_value=0.0, value=12.0, key="price_ttc")
    with col6:
        vat_rate = st.number_input("VAT %", min_value=0.0, value=20.0, key="vat")

    submitted = st.form_submit_button("Add product")
    if submitted and desc:
        st.session_state["products"].append({
            "product_description": desc,
            "asin": asin,
            "qty": qty,
            "unit_price": unit_price,
            "unit_price_ttc": unit_price_ttc,
            "vat_rate": vat_rate
        })

# Display current products with remove functionality
if st.session_state["products"]:
    st.write("Products added so far:")
    
    # Create a table with remove buttons
    for i, product in enumerate(st.session_state["products"]):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        with col1:
            st.write(f"**{product['product_description']}**")
            if product.get('asin'):
                st.write(f"ASIN: {product['asin']}")
        with col2:
            st.write(f"Qty: {product['qty']}")
        with col3:
            st.write(f"Price HT: {product['unit_price']:.2f} {currency_symbol}")
        with col4:
            st.write(f"Price TTC: {product['unit_price_ttc']:.2f} {currency_symbol}")
        with col5:
            st.write(f"VAT: {product['vat_rate']:.1f}%")
        with col6:
            total = product['qty'] * product['unit_price_ttc']
            st.write(f"Total: {total:.2f} {currency_symbol}")
        with col7:
            if st.button("Remove", key=f"remove_{i}", type="secondary"):
                st.session_state["products"].pop(i)
                st.rerun()
        
        st.divider()
    
    # Clear all products button
    if st.button("Clear All Products", type="secondary"):
        st.session_state["products"] = []
        st.rerun()
else:
    st.info("Add at least one product")

if st.button("Generate Invoice") and st.session_state["products"]:
    items = pd.DataFrame(st.session_state["products"])
    pdf_bytes = build_invoice(order_info, items, order_info["language"])

    # Add to session log
    add_to_session_log(order_info, st.session_state["products"], pdf_bytes)

    # Browser-friendly PDF display
    st.markdown("### 📄 Invoice Preview")
    
    # Download button for easy access
    st.download_button(
        label="📥 Download PDF Invoice",
        data=pdf_bytes,
        file_name=f"invoice_{order_info.get('invoice_number', 'unknown')}.pdf",
        mime="application/pdf",
        help="Click to download and view the PDF invoice"
    )
    
    # Show success message with instructions
    st.success(f"✅ Invoice {order_info.get('invoice_number', '')} generated successfully!")
    st.info("💡 **Tip:** Click the download button above to view the PDF. Some browsers may block embedded PDF previews for security reasons, but the download will work in all browsers.")
    
    # Optional: Show PDF data info
    pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
    st.caption(f"📊 PDF size: {pdf_size_mb:.2f} MB | Generated at {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    st.success(f"✅ Invoice {order_info.get('invoice_number', '')} generated and logged!")
    
    # Display session data and download option
    st.markdown("---")
    st.markdown("### 📊 Session Data Log")
    
    if "invoice_log" in st.session_state and st.session_state["invoice_log"]:
        # Show number of invoices in current session
        invoice_count = len(st.session_state["invoice_log"])
        st.info(f"📈 **Current Session:** {invoice_count} invoice(s) generated")
        
        # Create downloadable JSON
        log_json = json.dumps(st.session_state["invoice_log"], indent=2, ensure_ascii=False)
        log_bytes = log_json.encode('utf-8')
        
        # Download button for session data
        st.download_button(
            label="📥 Download Session Data (JSON)",
            data=log_bytes,
            file_name=f"invoice_session_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download all invoice data from current session as JSON file"
        )
        
        # Show summary table of invoices in session
        st.markdown("#### 📋 Invoice Summary")
        summary_data = []
        for i, log_entry in enumerate(st.session_state["invoice_log"], 1):
            summary_data.append({
                "Invoice #": log_entry["invoice_number"],
                "Customer": log_entry["customer_info"]["customer_name"],
                "Date": log_entry["timestamp"][:10],
                "Products": log_entry["totals"]["total_products"],
                "Currency": log_entry["payment_info"]["currency"]
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Clear session data button
            if st.button("🗑️ Clear Session Data", help="Clear all invoice data from current session"):
                st.session_state["invoice_log"] = []
                st.rerun()
    else:
        st.info("No invoices generated in this session yet.")
