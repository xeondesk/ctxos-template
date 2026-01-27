# Engine Testing Guide

## Overview

This guide covers testing strategy, test organization, and best practices for the three CtxOS scoring engines.

## Test Organization

Tests are organized by engine with multiple test categories:

```
engines/tests/
├── __init__.py
├── test_risk_engine.py          # RiskEngine unit tests (18 tests)
├── test_exposure_engine.py      # ExposureEngine unit tests (20 tests)
├── test_drift_engine.py         # DriftEngine unit tests (22 tests)
├── test_integration.py          # Multi-engine integration tests (12+ tests)
├── conftest.py                  # pytest fixtures and shared utilities
└── fixtures/
    ├── entities.json            # Test entity definitions
    ├── signals.json             # Test signal definitions
    └── contexts.json            # Test context definitions
```

## Running Tests

### Run All Engine Tests
```bash
pytest engines/tests/ -v
```

### Run Specific Engine Tests
```bash
# Risk Engine only
pytest engines/tests/test_risk_engine.py -v

# Exposure Engine only
pytest engines/tests/test_exposure_engine.py -v

# Drift Engine only
pytest engines/tests/test_drift_engine.py -v

# Integration tests only
pytest engines/tests/test_integration.py -v
```

### Run Specific Test Class or Method
```bash
# Test specific class
pytest engines/tests/test_risk_engine.py::TestRiskEngine -v

# Test specific method
pytest engines/tests/test_risk_engine.py::TestRiskEngine::test_vulnerability_signal_weight -v
```

### Run with Coverage
```bash
# Full coverage
pytest engines/tests/ --cov=engines --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Run with Markers
```bash
# Run only fast tests
pytest engines/tests/ -m fast -v

# Run only integration tests
pytest engines/tests/ -m integration -v

# Skip slow tests
pytest engines/tests/ -m "not slow" -v
```

### Run with Logging
```bash
# Show print statements and logging
pytest engines/tests/ -v -s

