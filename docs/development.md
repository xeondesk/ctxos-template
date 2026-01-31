# CtxOS Development Guide

This comprehensive guide covers everything you need to know to develop, test, and deploy CtxOS applications.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Architecture Overview](#architecture-overview)
4. [Core Development](#core-development)
5. [API Development](#api-development)
6. [Frontend Development](#frontend-development)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Performance Optimization](#performance-optimization)
10. [Security Best Practices](#security-best-practices)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/ctxos.git
cd ctxos

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
poetry install

# Set up frontend
cd src
npm install
cd ..

# Start development environment
docker-compose -f docker-compose.dev.yml up -d
python -m uvicorn api.main:app --reload
```

## Development Environment Setup

### Python Environment

```bash
# Using Poetry (recommended)
poetry install
poetry shell

# Or using pip
pip install -r requirements.txt
```

### Database Setup

```bash
# Start PostgreSQL with Docker
docker run --name ctxos-postgres \
  -e POSTGRES_DB=ctxos \
  -e POSTGRES_USER=ctxos_user \
  -e POSTGRES_PASSWORD=ctxos_password \
  -p 5432:5432 \
  postgres:15-alpine

# Run migrations
python -m alembic upgrade head

# Seed database
python scripts/seed_data.py
```

### Redis Setup

```bash
# Start Redis with Docker
docker run --name ctxos-redis -p 6379:6379 redis:7-alpine
```

### Environment Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://ctxos_user:ctxos_password@localhost:5432/ctxos

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# External Services
ELASTICSEARCH_URL=http://localhost:9200
BOSSNET_API_KEY=your-bossnet-key
SIEM_WEBHOOK_URL=your-siem-webhook
```

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │      API        │    │   Background    │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       │ PostgreSQL/Redis│
                       └─────────────────┘
```

### Core Modules

- **Core**: Entity, Signal, Context models
- **Collectors**: Data collection from various sources
- **Normalizers**: Data normalization and deduplication
- **Engines**: Risk, Exposure, and Drift assessment
- **Agents**: AI-powered analysis and automation
- **API**: RESTful API and GraphQL endpoints
- **CLI**: Command-line interface

## Core Development

### Entity Management

```python
from core.models import Entity, EntityType, EntitySeverity

# Create an entity
entity = Entity(
    name="example.com",
    entity_type=EntityType.DOMAIN,
    source="dns_collector",
    severity=EntitySeverity.MEDIUM,
    confidence=0.85
)

# Add properties
entity.set_property("registrar", "NameCheap")
entity.set_property("created_date", "2020-01-15")

# Save to database
from core.database import get_db
db = next(get_db())
db.add(entity)
db.commit()
```

### Signal Processing

```python
from core.models import Signal, SignalType, SignalSeverity

# Create a signal
signal = Signal(
    signal_type=SignalType.VULNERABILITY,
    severity=SignalSeverity.HIGH,
    confidence=SignalConfidence.HIGH,
    properties={
        "cve": "CVE-2023-1234",
        "cvss_score": 8.5,
        "affected_service": "nginx"
    }
)

# Link to entity
entity.add_signal(signal)
```

### Context Operations

```python
from core.models import Context

# Create context
context = Context(
    name="Security Assessment",
    description="Comprehensive security analysis",
    entities=[entity1, entity2],
    signals=[signal1, signal2]
)

# Query context
related_entities = context.get_entities_by_type(EntityType.DOMAIN)
high_risk_signals = context.get_signals_by_severity(SignalSeverity.HIGH)
```

## API Development

### FastAPI Application Structure

```
api/
├── main.py              # Application entry point
├── dependencies.py      # Dependency injection
├── middleware.py        # Custom middleware
├── routers/
│   ├── entities.py      # Entity endpoints
│   ├── signals.py       # Signal endpoints
│   ├── contexts.py      # Context endpoints
│   └── analytics.py     # Analytics endpoints
├── models/
│   ├── schemas.py       # Pydantic models
│   └── responses.py     # Response models
└── services/
    ├── entity_service.py
    ├── signal_service.py
    └── context_service.py
```

### Creating API Endpoints

```python
# api/routers/entities.py
from fastapi import APIRouter, Depends, HTTPException
from api.models.schemas import EntityCreate, EntityResponse
from api.services.entity_service import EntityService

router = APIRouter(prefix="/api/entities", tags=["entities"])

@router.post("/", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate,
    service: EntityService = Depends()
):
    """Create a new entity."""
    try:
        result = await service.create_entity(entity)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    service: EntityService = Depends()
):
    """Get entity by ID."""
    entity = await service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
```

### Dependency Injection

```python
# api/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db
from api.services.entity_service import EntityService

def get_entity_service(db: Session = Depends(get_db)) -> EntityService:
    return EntityService(db)

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Authentication logic
    return user
```

### Background Tasks

```python
from celery import Celery

app = Celery('ctxos')

@app.task
def process_collector_data(collector_name: str, target: str):
    """Process data from collector in background."""
    collector = get_collector(collector_name)
    data = collector.collect(target)
    
    # Process and store data
    for item in data:
        store_entity(item)
    
    return f"Processed {len(data)} items from {collector_name}"
```

## Frontend Development

### React Application Structure

```
src/
├── components/
│   ├── common/          # Reusable components
│   ├── entities/        # Entity-related components
│   ├── signals/         # Signal components
│   └── charts/          # Chart components
├── pages/
│   ├── Dashboard.tsx    # Main dashboard
│   ├── Entities.tsx     # Entity management
│   ├── Signals.tsx      # Signal analysis
│   └── Settings.tsx     # Application settings
├── hooks/
│   ├── useApi.ts        # API hook
│   ├── useWebSocket.ts  # WebSocket hook
│   └── useAuth.ts       # Authentication hook
├── services/
│   ├── api.ts           # API client
│   ├── websocket.ts     # WebSocket client
│   └── auth.ts          # Authentication service
├── stores/
│   ├── entityStore.ts   # Entity state management
│   └── signalStore.ts   # Signal state management
└── utils/
    ├── formatters.ts    # Data formatting
    └── validators.ts    # Form validation
```

### Component Development

```tsx
// src/components/entities/EntityCard.tsx
import React from 'react';
import { Card, Badge, Button } from '@/components/ui';
import { Entity } from '@/types';
import { useEntityStore } from '@/stores/entityStore';

interface EntityCardProps {
  entity: Entity;
  onEdit?: (entity: Entity) => void;
  onDelete?: (entityId: string) => void;
}

export const EntityCard: React.FC<EntityCardProps> = ({
  entity,
  onEdit,
  onDelete
}) => {
  const { updateEntity, deleteEntity } = useEntityStore();

  const handleEdit = () => {
    onEdit?.(entity);
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure?')) {
      await deleteEntity(entity.id);
      onDelete?.(entity.id);
    }
  };

  return (
    <Card className="entity-card">
      <div className="entity-header">
        <h3>{entity.name}</h3>
        <Badge variant={entity.severity}>
          {entity.severity}
        </Badge>
      </div>
      
      <div className="entity-details">
        <p>Type: {entity.type}</p>
        <p>Source: {entity.source}</p>
        <p>Confidence: {entity.confidence}%</p>
      </div>
      
      <div className="entity-actions">
        <Button onClick={handleEdit} variant="outline">
          Edit
        </Button>
        <Button onClick={handleDelete} variant="destructive">
          Delete
        </Button>
      </div>
    </Card>
  );
};
```

### State Management with Zustand

```typescript
// src/stores/entityStore.ts
import { create } from 'zustand';
import { Entity } from '@/types';
import { api } from '@/services/api';

interface EntityStore {
  entities: Entity[];
  loading: boolean;
  error: string | null;
  
  fetchEntities: () => Promise<void>;
  createEntity: (entity: Omit<Entity, 'id'>) => Promise<void>;
  updateEntity: (id: string, updates: Partial<Entity>) => Promise<void>;
  deleteEntity: (id: string) => Promise<void>;
}

export const useEntityStore = create<EntityStore>((set, get) => ({
  entities: [],
  loading: false,
  error: null,

  fetchEntities: async () => {
    set({ loading: true, error: null });
    try {
      const entities = await api.getEntities();
      set({ entities, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  createEntity: async (entityData) => {
    try {
      const entity = await api.createEntity(entityData);
      set(state => ({
        entities: [...state.entities, entity]
      }));
    } catch (error) {
      set({ error: error.message });
    }
  },

  updateEntity: async (id, updates) => {
    try {
      const updatedEntity = await api.updateEntity(id, updates);
      set(state => ({
        entities: state.entities.map(e =>
          e.id === id ? updatedEntity : e
        )
      }));
    } catch (error) {
      set({ error: error.message });
    }
  },

  deleteEntity: async (id) => {
    try {
      await api.deleteEntity(id);
      set(state => ({
        entities: state.entities.filter(e => e.id !== id)
      }));
    } catch (error) {
      set({ error: error.message });
    }
  }
}));
```

### API Client

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const entityApi = {
  getEntities: () => api.get('/api/entities').then(res => res.data),
  getEntity: (id: string) => api.get(`/api/entities/${id}`).then(res => res.data),
  createEntity: (entity: any) => api.post('/api/entities', entity).then(res => res.data),
  updateEntity: (id: string, updates: any) => 
    api.patch(`/api/entities/${id}`, updates).then(res => res.data),
  deleteEntity: (id: string) => api.delete(`/api/entities/${id}`).then(res => res.data),
};

export default api;
```

## Testing

### Unit Testing

```python
# tests/test_entities.py
import pytest
from core.models import Entity, EntityType, EntitySeverity

class TestEntity:
    def test_entity_creation(self):
        entity = Entity(
            name="test.com",
            entity_type=EntityType.DOMAIN,
            source="test",
            severity=EntitySeverity.LOW,
            confidence=0.8
        )
        
        assert entity.name == "test.com"
        assert entity.entity_type == EntityType.DOMAIN
        assert entity.confidence == 0.8
    
    def test_entity_properties(self):
        entity = Entity(name="test.com", entity_type=EntityType.DOMAIN)
        
        entity.set_property("registrar", "NameCheap")
        assert entity.get_property("registrar") == "NameCheap"
        
        entity.set_property("tags", ["security", "production"])
        assert entity.get_property("tags") == ["security", "production"]
```

### Integration Testing

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

class TestEntityAPI:
    def test_create_entity(self):
        response = client.post("/api/entities/", json={
            "name": "test-entity.com",
            "entity_type": "domain",
            "source": "test",
            "severity": "medium",
            "confidence": 0.85
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-entity.com"
        assert "id" in data
    
    def test_get_entities(self):
        # Create test entity first
        client.post("/api/entities/", json={
            "name": "test-list.com",
            "entity_type": "domain",
            "source": "test"
        })
        
        response = client.get("/api/entities/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        assert any(e["name"] == "test-list.com" for e in data)
```

### Frontend Testing

```tsx
// src/components/entities/__tests__/EntityCard.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { EntityCard } from '../EntityCard';
import { Entity } from '@/types';

const mockEntity: Entity = {
  id: '1',
  name: 'test.com',
  type: 'domain',
  severity: 'medium',
  source: 'test',
  confidence: 0.85
};

describe('EntityCard', () => {
  it('renders entity information correctly', () => {
    render(<EntityCard entity={mockEntity} />);
    
    expect(screen.getByText('test.com')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('Source: test')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<EntityCard entity={mockEntity} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByText('Edit'));
    expect(onEdit).toHaveBeenCalledWith(mockEntity);
  });

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = jest.fn();
    render(<EntityCard entity={mockEntity} onDelete={onDelete} />);
    
    // Mock window.confirm
    window.confirm = jest.fn(() => true);
    
    fireEvent.click(screen.getByText('Delete'));
    expect(onDelete).toHaveBeenCalledWith(mockEntity.id);
  });
});
```

### Running Tests

```bash
# Python tests
pytest tests/ -v
pytest tests/ --cov=core --cov-report=html

# Frontend tests
npm test
npm run test:coverage

# Integration tests
pytest tests/integration/ -v
```

## Deployment

### Docker Deployment

```bash
# Build and deploy
docker-compose up -d

# Scale services
docker-compose up -d --scale ctxos-worker=3

# View logs
docker-compose logs -f ctxos-api
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ctxos-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ctxos-api
  template:
    metadata:
      labels:
        app: ctxos-api
    spec:
      containers:
      - name: ctxos-api
        image: ctxos/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ctxos-secrets
              key: database-url
```

### Environment-Specific Configuration

```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Performance Optimization

### Database Optimization

```python
# Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_entities_type_severity 
ON ctxos_core.entities(entity_type, severity);

CREATE INDEX CONCURRENTLY idx_signals_entity_created 
ON ctxos_core.signals(entity_id, created_at);

# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### Caching Strategy

```python
# Redis caching
from functools import wraps
import redis
import json

redis_client = redis.Redis.from_url(settings.redis_url)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key, 
                expiration, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

@cache_result(expiration=600)
async def get_entity_risk_score(entity_id: str):
    # Expensive risk calculation
    return calculate_risk_score(entity_id)
```

### Async Operations

```python
# Use async for I/O operations
async def collect_multiple_targets(targets: List[str]):
    tasks = []
    for target in targets:
        task = asyncio.create_task(collect_single_target(target))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Security Best Practices

### Input Validation

```python
from pydantic import BaseModel, validator

class EntityCreate(BaseModel):
    name: str
    entity_type: str
    source: str
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 3 or len(v) > 255:
            raise ValueError('Name must be between 3 and 255 characters')
        return v
    
    @validator('entity_type')
    def validate_type(cls, v):
        allowed_types = ['domain', 'ip_address', 'email', 'url']
        if v not in allowed_types:
            raise ValueError(f'Invalid entity type: {v}')
        return v
```

### Authentication & Authorization

```python
# JWT Authentication
from jose import JWTError, jwt

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/entities")
@limiter.limit("100/minute")
async def get_entities(request: Request):
    return await entity_service.get_all_entities()
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   docker-compose logs postgres
   
   # Test connection
   python -c "
   from sqlalchemy import create_engine
   engine = create_engine('postgresql://user:pass@localhost/ctxos')
   print(engine.execute('SELECT 1').scalar())
   "
   ```

2. **Redis Connection Issues**
   ```bash
   # Test Redis connection
   redis-cli ping
   
   # Check Redis logs
   docker-compose logs redis
   ```

3. **API Performance Issues**
   ```bash
   # Profile API endpoints
   python -m cProfile -o api_profile.stats -m uvicorn api.main:app
   
   # Analyze with memory profiler
   python -m memory_profiler api/main.py
   ```

4. **Frontend Build Errors**
   ```bash
   # Clear cache
   rm -rf node_modules package-lock.json
   npm install
   
   # Check for TypeScript errors
   npm run type-check
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Database query logging
import sqlalchemy as sa
engine = create_engine(database_url, echo=True)
```

### Health Checks

```python
# api/health.py
from fastapi import APIRouter
from sqlalchemy import text
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    checks = {
        "database": "healthy",
        "redis": "healthy",
        "api": "healthy"
    }
    
    try:
        # Check database
        db.execute(text("SELECT 1"))
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis
        redis_client.ping()
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy",
        "checks": checks
    }
```

## Contributing

### Code Style

- Python: Follow PEP 8, use Black for formatting
- TypeScript: Use ESLint + Prettier
- Git: Use conventional commits

### Development Workflow

1. Create feature branch
2. Write tests
3. Implement functionality
4. Run tests and benchmarks
5. Submit pull request

### Code Review Checklist

- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact assessed

This development guide provides a comprehensive foundation for building and maintaining CtxOS applications. For specific questions or issues, refer to the project documentation or reach out to the development team.
