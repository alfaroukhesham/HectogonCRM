# Tiny CRM Backend API

A well-structured FastAPI backend for a Customer Relationship Management (CRM) system.

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI app creation and configuration
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration and settings
│   │   └── database.py    # Database connection management
│   ├── models/            # Pydantic models
│   │   ├── __init__.py
│   │   ├── contact.py     # Contact models
│   │   ├── deal.py        # Deal models and enums
│   │   └── activity.py    # Activity models and enums
│   └── routers/           # API route handlers
│       ├── __init__.py
│       ├── contacts.py    # Contact endpoints
│       ├── deals.py       # Deal endpoints
│       ├── activities.py  # Activity endpoints
│       └── dashboard.py   # Dashboard/analytics endpoints
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── server.py             # Application entry point
└── README.md             # This file
```

## Features

- **Modular Design**: Clean separation of concerns with dedicated modules
- **Type Safety**: Full Pydantic model validation
- **Database**: MongoDB with async motor driver
- **Configuration**: Environment-based configuration management
- **CORS**: Properly configured for frontend integration
- **Logging**: Comprehensive logging setup
- **Documentation**: Auto-generated API docs with FastAPI

## Quick Start

### Prerequistes

- install python 3.12

### 1. Install Dependencies
```bash
# Create new virtual environment with Python 3.12
python -m venv venv

# Activate the new environment
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the backend directory:
```env
MONGO_URL=mongodb://localhost:27017/
DB_NAME=tiny_crm
LOG_LEVEL=INFO
```

### 3. Start the Server
```bash
# Option 1: Direct uvicorn
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python
python server.py

# Option 3: Module approach
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API
- **API Base URL**: http://localhost:8000/api
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Contacts
- `POST /api/contacts` - Create new contact
- `GET /api/contacts` - List contacts (with optional search)
- `GET /api/contacts/{id}` - Get specific contact
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact

### Deals
- `POST /api/deals` - Create new deal
- `GET /api/deals` - List all deals
- `GET /api/deals/{id}` - Get specific deal
- `PUT /api/deals/{id}` - Update deal
- `DELETE /api/deals/{id}` - Delete deal

### Activities
- `POST /api/activities` - Create new activity
- `GET /api/activities` - List activities (filterable by contact/deal)
- `GET /api/activities/{id}` - Get specific activity
- `PUT /api/activities/{id}` - Update activity
- `DELETE /api/activities/{id}` - Delete activity

### Dashboard
- `GET /api/dashboard/stats` - Get CRM statistics

## Development

### Adding New Features

1. **Models**: Add new Pydantic models in `app/models/`
2. **Routes**: Create new router in `app/routers/`
3. **Registration**: Include router in `app/main.py`

### Database Operations
All database operations use MongoDB with the Motor async driver. The database connection is managed in `app/core/database.py` and injected as a dependency.

### Configuration
Settings are managed in `app/core/config.py` using environment variables. Add new settings to the `Settings` class.

### Error Handling
HTTP exceptions are handled using FastAPI's `HTTPException`. Common patterns:
- 404 for resource not found
- 400 for validation errors
- 500 for server errors

## Benefits of This Structure

1. **Maintainability**: Clear separation of concerns
2. **Scalability**: Easy to add new features and modules  
3. **Testing**: Each module can be tested independently
4. **Reusability**: Models and utilities can be shared
5. **Documentation**: Self-documenting code structure
6. **Team Development**: Multiple developers can work on different modules

## Migration from Old Structure

The original monolithic `server.py` file has been refactored into:
- **Models** → `app/models/`
- **Routes** → `app/routers/`
- **Configuration** → `app/core/config.py`
- **Database** → `app/core/database.py`
- **Main App** → `app/main.py`

All functionality remains the same, but the code is now more organized and maintainable.

more functionality to come...