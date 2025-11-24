## SmartPC Builder Backend (FastAPI)

Backend API dla aplikacji SmartPC Builder & Recommender.

### Struktura projektu

```
smartpc-builder-backend/
  app/
    api/
      routes/          # Endpointy API
        health.py
        products.py
        presets.py
        validation.py
        inquiries.py
        configurations.py
        auth.py
        import_export.py
        statistics.py
    core/
      config.py        # Konfiguracja
      database.py      # Połączenie z bazą
      init_db.py       # Inicjalizacja bazy
    models/            # Modele SQLAlchemy
      product.py
      preset.py
      inquiry.py
      user.py
      configuration.py
    schemas/           # Schematy Pydantic
      product.py
      preset.py
      inquiry.py
      user.py
      configuration.py
      validation.py
    services/          # Logika biznesowa
      validation.py
      recommendation.py
      email.py
      auth.py
      performance.py
    middleware/
      rate_limit.py    # Rate limiting
    main.py            # Główna aplikacja
  requirements.txt
  render.yaml
  README.md
```

### Wymagania

- Python 3.11+
- PostgreSQL (produkcja) lub SQLite (development)

### Instalacja

```bash
python -m venv .venv
.\.venv\Scripts\activate            # Windows PowerShell
pip install -r requirements.txt
```

### Konfiguracja

Utwórz plik `.env` z następującymi zmiennymi:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/smartpc
# lub dla SQLite (development):
# DATABASE_URL=sqlite+aiosqlite:///./smartpc.db

# CORS
CORS_ORIGIN=http://localhost:3000

# Security
JWT_SECRET=your-secret-key-here

# Email/SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@smartpc.pro-kom.eu
INQUIRY_EMAIL=k.potaczek@pro-kom.eu

# reCAPTCHA (opcjonalne)
RECAPTCHA_SECRET_KEY=your-recaptcha-secret
```

### Inicjalizacja bazy danych

```bash
python -m app.core.init_db
```

### Uruchomienie serwera

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Endpointy API

- `GET /api/v1/health` - Health check
- `GET /api/v1/products` - Lista produktów
- `GET /api/v1/presets/recommendations` - Rekomendacje
- `POST /api/v1/validate` - Walidacja konfiguracji
- `POST /api/v1/inquiries` - Wysyłka zapytania
- `GET /api/v1/configurations` - Lista konfiguracji
- `POST /api/v1/auth/register` - Rejestracja
- `POST /api/v1/auth/login` - Logowanie
- `POST /api/v1/import-export/products/import` - Import CSV
- `GET /api/v1/import-export/products/export` - Eksport CSV
- `GET /api/v1/statistics/inquiries` - Statystyki zapytań

Pełna dokumentacja API dostępna pod: `http://localhost:8000/api/docs`

### Funkcjonalności

✅ Landing page (device/segment/budget selection)
✅ PC Configurator (wszystkie komponenty)
✅ Walidacja kompatybilności (socket, RAM, PSU, form factors)
✅ Silnik rekomendacji (rule-based)
✅ Formularze zapytań z wysyłką e-mail
✅ Lista laptopów z filtrami
✅ Autentykacja użytkowników
✅ Zapisywanie konfiguracji
✅ Analiza wydajności i FPS
✅ Import/eksport CSV
✅ Statystyki
✅ Rate limiting
✅ Publiczne linki do konfiguracji

### Deploy na Render

1. W repozytorium musi znajdować się `render.yaml`
2. W Render: New + → Blueprint → wskaż repo
3. Skonfiguruj zmienne środowiskowe
4. Deploy uruchomi komendy automatycznie
