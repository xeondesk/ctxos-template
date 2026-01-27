# Normalizers Module

The Normalizers module provides data normalization, deduplication, field mapping, and schema validation for entities and signals in CtxOS.

## Components

### 1. Normalization Engine (`normalization_engine.py`)

Handles data normalization and deduplication with multiple strategies.

**Features:**
- Hash-based and similarity-based deduplication
- Field normalization (case conversion, whitespace trimming)
- Entity and signal merging
- Configurable normalization rules

**Usage Example:**

```python
from normalizers import NormalizationEngine, NormalizationConfig

# Create engine with custom config
config = NormalizationConfig(
    deduplication_strategy="hash",
    normalize_case=True,
    trim_whitespace=True,
    similarity_threshold=0.95
)
engine = NormalizationEngine(config)

# Normalize entities
entities = [
    {"name": "EXAMPLE.COM", "type": "domain"},
    {"name": "example.com", "type": "domain"},
]
normalized = [engine.normalize_entity(e) for e in entities]
deduplicated = engine.deduplicate_entities(normalized)

# Merge duplicates
merged = engine.merge_entities(primary, duplicate)
```

### 2. Field Mapper (`mappers/field_mapper.py`)

Maps fields from different data sources to standardized formats.

**Features:**
- Source-specific field mapping
- Field value transformers
- Batch processing
- Preserve unmapped fields

**Usage Example:**

```python
from normalizers.mappers import FieldMapper

mapper = FieldMapper()

# Register mapping for DNS source
dns_mapping = {
    "domain_name": "name",
    "domain_type": "type",
    "register_date": "registered"
}
mapper.register_mapping("dns_source", dns_mapping)

# Register transformer for field values
def parse_date(value):
    return datetime.fromisoformat(value)

mapper.register_transformer("dns_source", "register_date", parse_date)

# Map entity
entity = {
    "domain_name": "example.com",
    "domain_type": "registered",
    "register_date": "2024-01-01"
}
mapped = mapper.map_entity("dns_source", entity)
```

### 3. Schema Validator (`validators/schema_validator.py`)

Validates entities and signals against JSON schemas.

**Features:**
- JSON schema validation
- Required field checking
- Type validation
- Custom validation functions
- Batch validation

**Usage Example:**

```python
from normalizers.validators import SchemaValidator

validator = SchemaValidator()

# Register schema
entity_schema = {
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "name": {"type": "string"},
        "type": {"type": "string"},
        "confidence": {"type": "number"}
    }
}
validator.register_schema("entity", entity_schema)

# Validate entity
entity = {"name": "example.com", "type": "domain", "confidence": 0.95}
is_valid, errors = validator.validate_entity(entity)

# Custom validator
def domain_validator(entity):
    errors = []
    if not entity.get("name", "").endswith(".com"):
        errors.append("Domain must end with .com")
    return len(errors) == 0, errors

validator.register_custom_validator("domain", domain_validator)
```

### 4. Normalization Rules (`rules/normalization_rules.py`)

Applies business logic rules to normalize data.

**Features:**
- Field removal rules
- Field renaming rules
- Default value assignment
- Conditional rules
- Rule engine for sequential application

**Usage Example:**

```python
from normalizers.rules import (
    RuleEngine,
    FieldRemovalRule,
    FieldRenameRule,
    DefaultValueRule
)

rule_engine = RuleEngine()

# Add rules
rule_engine.register_rule(
    FieldRemovalRule(["internal_id", "debug_info"])
)
rule_engine.register_rule(
    FieldRenameRule({"src_ip": "source_ip", "dst_ip": "dest_ip"})
)
rule_engine.register_rule(
    DefaultValueRule({"status": "unknown", "confidence": 0.0})
)

# Apply rules
item = {"internal_id": "123", "src_ip": "1.2.3.4"}
normalized = rule_engine.apply_rules(item)
```

## Complete Normalization Pipeline

A typical normalization workflow:

```python
from normalizers import NormalizationEngine
from normalizers.mappers import FieldMapper
from normalizers.validators import SchemaValidator
from normalizers.rules import RuleEngine, DefaultValueRule

# Initialize components
mapper = FieldMapper()
engine = NormalizationEngine()
validator = SchemaValidator()
rule_engine = RuleEngine()

# Configure
mapper.register_mapping("collector_a", {"old_field": "new_field"})
validator.register_schema("entity", {...})
rule_engine.register_rule(DefaultValueRule({"status": "active"}))

# Process data
raw_entities = [...]
mapped = [mapper.map_entity("collector_a", e) for e in raw_entities]
normalized = [engine.normalize_entity(e) for e in mapped]
processed = [rule_engine.apply_rules(e) for e in normalized]
deduplicated = engine.deduplicate_entities(processed)
valid_results = [(e, validator.validate_entity(e)) for e in deduplicated]
```

## Configuration

### NormalizationConfig

```python
NormalizationConfig(
    deduplication_strategy="hash",    # "hash" or "field-based"
    field_weights={},                 # Weights for similarity calculation
    similarity_threshold=0.95,         # Threshold for field-based dedup
    normalize_case=True,               # Convert to lowercase
    trim_whitespace=True,              # Trim whitespace
    remove_duplicates=True             # Enable deduplication
)
```

## Testing

Unit tests are in `tests/test_normalizers.py`:

```bash
pytest normalizers/tests/test_normalizers.py -v
```

Integration tests are in `tests/test_integration.py`:

```bash
pytest normalizers/tests/test_integration.py -v
```

## Architecture

```
normalizers/
├── __init__.py                    # Module exports
├── normalization_engine.py        # Core normalization logic
├── mappers/
│   ├── __init__.py
│   └── field_mapper.py           # Field mapping and transformation
├── validators/
│   ├── __init__.py
│   └── schema_validator.py       # Schema validation
├── rules/
│   ├── __init__.py
│   └── normalization_rules.py    # Normalization rules and rule engine
└── tests/
    ├── __init__.py
    ├── test_normalizers.py       # Unit tests
    └── test_integration.py       # Integration tests
```

## Best Practices

1. **Normalize early**: Apply normalization close to data ingestion
2. **Map consistently**: Use consistent field mappings across sources
3. **Validate always**: Validate data before processing further
4. **Deduplicate wisely**: Choose strategy based on data characteristics
5. **Chain operations**: Build reusable normalization pipelines

## Future Enhancements

- [ ] Streaming normalization for large datasets
- [ ] ML-based similarity detection
- [ ] Field-level audit logging
- [ ] Normalization performance profiling
- [ ] Integration with graph engine for entity resolution