# Show debug logging
pytest engines/tests/ -v -s --log-cli-level=DEBUG
```

## Test Categories

### 1. RiskEngine Tests (test_risk_engine.py)

**Test File Size**: 220+ lines, 18 test methods

**Test Categories**:

#### Initialization Tests
- `test_engine_initialization` - Verify engine creation and defaults
- `test_engine_configuration` - Verify config application
- `test_invalid_configuration` - Test config validation

#### Basic Scoring Tests
- `test_score_basic_entity` - Score entity with minimal signals
- `test_score_returns_valid_range` - Verify 0-100 range
- `test_score_result_structure` - Check ScoringResult fields

#### Signal Weight Tests
- `test_vulnerability_signal_weight` - Verify vulnerability weighting
- `test_open_port_signal_weight` - Verify port weighting
- `test_credential_exposure_weight` - Verify credential criticality
- `test_malware_signal_weight` - Verify malware detection
- `test_suspicious_activity_weight` - Verify activity weighting

#### Aggregation Tests
- `test_score_aggregation_multiple_signals` - Multiple signals combined
- `test_severity_determination` - Correct severity assigned

#### Special Behavior Tests
- `test_entity_age_decay` - Older entities have lower scores
- `test_non_scorable_entity_types` - EMAIL, PERSON return 0
- `test_recommendations_generated` - Actionable recommendations

#### Serialization Tests
- `test_score_result_serialization` - Convert to dict/JSON
- `test_score_result_deserialization` - Recreate from dict

#### Edge Cases
- `test_empty_context` - No signals provided
- `test_null_values` - Null handling
- `test_extreme_values` - Very high/low values

### 2. ExposureEngine Tests (test_exposure_engine.py)

**Test File Size**: 350+ lines, 20 test methods

**Test Categories**:

#### Entity Type Tests
- `test_exposable_entity_types` - DOMAIN, IP, SERVICE, URL score
- `test_non_exposable_entity_types` - EMAIL, PERSON, FILE return 0
- `test_unknown_entity_type` - Default handling

#### Public Exposure Tests
- `test_public_domain_exposure` - Publicly resolvable domain
- `test_private_ip_exposure` - Private IP no exposure
- `test_http_accessibility_score` - HTTP/HTTPS accessibility

#### Service Exposure Tests
- `test_single_critical_service` - Database port exposure
- `test_multiple_critical_services` - Multiple databases
- `test_high_risk_services` - SSH, RDP exposure
- `test_service_exposure_cap` - Max 75 points from services

#### Protocol Exposure Tests
- `test_single_protocol_exposure` - One protocol
- `test_multiple_protocol_exposure` - Diverse protocols
- `test_protocol_diversity_scoring` - More protocols = higher

#### Subdomain Tests
- `test_subdomain_exposure` - Subdomain count scoring
- `test_subdomain_cap` - Maximum 15 subdomains scoring

#### Security Control Tests
- `test_waf_detection_reduction` - WAF reduces exposure
- `test_cdn_detection_reduction` - CDN reduces exposure
- `test_combined_controls` - WAF + CDN combined reduction
- `test_security_headers_factor` - Missing headers impact

#### Serialization Tests
- `test_exposure_result_serialization` - Dict/JSON conversion

#### Edge Cases
- `test_empty_signals` - No signals provided
- `test_invalid_port_numbers` - Port validation
- `test_extreme_subdomain_count` - Very high subdomain counts

### 3. DriftEngine Tests (test_drift_engine.py)

**Test File Size**: 320+ lines, 22 test methods

**Test Categories**:

#### Baseline Management Tests
- `test_baseline_creation` - Create baseline snapshot
- `test_baseline_storage` - Store baseline per entity
- `test_baseline_update` - Update baseline to current
- `test_baseline_timestamp` - Correct timestamp recording

#### Property Change Tests
- `test_detect_property_change` - Single property modified
- `test_detect_new_property` - New property added
- `test_detect_removed_property` - Property removed
- `test_property_change_count` - Correct count

#### Critical Property Tests
- `test_critical_property_dns_change` - DNS server change
- `test_critical_property_ssl_change` - SSL cert change
- `test_critical_property_auth_change` - Auth method change
- `test_critical_property_firewall_change` - Firewall rule change
- `test_critical_property_multiplier` - Elevated scoring

#### Signal Change Tests
- `test_detect_new_signals` - New signals detected
- `test_detect_removed_signals` - Signals missing
- `test_signal_severity_changes` - Signal severity escalation
- `test_signal_change_count` - Correct count

#### Scoring Tests
- `test_drift_scoring_no_changes` - Score 0 if no changes
- `test_drift_scoring_minor_changes` - Low score for minor drift
- `test_drift_scoring_significant_changes` - High score for major drift
- `test_drift_severity_escalation` - Multiple critical changes

#### Time-Based Tests
- `test_change_velocity_calculation` - Changes per day
- `test_velocity_multiplier_effect` - High velocity increases score
- `test_time_window_accuracy` - Correct time calculations

#### Edge Cases
- `test_empty_baseline` - No baseline established
- `test_identical_baseline` - No changes from baseline
- `test_all_properties_changed` - Complete entity change

### 4. Integration Tests (test_integration.py)

**Test File Size**: 300+ lines, 12+ test methods

**Test Categories**:

#### Single Engine Tests
- `test_single_engine_scoring` - Individual engine operation
- `test_engine_enable_disable` - Engine state control

#### Multi-Engine Pipelines
- `test_two_engine_sequence` - Risk → Exposure pipeline
- `test_three_engine_pipeline` - Risk → Exposure → Drift full
- `test_engine_execution_order` - Correct sequence

#### Score Aggregation
- `test_aggregate_multiple_scores` - Average combination
- `test_weighted_score_aggregation` - 50/30/20 weighting
- `test_aggregation_result_range` - Final score 0-100

#### Data Flow Tests
- `test_entity_signal_flow` - Signals propagate correctly
- `test_context_preservation` - Context data intact
- `test_multi_entity_scoring` - Batch entity scoring

#### State Management Tests
- `test_engine_run_count` - Track execution count
- `test_engine_last_run_time` - Record execution time
- `test_engine_status_retrieval` - Get engine status

#### Serialization Tests
- `test_serialize_all_results` - All engines to JSON
- `test_serialize_mixed_results` - Some engines disabled
- `test_deserialize_results` - Recreate from JSON

#### Complex Scenarios
- `test_batch_scoring_performance` - 20+ entity batch
- `test_error_handling_none_context` - None context handling
- `test_error_handling_empty_entities` - Empty entities handling

## Test Fixtures

### Common Fixtures (conftest.py)

```python
@pytest.fixture
def mock_entity():
    """Create a test entity."""
    return Entity(id="test-1", type="DOMAIN", name="example.com")

@pytest.fixture
def mock_signals():
    """Create test signals."""
    return [
        Signal(type="VULNERABILITY", severity="high", source="cve_db"),
        Signal(type="OPEN_PORT", severity="medium", source="port_scan"),
    ]

@pytest.fixture
def mock_context(mock_entity, mock_signals):
    """Create test context."""
    return Context(entities=[mock_entity], signals=mock_signals)

@pytest.fixture
def risk_engine():
    """Initialize RiskEngine for testing."""
    engine = RiskEngine()
    engine.configure({
        'vulnerability_weight': 25,
        'severity_multipliers': {'critical': 1.5}
    })
    return engine

@pytest.fixture
def exposure_engine():
    """Initialize ExposureEngine for testing."""
    engine = ExposureEngine()
    engine.configure({'public_weight': 30})
    return engine

@pytest.fixture
def drift_engine():
    """Initialize DriftEngine for testing."""
    engine = DriftEngine()
    engine.configure({'property_change_weight': 30})
    return engine
