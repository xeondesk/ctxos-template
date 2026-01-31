#!/usr/bin/env python3
"""
Performance Benchmark Runner for CtxOS
"""

import sys
import os
import time
import statistics
import json
from pathlib import Path
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import Entity, EntityType, EntitySeverity, Signal, SignalType, SignalSeverity, SignalConfidence, Context
from engines.risk.risk_engine import RiskEngine, RiskFactors


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


class BenchmarkRunner:
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def run_benchmark(self, name: str, operation: Callable, iterations: int = 1000, **kwargs) -> BenchmarkResult:
        print(f"🏃 Running: {name} ({iterations} iterations)")
        
        times = []
        
        # Warm up
        for _ in range(min(10, iterations // 10)):
            operation(**kwargs)
        
        # Benchmark
        for _ in range(iterations):
            start_time = time.perf_counter()
            operation(**kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        result = BenchmarkResult(
            name=name,
            operation=operation.__name__,
            iterations=iterations,
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            throughput=iterations / sum(times)
        )
        
        self.results.append(result)
        print(f"  ✅ Avg: {result.avg_time*1000:.3f}ms, Throughput: {result.throughput:.1f} ops/sec")
        return result
    
    def generate_report(self, output_file: str = None) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": len(self.results),
                "total_iterations": sum(r.iterations for r in self.results),
                "total_time": sum(r.total_time for r in self.results)
            },
            "benchmarks": []
        }
        
        for result in self.results:
            report["benchmarks"].append({
                "name": result.name,
                "avg_time_ms": result.avg_time * 1000,
                "throughput_ops_per_sec": result.throughput
            })
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report


# Benchmark operations
def create_entity():
    return Entity(
        name="test-entity.com",
        entity_type=EntityType.DOMAIN,
        source="benchmark",
        severity=EntitySeverity.MEDIUM,
        confidence=0.8
    )


def create_signal():
    return Signal(
        signal_type=SignalType.VULNERABILITY,
        severity=SignalSeverity.HIGH,
        confidence=SignalConfidence.HIGH,
        properties={"cve": "CVE-2023-1234"}
    )


def create_context():
    entities = [create_entity() for _ in range(10)]
    signals = [create_signal() for _ in range(5)]
    return Context(name="benchmark-context", entities=entities, signals=signals)


def calculate_risk_score():
    risk_engine = RiskEngine()
    factors = RiskFactors(
        vulnerability_count=5, open_ports=10, exposed_credentials=2,
        suspicious_activity=3, data_breach_mentions=1, malware_indicators=1,
        certificate_issues=0, configuration_issues=4, age_days=100, last_seen_days=5
    )
    return risk_engine._calculate_risk_score(factors)


def main():
    print("🚀 CtxOS Performance Benchmarks")
    print("=" * 50)
    
    runner = BenchmarkRunner()
    
    # Core operations
    print("\n📊 Core Operations")
    runner.run_benchmark("Entity Creation", create_entity, 1000)
    runner.run_benchmark("Signal Creation", create_signal, 1000)
    runner.run_benchmark("Context Creation", create_context, 100)
    
    # Risk assessment
    print("\n📊 Risk Assessment")
    runner.run_benchmark("Risk Score Calculation", calculate_risk_score, 1000)
    
    # Generate report
    report = runner.generate_report("benchmarks/results.json")
    
    print(f"\n🏁 Summary")
    print(f"Total benchmarks: {report['summary']['total_benchmarks']}")
    print(f"Total iterations: {report['summary']['total_iterations']:,}")
    print(f"Total time: {report['summary']['total_time']:.3f}s")
    
    print(f"\n📊 Results saved to: benchmarks/results.json")


if __name__ == "__main__":
    main()
