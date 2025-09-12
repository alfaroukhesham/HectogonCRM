# Cursor Rules for Tiny CRM Backend

This directory contains Cursor Rules that capture the patterns, conventions, and best practices used in the Tiny CRM backend codebase.

## Available Rules

### 🚀 [FastAPI Router Patterns](rules/fastapi-router-patterns.mdc)
- Router structure and organization
- Route definition patterns
- Dependency injection usage
- Authentication and error handling patterns

### 🔐 [Authentication & Security](rules/authentication-security.mdc)
- JWT token management (access/refresh tokens)
- OAuth implementation patterns
- Password security and session management
- Multi-tenant security considerations

### 🗄️ [Database & Models](rules/database-models.mdc)
- MongoDB with Motor async patterns
- Pydantic model conventions
- Database operation patterns
- Multi-tenant data scoping

### 🔧 [Service Layer](rules/service-layer.mdc)
- Service class structure
- Business logic patterns
- Caching integration
- Error handling and recovery

### ⚡ [Caching Patterns](rules/caching-patterns.mdc)
- Redis integration patterns
- Cache key naming conventions
- Cache invalidation strategies
- Organization-scoped caching

### 🚨 [Error Handling](rules/error-handling.mdc)
- HTTP exception patterns
- Database and cache error handling
- Validation error management
- Logging and recovery patterns

### 🏢 [Multi-tenant Architecture](rules/multi-tenant-architecture.mdc)
- Organization and membership models
- Permission checking patterns
- Data isolation strategies
- Role-based access control

### 🧪 [Testing Patterns](rules/testing-patterns.mdc)
- Integration testing patterns
- Service and API testing
- Mock usage patterns
- Test fixtures and database setup

### 🏗️ [Backend Architecture](rules/backend-architecture.mdc) *(Always Applied)*
- Overall project structure
- Coding standards and conventions
- Configuration management
- Performance and security best practices

### 📁 [Service Organization](rules/service-organization.mdc)
- Folder-based service architecture
- Migration from flat to structured services
- Service-specific file organization

### 🔄 [Service Migration Example](rules/service-migration-example.mdc)
- Practical cache service migration walkthrough
- File splitting strategies
- Import and dependency updates
- Testing migration approach

## How to Use These Rules

### Automatic Application
Rules with `alwaysApply: true` are automatically applied to all requests and will influence the AI's responses and code generation.

### Manual Application
Rules with `description` fields can be manually applied by mentioning their description in your request, or by asking Cursor to apply a specific rule.

### File-Specific Rules
Rules with `globs` patterns are automatically applied when working with files matching those patterns.

## Key Patterns Covered

### FastAPI Best Practices
- Async route handlers for all I/O operations
- Pydantic models for input validation and responses
- Dependency injection for database, cache, and services
- Proper HTTP status codes and error responses

### Authentication & Security
- JWT access tokens (30-minute expiry)
- Redis-stored refresh tokens (30-day expiry)
- OAuth integration with multiple providers
- Session invalidation on security events

### Multi-tenant Architecture
- Organization-scoped data access
- Role-based permissions (Admin, Editor, Viewer)
- Membership validation for all operations
- Cache key scoping by organization

### Database Patterns
- MongoDB with async Motor operations
- Pydantic models with ObjectId handling
- Aggregation pipelines for complex queries
- Proper error handling and connection management

### Caching Strategy
- Redis for high-performance caching
- Organization-scoped cache keys to prevent cross-tenant access
- Graceful fallback when Redis is unavailable
- Strategic cache invalidation patterns

### Error Handling
- Early return pattern for error conditions
- HTTP exceptions with appropriate status codes
- Comprehensive logging with context
- Recovery patterns and graceful degradation

## Technology Stack

- **FastAPI**: Async web framework
- **MongoDB + Motor**: Async database operations
- **Redis**: Caching and session storage
- **Pydantic v2**: Data validation and serialization
- **JWT**: Authentication tokens
- **OAuth**: Social login integration

## Service Organization Migration

### Current Structure → Target Structure

**Before (Flat):**
```
services/
├── cache_service.py
├── invite_service.py
├── membership_service.py
└── organization_service.py
```

**After (Folder-based):**
```
services/
├── cache_service/
│   ├── __init__.py
│   ├── service.py
│   ├── models.py
│   ├── types.py
│   ├── utils.py
│   ├── constants.py
│   └── test_service.py
├── invite_service/
│   ├── __init__.py
│   ├── service.py
│   ├── models.py
│   ├── types.py
│   ├── utils.py
│   └── test_service.py
└── ...
```

### Migration Benefits
- **Better maintainability**: Related code grouped together
- **Improved debugging**: Clear separation of concerns
- **Enhanced testability**: Tests co-located with code
- **Scalability**: Easy to add features per service
- **Team collaboration**: Reduced merge conflicts

### Implementation Steps
1. Create service folders with kebab-case naming
2. Split monolithic service files into focused modules
3. Move tests into respective service folders
4. Update all import statements throughout codebase
5. Update dependency injection functions
6. Test thoroughly after migration

See [Service Organization](rules/service-organization.mdc) for detailed migration guidance.

## Development Workflow

1. **Route Development**: Use FastAPI router patterns
2. **Business Logic**: Implement in service layer with proper error handling
3. **Data Access**: Follow database patterns with async operations
4. **Caching**: Implement strategic caching with organization scoping
5. **Security**: Apply authentication and authorization patterns
6. **Testing**: Use comprehensive testing patterns for validation

## Code Quality Standards

- Full type hints on all functions
- Descriptive variable names with auxiliary verbs
- Async/await for all I/O operations
- Comprehensive error handling and logging
- Pydantic models for data validation
- Dependency injection for testability
- Clean separation of concerns

These rules ensure consistent, maintainable, and secure code across the entire backend codebase.
