# Core Modules Quick Reference

## 🚀 Quick Start

### Import Core Models
```python
from core.models import Entity, EntityType, Signal, SignalType, Context
```

### Import Utilities
```python
from core.utils import (
    # Dictionary utilities
    merge_dicts, flatten_dict, sanitize_dict,
    # String utilities
    is_valid_domain, extract_emails, normalize_domain
)
```

### Import Schema
```python
from core.schema import validate_schema, get_registry, get_schema
```

---

## 📋 Entity Types (13)

```
domain                Email addresses
ip_address            URL/URIs
host                  Certificates
service               Accounts
person                Credentials
email                 Files
                      Processes, Registry entries, Other
```

---

## 📡 Signal Types (15)

```
domain_registration   HTTP headers
dns_record            Open ports
ip_whois              Vulnerabilities
certificate           Malware
                      Suspicious activity, Configuration, etc.
```

---

## 🎯 Entity Creation

```python
entity = Entity(
    name="example.com",
    entity_type=EntityType.DOMAIN,
    source="dns_collector",
    severity=EntitySeverity.MEDIUM,      # Optional
    confidence=0.85                       # Optional
)

# Add properties
entity.set_property("registrar", "NameCheap")
entity.get_property("registrar")

# Manage tags
entity.add_tag("monitored")
entity.remove_tag("monitored")
entity.tags  # List of tags

# Manage relationships
entity.add_related_entity(other_entity_id)

# Serialize
entity_dict = entity.to_dict()
entity2 = Entity.from_dict(entity_dict)
```

---

## 📊 Signal Creation

```python
signal = Signal(
    source="dns_collector",
    signal_type=SignalType.DNS_RECORD,
    data={"record_type": "A", "value": "1.2.3.4"},
    entity_id=entity.id,                # Optional
    severity=SignalSeverity.LOW,        # Optional
    confidence=SignalConfidence.VERIFIED  # Optional
)

# Add metadata
signal.set_metadata("key", "value")
signal.get_metadata("key")
signal.metadata  # Full metadata dict

# Check expiry
if not signal.is_expired():
    print("Signal is valid")

# Serialize
signal_dict = signal.to_dict()
signal2 = Signal.from_dict(signal_dict)
```

---

## 📦 Context Management

```python
context = Context(name="Assessment-2024")

# Add items
context.add_entity(entity)
context.add_entities([entity1, entity2])
context.add_signal(signal)
context.add_signals([signal1, signal2])

# Query entities
domains = context.get_entities_by_type("domain")
entity = context.get_entity(entity_id)

# Query signals
signals = context.get_signals_by_type("dns_record")
entity_signals = context.get_signals_for_entity(entity_id)
active_signals = context.get_active_signals()

# Remove items
context.remove_entity(entity_id)
context.remove_signal(signal_id)

# Analytics
context.entity_count()
context.signal_count()

# Serialize
context_dict = context.to_dict()
context2 = Context.from_dict(context_dict)
```

---

## ✅ Validation Functions

```python
from core.utils import (
    is_valid_domain,      # "example.com" → True
    is_valid_email,       # "user@example.com" → True
    is_valid_ip,          # "192.0.2.1" → True
    is_valid_ipv6,        # "2001:db8::1" → True
    is_valid_url,         # "https://example.com" → True
    is_valid_uuid,        # UUID string → True
    is_valid_cidr         # "192.0.2.0/24" → True
)
```

---

## 🔍 Extraction Functions

```python
from core.utils import (
    extract_domain,       # From URL
    extract_domains,      # All domains from text
    extract_emails,       # All emails from text
    extract_ips,          # All IPs from text
    extract_urls          # All URLs from text
)

# Example
text = "Contact admin@example.com or visit example.org"
emails = extract_emails(text)  # ["admin@example.com"]
domains = extract_domains(text)  # ["example.com", "example.org"]
```

---

## 🛠️ Dictionary Utilities

```python
from core.utils import (
    generate_hash,        # SHA256
    merge_dicts,          # Deep merge
    flatten_dict,         # Dot notation
    unflatten_dict,       # Reconstruct
    sanitize_dict,        # Remove secrets
    filter_by_keys,       # Include/exclude
    get_nested,           # Dot notation access
    set_nested,           # Dot notation assignment
    sort_dict,            # Recursive sort
    compact_dict,         # Remove None/empty
    diff_dicts,           # Calculate differences
    json_encode,          # JSON with datetime
    json_decode           # JSON with datetime
)

# Examples
flat = flatten_dict({"a": {"b": "c"}})  # {"a.b": "c"}
merged = merge_dicts(dict1, dict2)
value = get_nested(data, "user.profile.name")
set_nested(data, "user.email", "new@example.com")
```

---

## 🔄 String Transformers

```python
from core.utils import (
    truncate,             # Add ellipsis if too long
    slugify,              # URL-safe slug
    camel_to_snake,       # myVar → my_var
    snake_to_camel        # my_var → myVar
)
```

---

## 🔐 Schema Validation

```python
from core.schema import validate_schema, get_schema, get_registry

# Validate
entity_dict = entity.to_dict()
is_valid = validate_schema("entity", entity_dict)

# Get schema
schema = get_schema("entity")  # Or specific version
schema = get_schema("entity", "1.0.0")

# Custom validation
registry = get_registry()
is_valid = registry.validate("entity", data)

# Register custom schema
registry.register_schema("custom", "1.0.0", schema_dict)

# Migration
def migrate(data):
    data["new_field"] = "default"
    return data

registry.register_migration("entity", "1.0.0", "2.0.0", migrate)
new_data = registry.migrate("entity", old_data, "1.0.0", "2.0.0")
```

