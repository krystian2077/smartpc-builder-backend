import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """Send email via SMTP"""
    if not settings.smtp_host or not settings.smtp_user:
        # In development, just log
        print(f"[EMAIL] Would send to {to_email}: {subject}")
        print(f"[EMAIL] Body: {body}")
        return True
    
    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain"))
        if html_body:
            message.attach(MIMEText(html_body, "html"))
        
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_port == 465,
            start_tls=settings.smtp_port != 465,
        )
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")
        return False


async def send_inquiry_notification(
    reference_number: str,
    inquiry_data: dict,
) -> bool:
    """Send inquiry notification email to PRO-KOM"""
    subject = f"Nowe zapytanie ofertowe - {reference_number}"
    
    # Extract configuration data
    config_data = inquiry_data.get('configuration_data', {})
    components = config_data.get('components', {})
    device = config_data.get('device', 'N/A')
    segment = config_data.get('segment', 'N/A')
    budget = config_data.get('budget', 'N/A')
    total_price = config_data.get('totalPrice', 'N/A')
    assembly_service = config_data.get('assemblyService', False)
    
    # Build components list for plain text
    components_text = ""
    if components:
        for key, value in components.items():
            if value:
                component_label = {
                    'cpu': 'Procesor (CPU)',
                    'motherboard': 'Płyta główna',
                    'gpu': 'Karta graficzna (GPU)',
                    'ram': 'Pamięć RAM',
                    'storage': 'Dysk',
                    'psu': 'Zasilacz (PSU)',
                    'case': 'Obudowa',
                    'cooler': 'Chłodzenie'
                }.get(key, key.upper())
                
                # Check if value is a dict with name and price
                if isinstance(value, dict):
                    name = value.get('name', 'N/A')
                    price = value.get('price', 0)
                    components_text += f"- {component_label}: {name} ({price} zł)\n"
                else:
                    # Fallback for old format (just ID)
                    components_text += f"- {component_label}: {value}\n"
    else:
        components_text = "Brak wybranych komponentów"
    
    body = f"""
Nowe zapytanie ofertowe otrzymane w systemie SmartPC Builder.

Numer referencyjny: {reference_number}
Typ zapytania: {inquiry_data.get('inquiry_type')}
Źródło: {inquiry_data.get('source')}

Konfiguracja:
- Urządzenie: {device}
- Segment: {segment}
- Budżet: {budget} zł
- Całkowita cena: {total_price} zł
- Usługa montażu: {'TAK (+399 zł)' if assembly_service else 'NIE'}

Wybrane komponenty:
{components_text}

Dane kontaktowe:
- Imię i nazwisko: {inquiry_data.get('first_name')} {inquiry_data.get('last_name')}
- Email: {inquiry_data.get('email')}
- Telefon: {inquiry_data.get('phone', 'Nie podano')}

Wiadomość:
{inquiry_data.get('message', 'Brak wiadomości')}

Zgody:
- Kontakt: {'Tak' if inquiry_data.get('consent_contact') else 'Nie'}
- RODO: {'Tak' if inquiry_data.get('consent_rodo') else 'Nie'}

---
SmartPC Builder System
"""
    
    # Build components HTML
    components_html = ""
    if components:
        for key, value in components.items():
            if value:
                component_name = {
                    'cpu': 'Procesor (CPU)',
                    'motherboard': 'Płyta główna',
                    'gpu': 'Karta graficzna (GPU)',
                    'ram': 'Pamięć RAM',
                    'storage': 'Dysk',
                    'psu': 'Zasilacz (PSU)',
                    'case': 'Obudowa',
                    'cooler': 'Chłodzenie'
                }.get(key, key.upper())
                
                # Check if value is a dict with name and price
                if isinstance(value, dict):
                    product_name = value.get('name', 'N/A')
                    product_price = value.get('price', 0)
                    components_html += f"""
                    <div class="component-item">
                        <div>
                            <div class="component-label">{component_name}</div>
                            <div style="color: #6b7280; font-size: 13px; margin-top: 2px;">{product_name}</div>
                        </div>
                        <div class="component-price" style="color: #10b981; font-weight: bold; font-size: 16px;">{product_price} zł</div>
                    </div>
                    """
                else:
                    # Fallback for old format (just ID)
                    components_html += f"""
                    <div class="component-item">
                        <span class="component-label">{component_name}:</span>
                        <span class="component-id">{value}</span>
                    </div>
                    """
    else:
        components_html = '<p style="color: #6b7280; font-style: italic;">Brak wybranych komponentów</p>'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f9; }}
            .container {{ max-width: 700px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 600; }}
            .header p {{ margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; margin-bottom: 15px; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; padding: 8px; background-color: #f9fafb; border-radius: 6px; }}
            .info-label {{ font-weight: 600; color: #374151; min-width: 140px; }}
            .info-value {{ color: #111827; }}
            .config-box {{ background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .config-item {{ margin-bottom: 8px; }}
            .config-label {{ font-weight: 600; color: #065f46; margin-right: 8px; }}
            .config-value {{ color: #047857; }}
            .component-item {{ background-color: #ffffff; border: 1px solid #e5e7eb; padding: 12px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }}
            .component-label {{ font-weight: 600; color: #374151; }}
            .component-id {{ color: #6b7280; font-family: 'Courier New', monospace; font-size: 12px; }}
            .message-box {{ background-color: #f3f4f6; border-left: 4px solid #10b981; padding: 15px; border-radius: 4px; font-style: italic; color: #4b5563; }}
            .footer {{ background-color: #1f2937; color: #9ca3af; text-align: center; padding: 20px; font-size: 12px; }}
            .tag {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }}
            .tag-emerald {{ background-color: #d1fae5; color: #065f46; }}
            .tag-blue {{ background-color: #dbeafe; color: #1e40af; }}
            .highlight {{ color: #10b981; font-weight: bold; }}
            .price-badge {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 12px 20px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖥️ Nowe Zapytanie Ofertowe</h1>
                <p>SmartPC Builder - Konfigurator PC</p>
            </div>
            <div class="content">
                <div class="section">
                    <div class="section-title">📋 Szczegóły Zapytania</div>
                    <p style="margin: 5px 0;"><strong>Numer referencyjny:</strong> <span class="highlight">{reference_number}</span></p>
                    <p style="margin: 5px 0;"><strong>Typ:</strong> <span class="tag tag-emerald">{inquiry_data.get('inquiry_type')}</span></p>
                    <p style="margin: 5px 0;"><strong>Źródło:</strong> <span class="tag tag-blue">{inquiry_data.get('source')}</span></p>
                </div>

                <div class="section">
                    <div class="section-title">⚙️ Konfiguracja Komputera</div>
                    <div class="config-box">
                        <div class="config-item">
                            <span class="config-label">Urządzenie:</span>
                            <span class="config-value">{device}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Segment:</span>
                            <span class="config-value">{segment}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Budżet:</span>
                            <span class="config-value">{budget} zł</span>
                        </div>
                    </div>
                    <div class="price-badge">
                        💰 Całkowita cena: {total_price} zł
                    </div>
                    {f'<div style="background-color: #d1fae5; border: 2px solid #10b981; padding: 12px; border-radius: 8px; text-align: center; margin-top: 15px;"><span style="color: #065f46; font-weight: bold;">✅ Usługa montażu: TAK (+399 zł)</span></div>' if assembly_service else '<div style="background-color: #f3f4f6; border: 2px solid #9ca3af; padding: 12px; border-radius: 8px; text-align: center; margin-top: 15px;"><span style="color: #6b7280; font-weight: bold;">Usługa montażu: NIE</span></div>'}
                </div>

                <div class="section">
                    <div class="section-title">🔧 Wybrane Komponenty</div>
                    {components_html}
                </div>

                <div class="section">
                    <div class="section-title">👤 Dane Kontaktowe</div>
                    <div class="info-row"><span class="info-label">Imię i nazwisko:</span> <span class="info-value">{inquiry_data.get('first_name')} {inquiry_data.get('last_name')}</span></div>
                    <div class="info-row"><span class="info-label">Email:</span> <span class="info-value"><a href="mailto:{inquiry_data.get('email')}" style="color: #10b981; text-decoration: none;">{inquiry_data.get('email')}</a></span></div>
                    <div class="info-row"><span class="info-label">Telefon:</span> <span class="info-value">{inquiry_data.get('phone', 'Nie podano')}</span></div>
                </div>

                <div class="section">
                    <div class="section-title">💬 Wiadomość od Klienta</div>
                    <div class="message-box">
                        "{inquiry_data.get('message', 'Brak wiadomości')}"
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">✅ Zgody Formalne</div>
                    <div class="info-row"><span class="info-label">Kontakt:</span> <span class="info-value">{'✅ Tak' if inquiry_data.get('consent_contact') else '❌ Nie'}</span></div>
                    <div class="info-row"><span class="info-label">RODO:</span> <span class="info-value">{'✅ Tak' if inquiry_data.get('consent_rodo') else '❌ Nie'}</span></div>
                </div>
            </div>
            <div class="footer">
                Wiadomość wygenerowana automatycznie przez system SmartPC Builder.<br>
                &copy; 2024 PRO-KOM. Wszystkie prawa zastrzeżone.
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to_email=settings.inquiry_email,
        subject=subject,
        body=body,
        html_body=html_body,
    )

