# 🎯 Strategic Plan: Sections 5 & 7 Implementation

## Current Status
- ✅ Section 4: Engines & Scoring - Complete
- ⏳ Section 5: Agents & MCP - Ready to Start
- ⏳ Section 7: API Layer - Ready to Start

---

## Section 5: Agents & MCP Implementation Plan

### Phase 1: Agent Infrastructure
**Timeline**: ~2 weeks

#### 1.1 Enhanced BaseAgent
```python
class BaseAgent(ABC):
    """Abstract base for all agents."""
    - name: str
    - version: str
    - description: str
    
    Abstract Methods:
    - analyze(context: Context) -> AnalysisResult
    - validate_config(config: Dict) -> bool
    - configure(config: Dict) -> None
    - explain(result: AnalysisResult) -> str
    
    Features:
    - Audit logging (WHO, WHAT, WHEN)
    - State tracking
    - Error handling
    - Configuration management
```

#### 1.2 Agent Types to Implement
1. **Context Summarizer Agent** - Reduce context to key findings
2. **Gap Detector Agent** - Identify missing data/signals
3. **Hypothesis Generator Agent** - Suggest likely issues
4. **Explainability Agent** - Explain scoring decisions
5. **Recommendation Agent** - Prioritize fixes (bonus)

#### 1.3 Agent Integration Pattern
```
Input: ScoringResult(s) from Engines
  ↓
Agent Analysis
  ↓
Output: AnalysisResult
  ↓
Audit Log Entry
```

### Phase 2: Integration with Engines
**Timeline**: ~1 week

```
Collector Data
    ↓
Normalizers
    ↓
Engines (Risk, Exposure, Drift)
    ↓
Agents (Context, Gap, Hypothesis, Explainability)
    ↓
Recommendations/Actions
```

### Phase 3: MCP Server Integration
**Timeline**: ~1 week

- Expose agents via MCP protocol
- Enable remote agent execution
- Implement streaming responses
- Handle long-running analysis

### Phase 4: Testing & Audit Logging
**Timeline**: ~1 week

- Unit tests per agent (80%+ coverage)
- Integration tests for agent chains
- Audit logging verification
- Performance benchmarks

---

## Section 7: API Layer Implementation Plan

### Phase 1: REST API Foundation
**Timeline**: ~2 weeks

#### 1.1 Core Endpoints

**Scoring Endpoints**:
```
POST /api/v1/score
  Input: Entity + Signals
  Output: ScoringResult
  
POST /api/v1/score/batch
  Input: [Entity + Signals]
  Output: [ScoringResult]
  
GET /api/v1/score/history/{entity_id}
  Output: [ScoringResult] (historical)
```

**Analysis Endpoints**:
```
POST /api/v1/analyze
  Input: Entity + ScoringResult
  Output: AnalysisResult
  
GET /api/v1/analyze/{result_id}
  Output: AnalysisResult
```

**Configuration Endpoints**:
```
GET /api/v1/config/engines
  Output: Current engine configuration
  
PUT /api/v1/config/engines
  Input: New configuration
  Output: Updated configuration
```

#### 1.2 FastAPI Implementation
```
- app.py: FastAPI application setup
- routes/scoring.py: Scoring endpoints
- routes/analysis.py: Analysis endpoints
- routes/config.py: Configuration endpoints
- models/: Pydantic response models
- middleware/: Auth, CORS, logging
```

### Phase 2: Authentication & RBAC
**Timeline**: ~1 week

#### 2.1 Authentication
- JWT tokens
- OAuth2 support
- API key authentication
- Rate limiting per user/key

#### 2.2 RBAC (Role-Based Access Control)
```
Roles:
- admin: Full access
- analyst: Read/score/analyze
- viewer: Read-only
- api_client: Programmatic access

Permissions:
- score:read, score:write
- analyze:read, analyze:write
- config:read, config:write (admin only)
```

### Phase 3: CLI Integration
**Timeline**: ~1 week

```bash
# Query API from CLI
ctxos score --entity example.com --engine all
ctxos analyze --result-id <id>
ctxos config get engines
ctxos config set engines --file new_config.yml

# Batch operations
ctxos score --input entities.json --format json
ctxos score --db postgresql://... --query "SELECT * FROM entities"
```

### Phase 4: Documentation & Testing
**Timeline**: ~1 week

- API documentation (Swagger/OpenAPI)
- Integration tests (pytest)
- Load testing
- Security testing

---

## Implementation Architecture

