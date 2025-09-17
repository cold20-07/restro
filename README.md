# QR Code Ordering System

A multi-tenant QR-code ordering system for restaurants built with FastAPI and Reflex.

## Features

- Multi-tenant restaurant management with data isolation
- QR code-based table ordering for customers
- Real-time order management dashboard
- Payment processing integration
- Analytics and reporting

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: Reflex (Python-based web framework)
- **Database**: Supabase (PostgreSQL with Row-Level Security)
- **Authentication**: Supabase Auth with JWT
- **Real-time**: WebSockets + Supabase Realtime

## Project Structure

```
├── app/                    # FastAPI application
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   ├── database/          # Database connections
│   ├── models/            # Pydantic models
│   └── services/          # Business logic
├── dashboard/             # Reflex dashboard app
├── tests/                 # Test suite
├── main.py               # FastAPI entry point
├── rxconfig.py           # Reflex configuration
└── requirements.txt      # Python dependencies
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Run the FastAPI backend:
```bash
python main.py
```

4. Run the Reflex dashboard (in a separate terminal):
```bash
reflex run
```

## Environment Variables

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `SECRET_KEY`: JWT secret key for authentication

## Development

This project follows the spec-driven development methodology. See the `.kiro/specs/qr-code-ordering-system/` directory for detailed requirements, design, and implementation tasks.

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Dashboard

The restaurant dashboard will be available at `http://localhost:3000` when running the Reflex app.