---

## 📐 Severity Levels

**EntitySeverity**:
- `CRITICAL` - Immediate action required
- `HIGH` - Urgent attention needed
- `MEDIUM` - Should be addressed
- `LOW` - Monitor situation
- `INFO` - Informational

**SignalSeverity**: Same levels

---

## 🎯 Confidence Levels

**EntitySeverity**: 0.0 - 1.0 (float)
- 0.9+ : Very high confidence
- 0.7-0.9 : High confidence
- 0.5-0.7 : Medium confidence
- 0.3-0.5 : Low confidence
- <0.3 : Very low confidence

**SignalConfidence** (enum):
- `VERIFIED` - Confirmed
- `HIGH` - Very likely
- `MEDIUM` - Probable
- `LOW` - Possible
- `UNVERIFIED` - Unconfirmed

---

## 🔑 Common Workflows

### Assess a Domain
```python
# Create entity
domain = Entity("example.com", EntityType.DOMAIN, "osint")

# Add signals
for signal_data in signals:
    signal = Signal(
        source="scanner",
        signal_type=SignalType.OPEN_PORT,
        data=signal_data,
        entity_id=domain.id
    )
    context.add_signal(signal)

# Query results
domain_signals = context.get_signals_for_entity(domain.id)
```

### Track Multiple Findings
```python
# Create context
context = Context("Assessment-Q1-2024")

# Add entities from discovery
for ip in discovered_ips:
    entity = Entity(ip, EntityType.IP_ADDRESS, "scanner")
    context.add_entity(entity)

# Categorize by type
ips = context.get_entities_by_type("ip_address")
```

### Deduplicate Signals
```python
from core.utils import generate_hash

signals_dict = {}
for signal in signals:
    signal_dict = signal.to_dict()
    hash_val = generate_hash(signal_dict)
    if hash_val not in signals_dict:
        signals_dict[hash_val] = signal
        context.add_signal(signal)
```

### Export Data
```python
# Serialize context
context_dict = context.to_dict()

# Export as JSON
import json
json_str = json.dumps(context_dict, default=str)

# Save to file
with open("assessment.json", "w") as f:
    json.dump(context_dict, f, indent=2, default=str)

# Restore from file
with open("assessment.json") as f:
    restored = Context.from_dict(json.load(f))
```

---

## 📚 File Structure

```
core/
├── models/              # Data models
│   ├── entity.py        # Entity class
│   ├── signal.py        # Signal class
│   ├── context.py       # Context class
│   └── __init__.py      # Exports
├── schema/              # Schema management
│   ├── schema_registry.py  # Registry class
│   └── __init__.py      # Exports
├── utils/               # Utilities
│   ├── dict_utils.py    # Dictionary functions
│   ├── string_utils.py  # String functions
│   └── __init__.py      # Exports
└── tests/               # Tests
    ├── test_models.py   # Model tests
    ├── test_utils.py    # Utility tests
    ├── test_schema.py   # Schema tests
    └── __init__.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest core/tests/ -v

# Run specific test
pytest core/tests/test_models.py::TestEntity::test_entity_creation -v

# Run with coverage
pytest core/tests/ --cov=core

# Run examples
python examples/core_modules_example.py

# Verify implementation
python verify_core_modules.py
```

---

## 📖 Documentation

- **Architecture**: `docs/architecture/core-modules.md`
- **Examples**: `examples/core_modules_example.py`
- **Summary**: `CORE_MODULES_SUMMARY.md`
- **Implementation**: `IMPLEMENTATION_COMPLETE.md`
- **Status**: `FINAL_STATUS_REPORT.md`

---

## 🔗 Related Modules

- **Collectors** - Produce signals
- **Normalizers** - Consume/produce entities
- **Engines** - Consume entities/signals
- **Graph** - Manage relationships
- **API** - Query/expose
- **CLI** - Commands
- **UI** - Visualization

---

## 💡 Pro Tips

1. Always validate domains/emails with `is_valid_*` functions
2. Use `flatten_dict` for accessing nested data
3. Use `sanitize_dict` before logging/exporting
4. Use `extract_*` functions to find indicators in text
5. Always set `entity_id` on signals for tracking
6. Validate data with `validate_schema` before processing
7. Use `merge_dicts` for combining configurations
8. Use `diff_dicts` to track changes
9. Check signal expiry with `is_expired()` before use
10. Always serialize with `to_dict()` before JSON export

---

## ❓ FAQ

**Q: How do I create an entity with confidence?**
```python
entity = Entity("example.com", EntityType.DOMAIN, "osint", confidence=0.92)
```

**Q: How do I link an entity to a signal?**
```python
signal = Signal(..., entity_id=entity.id)
```

**Q: How do I query by multiple types?**
```python
domains = context.get_entities_by_type("domain")
ips = context.get_entities_by_type("ip_address")
```

**Q: How do I export context as JSON?**
```python
import json
data = context.to_dict()
json_str = json.dumps(data, default=str)
```

**Q: How do I import context from JSON?**
```python
import json
data = json.loads(json_str)
context = Context.from_dict(data)
```

---

**For more information, see the complete documentation in the `docs/` directory.**