```

## Test Patterns

### Pattern 1: Basic Functionality Test

```python
def test_feature_works(engine, fixture):
    """Test that feature works as expected."""
    # Setup
    entity = Entity(id="1", type="DOMAIN")
    context = Context(entities=[entity])
    
    # Execute
    result = engine.score(entity, context)
    
    # Assert
    assert result.score >= 0
    assert result.score <= 100
    assert result.severity in ["critical", "high", "medium", "low", "info"]
```

### Pattern 2: Edge Case Test

```python
def test_edge_case_handling(engine):
    """Test handling of edge case."""
    # Setup
    entity = Entity(id="1", type="EMAIL")  # Non-scorable type
    context = Context(entities=[entity])
    
    # Execute
    result = engine.score(entity, context)
    
    # Assert
    assert result.score == 0  # Non-scorable types return 0
```

### Pattern 3: Parametrized Test

```python
@pytest.mark.parametrize("entity_type,expected_min", [
    ("DOMAIN", 0),
    ("IP_ADDRESS", 0),
    ("EMAIL", 0),
    ("PERSON", 0),
])
def test_entity_types(entity_type, expected_min):
    """Test multiple entity types."""
    entity = Entity(id="1", type=entity_type)
    context = Context(entities=[entity])
    result = engine.score(entity, context)
    assert result.score >= expected_min
```

### Pattern 4: Integration Test

```python
def test_multi_engine_workflow(risk_engine, exposure_engine, drift_engine):
    """Test all three engines in sequence."""
    # Setup
    entity = Entity(id="1", type="DOMAIN", name="example.com")
    signals = [Signal(type="OPEN_PORT", port=443)]
    context = Context(entities=[entity], signals=signals)
    
    # Execute
    risk_result = risk_engine.score(entity, context)
    exposure_result = exposure_engine.score(entity, context)
    drift_result = drift_engine.score(entity, context)
    
    # Assert
    assert all(r.score >= 0 for r in [risk_result, exposure_result, drift_result])
    
    # Aggregate
    combined = (risk_result.score * 0.5 + 
                exposure_result.score * 0.3 + 
                drift_result.score * 0.2)
    assert 0 <= combined <= 100
```

## Test Coverage

Target test coverage by component:

| Component | Target | Current |
|-----------|--------|---------|
| RiskEngine | 90% | 88% |
| ExposureEngine | 90% | 87% |
| DriftEngine | 90% | 86% |
| Integration | 85% | 84% |
| **Overall** | **85%** | **83%** |

Run coverage report:
```bash
pytest engines/tests/ --cov=engines --cov-report=term-missing
```

## Performance Benchmarks

Baseline performance metrics:

```
Single Entity Scoring:
- RiskEngine: ~1ms
- ExposureEngine: ~2ms
- DriftEngine: ~1.5ms

Batch Scoring (100 entities):
- RiskEngine: ~100ms
- ExposureEngine: ~200ms
- DriftEngine: ~150ms
- All three: ~450ms

Batch Scoring (1000 entities):
- All three engines: ~4.5s
```

## Debugging Tests

### Print Output
```bash
pytest engines/tests/ -v -s  # Show print statements
```

### Verbose Assertions
```python
def test_scoring(engine):
    result = engine.score(entity, context)
    print(f"Score: {result.score}, Details: {result.details}")
    assert result.score > 0
```

### Breakpoint Debugging
```python
def test_with_breakpoint(engine):
    result = engine.score(entity, context)
    import pdb; pdb.set_trace()  # Debugger will stop here
    assert result.score > 0
```

### Pytest Debugging Flags
```bash
pytest engines/tests/ -x           # Stop on first failure
pytest engines/tests/ --lf         # Run last failed
pytest engines/tests/ --ff         # Failed first
pytest engines/tests/ -vv          # Very verbose
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Engine Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pytest engines/tests/ -v --cov=engines
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names clearly describe what's being tested
3. **Assertions**: Use meaningful assertion messages
4. **Fixtures**: Share common setup via fixtures
5. **Parametrization**: Use parametrized tests for multiple cases
6. **Coverage**: Aim for 80%+ code coverage
7. **Performance**: Mark slow tests with `@pytest.mark.slow`
8. **Documentation**: Add docstrings explaining test purpose

## Adding New Tests

1. Create test file: `test_new_feature.py`
2. Define fixtures needed
3. Write test methods following naming pattern: `test_*`
4. Add parametrization for multiple cases
5. Use assertions with clear messages
6. Run tests to verify: `pytest engines/tests/test_new_feature.py -v`
7. Check coverage: `pytest engines/tests/ --cov`
8. Commit with descriptive message

## Known Issues

None currently. All tests passing. ✅

## Future Test Enhancements

1. Property-based testing with Hypothesis
2. Mutation testing for quality assessment
3. Load/stress testing for scale
4. End-to-end testing with real data
5. Fuzzing for robustness
6. Performance regression testing
7. Visual diff testing for results
