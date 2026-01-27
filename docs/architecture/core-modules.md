# Core Modules Architecture

## Overview

The Core Modules layer (`core/`) provides foundational data models, schema management, and utility functions that power the entire CtxOS framework. This layer is responsible for representing security entities, signals, and context in a structured, type-safe manner.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Core Modules (core/)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Data Models (core/models/)                 │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • Entity      - Security entities (domains, IPs)    │  │
│  │  • Signal      - Security signals/evidence            │  │
│  │  • Context     - Collections of entities & signals   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                   │
│                           │ uses                             │
│                           │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Schema Management (core/schema/)                │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • SchemaRegistry    - Version management             │  │
│  │  • SchemaVersion     - Version metadata               │  │
│  │  • Validation        - JSON schema validation         │  │
│  │  • Migrations        - Schema upgrade paths           │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                   │
│                           │ uses                             │
│                           │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       Utilities (core/utils/)                        │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Dict Utils:                                         │  │
│  │  • Hashing, merging, flattening                      │  │
│  │  • Sanitization, filtering, diffing                  │  │
│  │                                                      │  │
│  │  String Utils:                                       │  │
│  │  • Validation (domain, IP, email, URL, etc)         │  │
│  │  • Extraction (domains, emails, IPs from text)      │  │
│  │  • Transformation (slugify, camelCase conversion)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Models

### Entity Model

**Purpose**: Represents security entities discovered during reconnaissance and analysis.

**Supported Entity Types** (13 types):
- `domain` - Domain names
- `ip_address` - IPv4/IPv6 addresses  
- `host` - Hostnames
- `service` - Network services
- `person` - People associated with organization
- `email` - Email addresses
- `url` - URLs/URIs
- `certificate` - SSL/TLS certificates
- `account` - User/service accounts
- `credential` - Credentials (passwords, tokens)
- `file` - Files and archives
- `process` - Running processes
- `registry` - Registry entries
- `other` - Other entity types

**Key Features**:
- **UUID-based identification** - Globally unique entity IDs
- **Severity scoring** - Risk level assessment (critical/high/medium/low/info)
- **Confidence scoring** - 0-1 confidence scale for findings
- **Temporal tracking** - Discovery and last-seen timestamps
- **Property storage** - Flexible key-value metadata
- **Relationship tracking** - Links to related entities
- **Tag management** - Categorization and classification
- **Status tracking** - Entity lifecycle state (active/inactive/unknown/archived)

**Example Usage**:
```python
from core.models import Entity, EntityType

entity = Entity(
    name="example.com",
    entity_type=EntityType.DOMAIN,
    source="dns_collector",
    severity=EntitySeverity.MEDIUM,
    confidence=0.85
)

# Add properties
entity.set_property("registrar", "NameCheap")
entity.set_property("expiry", "2024-12-31")

# Add tags
entity.add_tag("monitored")
entity.add_tag("external")

# Serialize
entity_dict = entity.to_dict()
```

### Signal Model

**Purpose**: Represents security signals, evidence, and findings from collectors.

**Supported Signal Types** (15 types):
- `domain_registration` - Domain registration events
- `dns_record` - DNS record discoveries
- `ip_whois` - IP geolocation/ownership data
- `certificate` - Certificate findings
- `http_header` - HTTP header analysis
- `open_port` - Open ports detected
- `vulnerability` - Vulnerability findings
- `malware` - Malware indicators
- `suspicious_activity` - Suspicious behavior
- `configuration` - Configuration issues
- `credential_exposure` - Exposed credentials
- `data_breach` - Data breach mentions
- `other` - Other signal types

**Key Features**:
- **Source tracking** - Which collector provided the signal
- **Entity linking** - Association with specific entities
- **Severity assessment** - Signal risk level
- **Confidence levels** - verified/high/medium/low/unverified
- **Expiry tracking** - Time-bounded validity
- **Metadata storage** - Rich structured data
- **Raw data preservation** - Original collector output
- **Tag classification** - Signal categorization