```
┌─────────────────────────────────────────────────┐
│              CLI & UI Layer                      │
│  (ctxos commands + web dashboard)               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│        REST API Layer (Section 7)               │
│  ├─ /api/v1/score                              │
│  ├─ /api/v1/analyze                            │
│  ├─ /api/v1/config                             │
│  └─ Authentication/RBAC                         │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      Agents Layer (Section 5)                   │
│  ├─ Context Summarizer                         │
│  ├─ Gap Detector                               │
│  ├─ Hypothesis Generator                       │
│  ├─ Explainability                             │
│  └─ Recommendation                             │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      Scoring Engines (Section 4) ✅             │
│  ├─ Risk Engine                                │
│  ├─ Exposure Engine                            │
│  └─ Drift Engine                               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│   Data Layer                                     │
│  ├─ Collectors                                 │
│  ├─ Normalizers                                │
│  └─ Storage                                    │
└─────────────────────────────────────────────────┘
```

---

## Implementation Sequence

### Week 1: Foundation
- [ ] Agent infrastructure (BaseAgent enhancements)
- [ ] REST API structure (FastAPI setup)
- [ ] Basic endpoints (scoring)

### Week 2: Agents
- [ ] Context Summarizer agent
- [ ] Gap Detector agent
- [ ] Hypothesis Generator agent
- [ ] Explainability agent

### Week 3: API Completion
- [ ] Authentication & RBAC
- [ ] CLI integration
- [ ] Configuration endpoints
- [ ] Batch processing

### Week 4: Integration & Testing
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Security hardening

---

## File Structure (New)

```
agents/
├── base_agent.py (enhanced)
├── context_summarizer/
│   ├── __init__.py
│   └── summarizer.py
├── gap_detector/
│   ├── __init__.py
│   └── detector.py
├── hypothesis_generator/
│   ├── __init__.py
│   └── generator.py
├── explainability/
│   ├── __init__.py
│   └── explainer.py
├── tests/
│   ├── test_context_summarizer.py
│   ├── test_gap_detector.py
│   ├── test_hypothesis_generator.py
│   └── test_explainability.py
└── audit_logger.py (new)

api/
├── server/
│   ├── __init__.py
│   ├── app.py
│   ├── routes/
│   │   ├── scoring.py
│   │   ├── analysis.py
│   │   └── config.py
│   ├── models/
│   │   ├── request.py
│   │   └── response.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── rbac.py
│   │   └── logging.py
│   └── tests/
│       ├── test_scoring_api.py
│       ├── test_analysis_api.py
│       └── test_auth.py
├── schemas/ (existing)
├── controllers/ (existing)
└── middlewares/ (existing)
```

---

## Key Technologies

### Section 5 (Agents)
- Python dataclasses/typing
- Logging framework
- Async support (optional)
- MCP SDK

### Section 7 (API)
- FastAPI (modern, async)
- Pydantic (validation)
- SQLAlchemy (optional ORM)
- JWT/OAuth2
- Pytest (testing)

---

## Success Criteria

### Section 5
- ✅ 4 agent types implemented
- ✅ 40+ integration tests
- ✅ 80%+ code coverage
- ✅ Audit logging working
- ✅ MCP endpoints exposed

### Section 7
- ✅ REST API fully functional
- ✅ Authentication working
- ✅ RBAC enforced
- ✅ CLI integrated
- ✅ 50+ API tests
- ✅ OpenAPI documentation

---

## Next Steps

### Option A: Start Section 5 (Agents)
- Implement BaseAgent enhancements
- Create Context Summarizer agent first
- Add comprehensive tests
- Integrate with engines

### Option B: Start Section 7 (API)
- Set up FastAPI application
- Create basic scoring endpoints
- Add authentication layer
- Integrate with engines

### Option C: Parallel (Recommended)
- Team 1: Section 5 (Agents)
- Team 2: Section 7 (API)
- Both teams integrate in Week 4

---

## Estimated Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Foundation | 1 week | Week 1 | Week 1 |
| Core Implementation | 2 weeks | Week 2 | Week 3 |
| Integration & Testing | 1 week | Week 4 | Week 4 |
| **Total** | **4 weeks** | - | - |

---

## Questions to Answer Before Starting

1. **Parallel or Sequential?** Start both sections in parallel or one after the other?
2. **Database?** Use database for result storage or in-memory?
3. **GraphQL?** Include GraphQL in addition to REST?
4. **Async?** Use async for long-running operations?
5. **Containerization?** Docker setup for API server?
6. **Monitoring?** Prometheus metrics for API?

---

**Ready to proceed?** Let me know which section you'd like to start with, and I'll begin implementation immediately! 🚀
