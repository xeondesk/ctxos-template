#!/usr/bin/env python3
"""
CtxOS Performance Benchmark Runner
---------------------------------
Adaptive, schema-safe benchmarking harness for CtxOS core systems.
"""

import sys
import time
import json
import inspect
import statistics
from pathlib import Path
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime

# -------------------------------------------------------------------
# Project setup
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.models import (
    Entity, EntityType, EntitySeverity,
    Signal, SignalType, SignalSeverity, SignalConfidence,
    Context
)
from engines.risk.risk_engine import RiskEngine, RiskFactors

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def adaptive_construct(cls, **candidates):
    """
    Safely construct an object by matching only supported __init__ args.
    """
    sig = inspect.signature(cls.__init__)
    kwargs = {
        name: value
        for name, value in candidates.items()
        if name in sig.parameters
    }
    return cls(**kwargs)

# -------------------------------------------------------------------
# Benchmark result model
# -------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    name: str
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float

# -------------------------------------------------------------------
# Benchmark runner
# -------------------------------------------------------------------

class BenchmarkRunner:
    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_benchmark(
        self,
        name: str,
        operation: Callable[..., Any],
        iterations: int = 1000
    ) -> BenchmarkResult:
        print(f"🏃 Running: {name} ({iterations} iterations)")

        # Warmup
        for _ in range(min(10, iterations // 10)):
            operation()

        times: List[float] = []

        for _ in range(iterations):
            start = time.perf_counter()
            operation()
            end = time.perf_counter()
            times.append(end - start)

        total = sum(times)
        avg = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0.0

        result = BenchmarkResult(
            name=name,
            operation=operation.__name__,
            iterations=iterations,
            total_time=total,
            avg_time=avg,
            min_time=min(times),
            max_time=max(times),
            std_dev=std,
            throughput=iterations / total if total > 0 else float("inf"),
        )

        self.results.append(result)
        print(f"  ✅ Avg: {avg * 1000:.3f}ms, Throughput: {result.throughput:.1f} ops/sec")
        return result

    def generate_report(self, path: str) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "benchmarks": len(self.results),
                "iterations": sum(r.iterations for r in self.results),
                "total_time_sec": sum(r.total_time for r in self.results),
            },
            "results": [
                {
                    "name": r.name,
                    "avg_ms": r.avg_time * 1000,
                    "min_ms": r.min_time * 1000,
                    "max_ms": r.max_time * 1000,
                    "std_ms": r.std_dev * 1000,
                    "throughput_ops_sec": r.throughput,
                }
                for r in self.results
            ],
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(report, f, indent=2)

        return report

# -------------------------------------------------------------------
# Benchmark operations (SCHEMA SAFE)
# -------------------------------------------------------------------

def create_entity() -> Entity:
    return adaptive_construct(
        Entity,
        name="test-entity.com",
        entity_type=EntityType.DOMAIN,
        source="benchmark",
        severity=EntitySeverity.MEDIUM,
        confidence=0.8,
        data={}
    )

def create_signal() -> Signal:
    return adaptive_construct(
        Signal,
        signal_type=SignalType.VULNERABILITY,
        severity=SignalSeverity.HIGH,
        confidence=SignalConfidence.HIGH,
        source="benchmark",
        data={
            "cve": "CVE-2023-1234",
            "exploit": False
        }
    )

def create_context() -> Context:
    entities = [create_entity() for _ in range(10)]
    signals = [create_signal() for _ in range(5)]
    return adaptive_construct(
        Context,
        name="benchmark-context",
        entities=entities,
        signals=signals
    )

def calculate_risk_score() -> float:
    engine = RiskEngine()
    factors = RiskFactors(
        vulnerability_count=5,
        open_ports=10,
        exposed_credentials=2,
        suspicious_activity=3,
        data_breach_mentions=1,
        malware_indicators=1,
        certificate_issues=0,
        configuration_issues=4,
        age_days=100,
        last_seen_days=5,
    )
    return engine._calculate_risk_score(factors)

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    print("🚀 CtxOS Performance Benchmarks")
    print("=" * 50)

    runner = BenchmarkRunner()

    print("\n📊 Core Operations")
    runner.run_benchmark("Entity Creation", create_entity, 1000)
    runner.run_benchmark("Signal Creation", create_signal, 1000)
    runner.run_benchmark("Context Creation", create_context, 100)

    print("\n📊 Risk Assessment")
    runner.run_benchmark("Risk Score Calculation", calculate_risk_score, 1000)

    report_path = "benchmarks/results.json"
    report = runner.generate_report(report_path)

    print("\n🏁 Summary")
    print(f"Benchmarks: {report['summary']['benchmarks']}")
    print(f"Iterations: {report['summary']['iterations']:,}")
    print(f"Total time: {report['summary']['total_time_sec']:.3f}s")
    print(f"📁 Results saved to: {report_path}")

if __name__ == "__main__":
    main()