**Example Usage**:
```python
from core.models import Signal, SignalType, SignalSeverity

signal = Signal(
    source="dns_collector",
    signal_type=SignalType.DNS_RECORD,
    data={
        "record_type": "A",
        "value": "93.184.216.34",
        "ttl": 3600
    },
    severity=SignalSeverity.LOW,
    entity_id=entity.id
)

# Add metadata
signal.set_metadata("resolver", "8.8.8.8")
signal.set_metadata("query_time", 45)

# Check expiry
if not signal.is_expired():
    print("Signal is still valid")

# Serialize
signal_dict = signal.to_dict()
```

### Context Model

**Purpose**: Aggregates entities and signals into a cohesive security context for analysis.

**Key Features**:
- **Entity management** - Add, retrieve, filter entities
- **Signal management** - Add, retrieve, filter signals
- **Entity linking** - Find signals related to entities
- **Collection analytics** - Count and query operations
- **Hierarchical organization** - Project/engagement structure
- **Metadata tracking** - Context-level properties

**Example Usage**:
```python
from core.models import Context

context = Context(name="Assessment-2024-Q1")

# Add entities and signals
context.add_entities([entity1, entity2])
context.add_signals([signal1, signal2])

# Query by type
domains = context.get_entities_by_type("domain")
ips = context.get_entities_by_type("ip_address")

# Get signals for entity
entity_signals = context.get_signals_for_entity(entity.id)

# Analytics
print(f"Total entities: {context.entity_count()}")
print(f"Total signals: {context.signal_count()}")

# Serialize
context_dict = context.to_dict()
```

## Schema Management

### Schema Registry Pattern

The Schema Registry provides version management and validation capabilities:

**Features**:
- **Multiple versions** - Support multiple schema versions simultaneously
- **Migration framework** - Upgrade paths between versions
- **Validation** - JSON schema validation for data
- **Global registry** - Pre-configured default schemas

**Pre-registered Schemas**:
- `entity` (v1.0.0) - Entity data validation
- `signal` (v1.0.0) - Signal data validation
- `context` (v1.0.0) - Context data validation

**Usage**:
```python
from core.schema import validate_schema, get_schema, get_registry

# Validate data
if validate_schema("entity", entity_dict):
    print("Entity data is valid")

# Get schema
schema = get_schema("entity")

# Register custom migration
registry = get_registry()
def migrate_v1_to_v2(data):
    data["version"] = "2.0.0"
    return data

registry.register_migration("entity", "1.0.0", "2.0.0", migrate_v1_to_v2)
```

## Utility Functions

### Dictionary Utilities

**Hashing**:
- `generate_hash(data)` - SHA256 hash of dictionary

**Manipulation**:
- `merge_dicts(dict1, dict2)` - Deep merge
- `flatten_dict(data)` - Dot notation flattening
- `unflatten_dict(flat)` - Reconstruct nested dict
- `sort_dict(data)` - Sort keys recursively

**Filtering**:
- `sanitize_dict(data)` - Remove sensitive keys
- `filter_by_keys(data, include/exclude)` - Select/exclude keys
- `compact_dict(data)` - Remove None/empty values

**Access**:
- `get_nested(data, path)` - Get nested value
- `set_nested(data, path, value)` - Set nested value

**Transformation**:
- `diff_dicts(dict1, dict2)` - Calculate differences
- `convert_timestamps(data)` - ISO string to datetime
- `json_encode/decode(data)` - JSON with datetime support

### String Utilities

**Validation**:
- `is_valid_domain(text)` - Domain validation
- `is_valid_ip(text)` - IPv4 validation
- `is_valid_ipv6(text)` - IPv6 validation
- `is_valid_email(text)` - Email validation
- `is_valid_url(text)` - URL validation
- `is_valid_uuid(text)` - UUID validation
- `is_valid_cidr(text)` - CIDR validation

**Normalization**:
- `normalize_domain(text)` - Lowercase, strip, remove trailing dot
- `normalize_email(text)` - Lowercase, strip

**Extraction** (all return deduplicated lists):
- `extract_domain(url)` - Extract from URL
- `extract_domains(text)` - Extract all domains from text
- `extract_emails(text)` - Extract email addresses
- `extract_ips(text)` - Extract IPv4 addresses
- `extract_urls(text)` - Extract URLs

**Transformation**:
- `truncate(text, length)` - Truncate with ellipsis
- `slugify(text)` - Convert to URL-safe slug
- `camel_to_snake(text)` - camelCase → snake_case
- `snake_to_camel(text)` - snake_case → camelCase

