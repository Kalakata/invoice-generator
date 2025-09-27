# Modern Invoice Generator

A professional, multi-language invoice generator built with Streamlit and ReportLab.

## Features

- 🌍 **Multi-language Support**: French, English, Italian, Spanish, German
- 💰 **Multi-currency Support**: EUR, USD, GBP, CAD, AUD
- 🏢 **Flexible VAT Numbers**: 10 pre-configured VAT numbers + custom input
- 📦 **Multi-product Invoices**: Add multiple products with ASIN support
- 🎨 **Modern Design**: Professional, clean layout with modern colors
- 💳 **Payment Tracking**: Optional payment reference system
- 🚚 **Delivery Promotions**: Support for discounts and promotions
- 📊 **Data Logging**: Comprehensive logging of all invoice data
- 📱 **Responsive UI**: Clean, user-friendly interface

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/invoice-generator.git
   cd invoice-generator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run invoice_ui.py
   ```

## Usage

1. **Select Language & Currency**: Choose your preferred language and currency
2. **Fill Customer Information**: Enter customer details and VAT numbers
3. **Add Order Details**: Invoice number, order number, dates
4. **Configure Seller**: Select from pre-configured VAT numbers or enter custom
5. **Add Products**: Include multiple products with quantities and prices
6. **Set Delivery**: Configure shipping charges and promotions
7. **Generate Invoice**: Create and download professional PDF

## Features in Detail

### Multi-Language Support
- French (Français)
- English
- Italian (Italiano)
- Spanish (Español)
- German (Deutsch)

### VAT Number Support
- Czech Republic (CZ685067700)
- France (FR21852738061)
- Germany (DE320122686)
- Ireland (IE4434643EH)
- Italy (IT00240439992)
- Poland (PL5263292882)
- Spain (ESN0681960A)
- Sweden (SE502097371401)
- United Kingdom (GB296824649)
- Bulgaria (BG204646515)
- **Custom VAT**: Enter any VAT number not in the list

### Data Logging
All invoice data is automatically logged to `invoice_log.json` including:
- Customer and seller information
- Product details
- Payment information
- Delivery charges and promotions
- Timestamps and metadata

## File Structure

```
invoice-generator/
├── invoice_ui.py          # Main Streamlit application
├── translations.json      # Language translations
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── invoice_log.json      # Generated log file (created automatically)
```

## Deployment

### Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Set main file to `invoice_ui.py`
6. Deploy!

### Local Development
```bash
streamlit run invoice_ui.py
```

## Dependencies

- `streamlit>=1.28.0` - Web application framework
- `pandas>=1.5.0` - Data manipulation
- `reportlab>=4.0.0` - PDF generation
- `openpyxl>=3.1.0` - Excel file support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please create an issue on GitHub.
