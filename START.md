# 🚀 Jak uruchomić backend

## Krok 1: Przejdź do katalogu backendu
```bash
cd smartpc-builder-backend
```

## Krok 2: Utwórz wirtualne środowisko (opcjonalne, ale zalecane)
```bash
python -m venv .venv
```

## Krok 3: Aktywuj wirtualne środowisko

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

## Krok 4: Zainstaluj zależności
```bash
pip install -r requirements.txt
```

## Krok 5: Inicjalizuj bazę danych
```bash
python -m app.core.init_db
```

## Krok 6: Uruchom serwer
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Gotowe!

Backend będzie dostępny pod adresem:
- **API:** http://localhost:8000
- **Dokumentacja Swagger:** http://localhost:8000/api/docs
- **Health check:** http://localhost:8000/api/v1/health

---

## 🔧 Opcjonalna konfiguracja (.env)

Możesz utworzyć plik `.env` w katalogu `smartpc-builder-backend` z następującymi zmiennymi:

```env
# Database (opcjonalne - domyślnie używa SQLite)
DATABASE_URL=sqlite+aiosqlite:///./smartpc.db

# CORS
CORS_ORIGIN=http://localhost:3000

# Security
JWT_SECRET=your-secret-key-here

# Email (opcjonalne)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@smartpc.pro-kom.eu
INQUIRY_EMAIL=k.potaczek@pro-kom.eu
```

## 🐛 Rozwiązywanie problemów

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
**Rozwiązanie:** Upewnij się, że aktywowałeś wirtualne środowisko i zainstalowałeś zależności.

**Problem:** `asyncpg` nie instaluje się
**Rozwiązanie:** To normalne - `asyncpg` jest opcjonalne (tylko dla PostgreSQL). SQLite działa bez niego.

**Problem:** Błąd bazy danych
**Rozwiązanie:** Uruchom `python -m app.core.init_db` aby utworzyć tabele.

