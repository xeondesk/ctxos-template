# 🗂 CtxOS TODO Roadmap ✅

## 0️⃣ Foundation & Repo

* [ ] Initialize `CtxOS` repo skeleton (Python, Rust, CLI, UI) ✅
* [ ] Add Apache 2.0 LICENSE ✅
* [ ] Set up README.md with mission & module overview ✅
* [ ] Configure Python environment (Poetry / venv) ✅
* [ ] Configure Rust workspace for graph engine ✅
* [ ] Configure TS/React frontend scaffold ✅
* [ ] Add `.github/workflows` for CI/CD ✅
* [ ] Add Dockerfile placeholders for all modules ✅

---

## 1️⃣ Core Modules

* [x] Define context primitives (`Entity`, `Signal`, `Context`) ✅
* [x] Implement JSON/Protobuf schema versioning ✅
* [x] Build Python models for entities/signals/context ✅
* [x] Implement graph engine demo (`core/graph/graph_engine.py`) ✅
* [x] Implement scoring engine demo (`core/scoring/risk.py`) ✅
* [x] Add utils and helper functions (`core/utils/`) ✅
* [x] Add comprehensive unit tests ✅
* [x] Add architecture documentation ✅

---

## 2️⃣ Collectors Layer

* [ ] Implement `BaseCollector` interface ✅
* [ ] Implement `SubdomainCollector` demo ✅
* [ ] Implement `EmailCollector` demo ✅
* [ ] Add folder scaffolds for cloud, vuln collectors ✅
* [ ] Add tests for collectors ✅
* [ ] Implement YAML-driven collector configs (`configs/collectors.yml`) ✅

---

## 3️⃣ Normalizers Layer

* [x] Build deduplication & normalization engine ✅
* [x] Implement field mappers ✅
* [x] Add schema validators ✅
* [x] Add unit and integration tests ✅

---

## 4️⃣ Engines & Scoring

* [ ] Implement Risk Engine (demo version) ✅
* [ ] Implement Exposure Engine (scoring asset exposure)
* [ ] Implement Drift Engine (track changes over time)
* [ ] Create scoring utilities for confidence & risk
* [ ] Add engine configuration YAML (`configs/engines.yml`)

---

## 5️⃣ Agents & MCP

* [ ] Implement `BaseAgent` ✅
* [ ] Context Summarizer agent
* [ ] Gap Detector agent
* [ ] Hypothesis Generator agent
* [ ] Explainability agent
* [ ] Agent testing & audit logging
* [ ] Integrate agents with MCP server workflow

---

## 6️⃣ CLI

* [x] Create Python CLI skeleton ✅
* [x] Implement `collect`, `graph`, `risk`, `agent` commands ✅
* [x] Add global CLI options (`--project`, `--config`) ✅
* [x] Make CLI executable (`ctxos`) ✅
* [x] Add autocompletion support (bash/zsh/fish) ✅
* [x] Add CLI tests & demo workflows ✅

---

## 7️⃣ API Layer

* [ ] Implement REST / GraphQL server skeleton (`api/server/`)
* [ ] Add API schemas, controllers, middlewares
* [ ] Add auth & RBAC layer
* [ ] Integrate API with context graph & engines
* [ ] Add unit and integration tests

---

## 8️⃣ UI / Frontend

* [ ] Set up React/TS + Tailwind scaffold ✅
* [ ] Add pages: Dashboard, Graph Explorer, Risk Heatmap
* [ ] Add components: Nodes, Edges, Charts, Tables
* [ ] Add state management (`stores/`)
* [ ] Connect UI to API endpoints
* [ ] Add test harness (Jest / React Testing Library)