## Design Patterns

### Dataclass-Based Models

All core models use Python dataclasses with validation:

```python
@dataclass
class Entity:
    name: str
    entity_type: EntityType
    source: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 0.5
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
```

**Benefits**:
- Type-safe definitions
- Automatic __init__, __repr__, __eq__
- Validation in __post_init__
- Clean serialization

### Factory Methods

Serialization uses factory methods:

```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "id": self.id,
        "name": self.name,
        "entity_type": self.entity_type.value,
        ...
    }

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Entity":
    """Create from dictionary."""
    return cls(
        id=data["id"],
        name=data["name"],
        entity_type=EntityType(data["entity_type"]),
        ...
    )
```

**Benefits**:
- JSON compatibility
- Type conversion
- Bidirectional serialization

### Registry Pattern

Schema versioning uses the Registry pattern:

```python
class SchemaRegistry:
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Dict]] = {}
        self._current_versions: Dict[str, str] = {}
        self._migrations: Dict[str, List[Callable]] = {}
    
    def register_schema(self, name: str, version: str, schema: Dict):
        """Register schema version."""
        ...
    
    def validate(self, name: str, data: Dict) -> bool:
        """Validate data against schema."""
        ...
```

**Benefits**:
- Centralized schema management
- Easy versioning
- Migration support

## Testing

Comprehensive test coverage includes:

**Unit Tests** (`core/tests/test_models.py`):
- Model creation and validation
- Serialization/deserialization
- Property and tag management
- Relationship tracking

**Utility Tests** (`core/tests/test_utils.py`):
- Dictionary operations
- String validation
- Email/domain/IP extraction
- Case transformations

**Schema Tests** (`core/tests/test_schema.py`):
- Schema registration
- Data validation
- Migration execution
- Integration with models

Run tests:
```bash
pytest core/tests/ -v
pytest core/tests/test_models.py -v
pytest core/tests/test_utils.py -v
pytest core/tests/test_schema.py -v
```

## Extension Points

### Adding New Entity Types

```python
# In core/models/entity.py
class EntityType(Enum):
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    # Add new types here
    CUSTOM_TYPE = "custom_type"
```

### Adding New Signal Types

```python
# In core/models/signal.py
class SignalType(Enum):
    DOMAIN_REGISTRATION = "domain_registration"
    DNS_RECORD = "dns_record"
    # Add new types here
    CUSTOM_SIGNAL = "custom_signal"
```

### Adding Schema Migrations

```python
from core.schema import get_registry

registry = get_registry()

def migrate_1_0_to_2_0(data):
    # Transformation logic
    return data

registry.register_migration("entity", "1.0.0", "2.0.0", migrate_1_0_to_2_0)
```

### Adding Utility Functions

```python
# In core/utils/dict_utils.py or string_utils.py
def my_function(data: Dict) -> Any:
    """Custom utility function."""
    ...

# Export in __init__.py
__all__ = [..., "my_function"]
```

## Performance Considerations

- **Hash generation**: Uses SHA256, suitable for deduplication
- **Dictionary operations**: Linear complexity for flatten/unflatten
- **Regex validation**: Pre-compiled patterns for efficiency
- **Schema validation**: Basic field validation (O(n))
- **Serialization**: Recursive with depth-first traversal

## Future Enhancements

1. **Full JSON Schema Validation** - Implement complete JSON schema spec
2. **Async Support** - Async schema validation and migrations
3. **Caching** - Cache compiled regex patterns and schemas
4. **Metrics** - Add performance metrics for operations
5. **Advanced Validation** - Custom validators and constraints
6. **Graph Integration** - Direct integration with graph models
7. **Encryption** - Encrypted field support for sensitive data
8. **Versioning** - Automatic version detection and migration

## Related Documentation

- [Entity Model Reference](../models/entity.py)
- [Signal Model Reference](../models/signal.py)
- [Context Model Reference](../models/context.py)
- [Schema Registry Reference](../schema/schema_registry.py)
- [Dictionary Utilities Reference](../utils/dict_utils.py)
- [String Utilities Reference](../utils/string_utils.py)
