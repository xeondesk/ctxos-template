# CtxOS Performance Benchmarks

This directory contains performance benchmarking tools and results for the CtxOS platform.

## Overview

The benchmark suite measures performance across key components:

- **Core Operations**: Entity, Signal, and Context creation/manipulation
- **Risk Assessment**: Risk scoring and calculation performance
- **Graph Operations**: Node/edge operations and path finding
- **API Performance**: Response times and throughput
- **Database Operations**: Query performance and indexing effectiveness

## Running Benchmarks

### Quick Start

```bash
# Run all benchmarks
python benchmarks/benchmark_runner.py

# Run with custom iterations
python benchmarks/benchmark_runner.py --iterations 5000
```

### Individual Benchmark Categories

```bash
# Core operations only
python benchmarks/core_benchmarks.py

# Risk engine benchmarks
python benchmarks/risk_benchmarks.py

# Graph engine benchmarks
python benchmarks/graph_benchmarks.py

# API benchmarks
python benchmarks/api_benchmarks.py
```

## Benchmark Files

- `benchmark_runner.py` - Main benchmark runner
- `core_benchmarks.py` - Core module benchmarks
- `risk_benchmarks.py` - Risk engine benchmarks
- `graph_benchmarks.py` - Graph engine benchmarks
- `api_benchmarks.py` - API performance benchmarks
- `results/` - Benchmark results and reports
- `README.md` - This file

## Understanding Results

### Key Metrics

- **Average Time**: Mean execution time per operation
- **Min/Max Time**: Fastest and slowest execution times
- **Standard Deviation**: Performance consistency
- **Throughput**: Operations per second
- **Percentiles**: 50th, 95th, 99th percentile performance

### Performance Targets

| Operation | Target Avg Time | Target Throughput |
|-----------|-----------------|-------------------|
| Entity Creation | < 1ms | > 1000 ops/sec |
| Signal Creation | < 1ms | > 1000 ops/sec |
| Context Creation | < 10ms | > 100 ops/sec |
| Risk Score Calculation | < 5ms | > 200 ops/sec |
| Graph Query | < 50ms | > 20 ops/sec |

## Benchmark Reports

Results are saved in JSON format with detailed metrics:

```json
{
  "timestamp": "2023-12-01T10:00:00",
  "summary": {
    "total_benchmarks": 10,
    "total_iterations": 10000,
    "total_time": 15.234
  },
  "benchmarks": [
    {
      "name": "Entity Creation",
      "avg_time_ms": 0.856,
      "throughput_ops_per_sec": 1168.2
    }
  ]
}
```

## Performance Optimization

### Common Bottlenecks

1. **Database Queries**: Missing indexes, N+1 queries
2. **Memory Allocation**: Excessive object creation
3. **I/O Operations**: File system, network calls
4. **Algorithm Complexity**: Inefficient data structures

### Optimization Strategies

1. **Database Optimization**
   - Add appropriate indexes
   - Use connection pooling
   - Implement query caching

2. **Memory Management**
   - Object pooling for frequently created objects
   - Lazy loading where appropriate
   - Memory profiling with `memory_profiler`

3. **Algorithm Improvements**
   - Use more efficient data structures
   - Implement caching mechanisms
   - Parallelize independent operations

## Continuous Benchmarking

### CI/CD Integration

Add benchmarks to your CI pipeline:

```yaml
# .github/workflows/benchmarks.yml
- name: Run Benchmarks
  run: python benchmarks/benchmark_runner.py
  
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-results
    path: benchmarks/results/
```

### Performance Regression Detection

Set up alerts for performance regressions:

```python
# In benchmark_runner.py
def check_performance_regression(current_results, baseline_results):
    for current, baseline in zip(current_results, baseline_results):
        if current.avg_time > baseline.avg_time * 1.2:  # 20% regression
            print(f"⚠️ Performance regression detected in {current.name}")
```

## Profiling Tools

### CPU Profiling

```bash
# Profile specific operations
python -m cProfile -o profile.stats benchmarks/benchmark_runner.py

# Analyze results
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
python -m memory_profiler benchmarks/benchmark_runner.py
```

## Custom Benchmarks

### Adding New Benchmarks

1. Create a new benchmark function:

```python
def custom_operation():
    # Your operation here
    return result
```

2. Add to benchmark runner:

```python
runner.run_benchmark("Custom Operation", custom_operation, 1000)
```

### Benchmark Categories

Organize benchmarks by category:

```python
# Core benchmarks
runner.run_benchmark("Entity Creation", create_entity, 1000)
runner.run_benchmark("Signal Creation", create_signal, 1000)

# Risk benchmarks  
runner.run_benchmark("Risk Assessment", calculate_risk, 500)

# Graph benchmarks
runner.run_benchmark("Graph Query", graph_query, 100)
```

## Environment Setup

### Benchmark Environment

For consistent results:

1. Use dedicated hardware
2. Disable unnecessary services
3. Use consistent Python version
4. Clear caches before running

### System Monitoring

Monitor system resources during benchmarks:

```bash
# CPU and memory usage
htop

# Disk I/O
iotop

# Network activity
iftop
```

## Troubleshooting

### Common Issues

1. **Inconsistent Results**
   - Check for background processes
   - Ensure consistent system state
   - Run multiple iterations

2. **Memory Errors**
   - Reduce batch sizes
   - Check for memory leaks
   - Monitor memory usage

3. **Slow Performance**
   - Profile with cProfile
   - Check database queries
   - Verify indexes

### Debug Mode

Run benchmarks with debug information:

```bash
DEBUG=1 python benchmarks/benchmark_runner.py
```

## Contributing

When adding benchmarks:

1. Follow existing naming conventions
2. Include performance targets
3. Add documentation for new benchmarks
4. Update this README

## Results Archive

Historical benchmark results are stored in `results/archive/`:

```
results/
├── archive/
│   ├── 2023-12-01_results.json
│   ├── 2023-12-02_results.json
│   └── ...
├── latest.json
└── trends.json
```

Use the archive to track performance trends over time.
