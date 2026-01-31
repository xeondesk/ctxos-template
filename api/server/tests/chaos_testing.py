"""
Chaos testing for collector failure and graph corruption scenarios.
"""
import os
import sys
import time
import random
import threading
import asyncio
import json
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import unittest.mock
from contextlib import contextmanager
import sqlite3
import pickle

logger = logging.getLogger(__name__)


class ChaosScenario(str, Enum):
    """Types of chaos scenarios."""

    COLLECTOR_FAILURE = "collector_failure"
    NETWORK_PARTITION = "network_partition"
    DATA_CORRUPTION = "data_corruption"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_FULL = "disk_full"
    DATABASE_CORRUPTION = "database_corruption"
    PROCESS_CRASH = "process_crash"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class Severity(str, Enum):
    """Chaos scenario severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChaosConfig:
    """Configuration for chaos testing."""

    scenario: ChaosScenario
    severity: Severity
    duration_seconds: int = 30
    probability: float = 1.0
    target_components: List[str] = field(default_factory=list)
    recovery_time_seconds: int = 60
    metrics_collection: bool = True
    auto_recovery: bool = True


@dataclass
class ChaosResult:
    """Result of chaos test execution."""

    scenario: ChaosScenario
    success: bool
    duration_seconds: float
    error_count: int
    recovery_time_seconds: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    recovery_successful: bool = True
    system_impact: Dict[str, Any] = field(default_factory=dict)


class ChaosInjector:
    """Inject chaos into system components."""

    def __init__(self):
        self.active_injections = {}
        self.injection_lock = threading.Lock()

    def inject_collector_failure(
        self, collector_name: str, failure_type: str = "timeout"
    ) -> Dict[str, Any]:
        """Inject collector failure."""
        injection_id = f"collector_failure_{collector_name}_{int(time.time())}"

        logger.info(f"Injecting {failure_type} failure into collector {collector_name}")

        # Mock collector methods to fail
        if failure_type == "timeout":
            mock_method = unittest.mock.MagicMock(
                side_effect=asyncio.TimeoutError("Collector timeout")
            )
        elif failure_type == "connection_error":
            mock_method = unittest.mock.MagicMock(side_effect=ConnectionError("Connection failed"))
        elif failure_type == "data_error":
            mock_method = unittest.mock.MagicMock(side_effect=ValueError("Invalid data"))
        else:
            mock_method = unittest.mock.MagicMock(side_effect=Exception("Unknown error"))

        # Store injection info
        self.active_injections[injection_id] = {
            "type": "collector_failure",
            "target": collector_name,
            "failure_type": failure_type,
            "mock": mock_method,
            "start_time": time.time(),
        }

        return {
            "injection_id": injection_id,
            "collector": collector_name,
            "failure_type": failure_type,
            "status": "injected",
        }

    def inject_network_partition(self, affected_services: List[str]) -> Dict[str, Any]:
        """Inject network partition between services."""
        injection_id = f"network_partition_{int(time.time())}"

        logger.info(f"Injecting network partition affecting services: {affected_services}")

        # Mock network calls to fail
        def failing_network_call(*args, **kwargs):
            raise ConnectionError("Network partition active")

        mock_method = unittest.mock.MagicMock(side_effect=failing_network_call)

        self.active_injections[injection_id] = {
            "type": "network_partition",
            "affected_services": affected_services,
            "mock": mock_method,
            "start_time": time.time(),
        }

        return {
            "injection_id": injection_id,
            "affected_services": affected_services,
            "status": "injected",
        }

    def inject_data_corruption(
        self, data_source: str, corruption_type: str = "random"
    ) -> Dict[str, Any]:
        """Inject data corruption."""
        injection_id = f"data_corruption_{data_source}_{int(time.time())}"

        logger.info(f"Injecting {corruption_type} corruption into {data_source}")

        def corrupt_data(data):
            if isinstance(data, dict):
                # Corrupt random keys
                keys = list(data.keys())
                if keys:
                    corrupt_key = random.choice(keys)
                    if isinstance(data[corrupt_key], str):
                        data[corrupt_key] = "CORRUPTED_DATA"
                    elif isinstance(data[corrupt_key], (int, float)):
                        data[corrupt_key] = random.randint(-999999, 999999)
            elif isinstance(data, list):
                # Corrupt random list items
                if data:
                    corrupt_index = random.randint(0, len(data) - 1)
                    data[corrupt_index] = "CORRUPTED_ITEM"
            return data

        self.active_injections[injection_id] = {
            "type": "data_corruption",
            "target": data_source,
            "corruption_type": corruption_type,
            "corrupt_function": corrupt_data,
            "start_time": time.time(),
        }

        return {
            "injection_id": injection_id,
            "data_source": data_source,
            "corruption_type": corruption_type,
            "status": "injected",
        }

    def inject_memory_pressure(self, memory_mb: int) -> Dict[str, Any]:
        """Inject memory pressure."""
        injection_id = f"memory_pressure_{int(time.time())}"

        logger.info(f"Injecting {memory_mb}MB memory pressure")

        # Allocate memory to create pressure
        memory_blocks = []

        def allocate_memory():
            try:
                # Allocate memory in chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                for _ in range(memory_mb):
                    block = bytearray(chunk_size)
                    memory_blocks.append(block)
                    # Fill with random data to ensure it's actually allocated
                    for i in range(0, chunk_size, 1024):
                        block[i] = random.randint(0, 255)
            except MemoryError:
                logger.warning("Memory allocation failed - system under pressure")

        allocate_memory()

        self.active_injections[injection_id] = {
            "type": "memory_pressure",
            "memory_mb": memory_mb,
            "memory_blocks": memory_blocks,
            "start_time": time.time(),
        }

        return {"injection_id": injection_id, "memory_mb": memory_mb, "status": "injected"}

    def inject_disk_full(self, target_path: str, size_mb: int) -> Dict[str, Any]:
        """Inject disk full scenario."""
        injection_id = f"disk_full_{int(time.time())}"

        logger.info(f"Injecting disk full scenario at {target_path} with {size_mb}MB")

        # Create temporary files to fill disk
        temp_files = []

        try:
            target_dir = Path(target_path)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Create files to fill space
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(size_mb):
                temp_file = target_dir / f"chaos_file_{i}.tmp"
                with open(temp_file, "wb") as f:
                    # Write 1MB of random data
                    data = os.urandom(chunk_size)
                    f.write(data)
                temp_files.append(temp_file)

        except Exception as e:
            logger.error(f"Failed to create disk full scenario: {e}")

        self.active_injections[injection_id] = {
            "type": "disk_full",
            "target_path": target_path,
            "size_mb": size_mb,
            "temp_files": temp_files,
            "start_time": time.time(),
        }

        return {
            "injection_id": injection_id,
            "target_path": target_path,
            "size_mb": size_mb,
            "status": "injected",
        }

    def inject_database_corruption(self, db_path: str) -> Dict[str, Any]:
        """Inject database corruption."""
        injection_id = f"db_corruption_{int(time.time())}"

        logger.info(f"Injecting database corruption at {db_path}")

        # Backup original database
        backup_path = f"{db_path}.backup_{int(time.time())}"
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)

        try:
            # Corrupt the database file
            with open(db_path, "r+b") as f:
                # Seek to random position and write garbage data
                file_size = os.path.getsize(db_path)
                if file_size > 1024:
                    corrupt_pos = random.randint(1024, file_size - 1024)
                    f.seek(corrupt_pos)
                    f.write(b"CORRUPTED_DATA_CHAOS_TEST")
        except Exception as e:
            logger.error(f"Failed to corrupt database: {e}")

        self.active_injections[injection_id] = {
            "type": "database_corruption",
            "db_path": db_path,
            "backup_path": backup_path,
            "start_time": time.time(),
        }

        return {
            "injection_id": injection_id,
            "db_path": db_path,
            "backup_path": backup_path,
            "status": "injected",
        }

    def recover_injection(self, injection_id: str) -> bool:
        """Recover from chaos injection."""
        with self.injection_lock:
            if injection_id not in self.active_injections:
                logger.warning(f"Injection {injection_id} not found")
                return False

            injection = self.active_injections[injection_id]
            injection_type = injection["type"]

            logger.info(f"Recovering from injection {injection_id} ({injection_type})")

            try:
                if injection_type == "memory_pressure":
                    # Release memory blocks
                    injection["memory_blocks"].clear()

                elif injection_type == "disk_full":
                    # Remove temporary files
                    for temp_file in injection["temp_files"]:
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass
                    # Remove directory if empty
                    target_dir = Path(injection["target_path"])
                    try:
                        target_dir.rmdir()
                    except Exception:
                        pass

                elif injection_type == "database_corruption":
                    # Restore from backup
                    backup_path = injection["backup_path"]
                    db_path = injection["db_path"]
                    if os.path.exists(backup_path):
                        shutil.move(backup_path, db_path)

                # Remove injection
                del self.active_injections[injection_id]

                logger.info(f"Successfully recovered from injection {injection_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to recover from injection {injection_id}: {e}")
                return False

    def cleanup_all_injections(self):
        """Clean up all active injections."""
        with self.injection_lock:
            injection_ids = list(self.active_injections.keys())

            for injection_id in injection_ids:
                self.recover_injection(injection_id)

            logger.info("Cleaned up all chaos injections")


class SystemMonitor:
    """Monitor system metrics during chaos tests."""

    def __init__(self):
        self.metrics_history = []
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start system monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("Started system monitoring")

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Stopped system monitoring")

    def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        try:
            import psutil

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_free_mb = disk.free / (1024 * 1024)

            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv

            # Process metrics
            process_count = len(psutil.pids())

            return {
                "timestamp": time.time(),
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory_percent,
                "memory_available_mb": memory_available_mb,
                "disk_percent": disk_percent,
                "disk_free_mb": disk_free_mb,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv,
                "process_count": process_count,
            }

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self.metrics_history:
            return {}

        # Calculate averages and extremes
        cpu_values = [m.get("cpu_percent", 0) for m in self.metrics_history if "cpu_percent" in m]
        memory_values = [
            m.get("memory_percent", 0) for m in self.metrics_history if "memory_percent" in m
        ]
        disk_values = [
            m.get("disk_percent", 0) for m in self.metrics_history if "disk_percent" in m
        ]

        return {
            "total_samples": len(self.metrics_history),
            "duration_seconds": self.metrics_history[-1]["timestamp"]
            - self.metrics_history[0]["timestamp"]
            if self.metrics_history
            else 0,
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
            },
            "disk": {
                "avg": sum(disk_values) / len(disk_values) if disk_values else 0,
                "max": max(disk_values) if disk_values else 0,
                "min": min(disk_values) if disk_values else 0,
            },
        }


class ChaosTester:
    """Main chaos testing orchestrator."""

    def __init__(self):
        self.injector = ChaosInjector()
        self.monitor = SystemMonitor()
        self.test_results = []

    def run_chaos_test(
        self, config: ChaosConfig, test_function: Optional[Callable] = None
    ) -> ChaosResult:
        """Run a chaos test with the given configuration."""
        logger.info(f"Starting chaos test: {config.scenario} ({config.severity})")

        start_time = time.time()
        error_count = 0
        logs = []

        # Start monitoring
        self.monitor.start_monitoring()

        try:
            # Inject chaos
            injection_result = self._inject_chaos(config)
            injection_id = injection_result["injection_id"]

            logs.append(f"Injected chaos: {injection_result}")

            # Wait for specified duration or run test function
            if test_function:
                try:
                    test_function()
                    logs.append("Test function completed successfully")
                except Exception as e:
                    error_count += 1
                    logs.append(f"Test function failed: {e}")
                    logger.error(f"Test function failed during chaos: {e}")
            else:
                # Just wait for the duration
                time.sleep(config.duration_seconds)
                logs.append(f"Chaos injection active for {config.duration_seconds} seconds")

            # Check system impact
            system_impact = self._assess_system_impact()

            # Recover from chaos
            recovery_start = time.time()
            recovery_successful = self.injector.recover_injection(injection_id)
            recovery_time = time.time() - recovery_start

            if recovery_successful:
                logs.append(f"Successfully recovered in {recovery_time:.2f} seconds")
            else:
                logs.append("Failed to recover from chaos injection")
                error_count += 1

            # Wait for recovery period
            if config.auto_recovery and recovery_successful:
                time.sleep(config.recovery_time_seconds)
                logs.append(f"Recovery period completed: {config.recovery_time_seconds} seconds")

        except Exception as e:
            error_count += 1
            logs.append(f"Chaos test failed: {e}")
            logger.error(f"Chaos test failed: {e}")

        finally:
            # Stop monitoring
            self.monitor.stop_monitoring()

            # Get metrics
            metrics = self.monitor.get_metrics_summary()

            # Calculate total duration
            total_duration = time.time() - start_time

        # Create result
        result = ChaosResult(
            scenario=config.scenario,
            success=error_count == 0,
            duration_seconds=total_duration,
            error_count=error_count,
            recovery_time_seconds=recovery_time if "recovery_time" in locals() else 0,
            metrics=metrics,
            logs=logs,
            recovery_successful=recovery_successful if "recovery_successful" in locals() else False,
            system_impact=system_impact if "system_impact" in locals() else {},
        )

        self.test_results.append(result)

        logger.info(
            f"Chaos test completed: {config.scenario} - {'SUCCESS' if result.success else 'FAILED'}"
        )

        return result

    def _inject_chaos(self, config: ChaosConfig) -> Dict[str, Any]:
        """Inject chaos based on configuration."""
        if config.scenario == ChaosScenario.COLLECTOR_FAILURE:
            target = (
                config.target_components[0] if config.target_components else "default_collector"
            )
            failure_type = random.choice(["timeout", "connection_error", "data_error"])
            return self.injector.inject_collector_failure(target, failure_type)

        elif config.scenario == ChaosScenario.NETWORK_PARTITION:
            affected = config.target_components if config.target_components else ["api", "database"]
            return self.injector.inject_network_partition(affected)

        elif config.scenario == ChaosScenario.DATA_CORRUPTION:
            target = (
                config.target_components[0] if config.target_components else "default_data_source"
            )
            corruption_type = random.choice(["random", "nullify", "invert"])
            return self.injector.inject_data_corruption(target, corruption_type)

        elif config.scenario == ChaosScenario.MEMORY_PRESSURE:
            memory_mb = (
                512
                if config.severity == Severity.HIGH
                else 256
                if config.severity == Severity.MEDIUM
                else 128
            )
            return self.injector.inject_memory_pressure(memory_mb)

        elif config.scenario == ChaosScenario.DISK_FULL:
            size_mb = (
                1024
                if config.severity == Severity.HIGH
                else 512
                if config.severity == Severity.MEDIUM
                else 256
            )
            target_path = tempfile.mkdtemp(prefix="chaos_disk_")
            return self.injector.inject_disk_full(target_path, size_mb)

        elif config.scenario == ChaosScenario.DATABASE_CORRUPTION:
            # Create a test database
            db_path = tempfile.mktemp(suffix=".db")
            self._create_test_database(db_path)
            return self.injector.inject_database_corruption(db_path)

        else:
            raise ValueError(f"Unsupported chaos scenario: {config.scenario}")

    def _create_test_database(self, db_path: str):
        """Create a test database for corruption testing."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create test tables
        cursor.execute(
            """
            CREATE TABLE test_entities (
                id INTEGER PRIMARY KEY,
                name TEXT,
                data BLOB,
                created_at TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE test_signals (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER,
                signal_type TEXT,
                value REAL,
                timestamp TIMESTAMP
            )
        """
        )

        # Insert test data
        cursor.execute(
            "INSERT INTO test_entities (name, data, created_at) VALUES (?, ?, ?)",
            ("test_entity", b"test_data", datetime.now()),
        )

        cursor.execute(
            "INSERT INTO test_signals (entity_id, signal_type, value, timestamp) VALUES (?, ?, ?, ?)",
            (1, "test_signal", 42.0, datetime.now()),
        )

        conn.commit()
        conn.close()

    def _assess_system_impact(self) -> Dict[str, Any]:
        """Assess the impact of chaos on the system."""
        metrics = self.monitor.metrics_history

        if not metrics:
            return {}

        # Compare before and after metrics
        if len(metrics) < 2:
            return {}

        before_metrics = metrics[0]
        after_metrics = metrics[-1]

        impact = {}

        # CPU impact
        if "cpu_percent" in before_metrics and "cpu_percent" in after_metrics:
            cpu_change = after_metrics["cpu_percent"] - before_metrics["cpu_percent"]
            impact["cpu_change_percent"] = cpu_change

        # Memory impact
        if "memory_percent" in before_metrics and "memory_percent" in after_metrics:
            memory_change = after_metrics["memory_percent"] - before_metrics["memory_percent"]
            impact["memory_change_percent"] = memory_change

        # Disk impact
        if "disk_percent" in before_metrics and "disk_percent" in after_metrics:
            disk_change = after_metrics["disk_percent"] - before_metrics["disk_percent"]
            impact["disk_change_percent"] = disk_change

        # Overall impact score
        impact_score = 0
        if "cpu_change_percent" in impact:
            impact_score += abs(impact["cpu_change_percent"])
        if "memory_change_percent" in impact:
            impact_score += abs(impact["memory_change_percent"])
        if "disk_change_percent" in impact:
            impact_score += abs(impact["disk_change_percent"])

        impact["overall_impact_score"] = impact_score

        return impact

    def run_test_suite(self, test_configs: List[ChaosConfig]) -> List[ChaosResult]:
        """Run a suite of chaos tests."""
        results = []

        for config in test_configs:
            # Random probability check
            if random.random() > config.probability:
                logger.info(f"Skipping chaos test {config.scenario} due to probability")
                continue

            result = self.run_chaos_test(config)
            results.append(result)

            # Wait between tests
            time.sleep(5)

        return results

    def generate_report(self, results: Optional[List[ChaosResult]] = None) -> Dict[str, Any]:
        """Generate chaos testing report."""
        results = results or self.test_results

        if not results:
            return {"message": "No test results available"}

        # Calculate statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests

        # Scenario statistics
        scenario_stats = {}
        for result in results:
            scenario = result.scenario
            if scenario not in scenario_stats:
                scenario_stats[scenario] = {"total": 0, "success": 0, "failed": 0}

            scenario_stats[scenario]["total"] += 1
            if result.success:
                scenario_stats[scenario]["success"] += 1
            else:
                scenario_stats[scenario]["failed"] += 1

        # Average metrics
        avg_duration = sum(r.duration_seconds for r in results) / total_tests
        avg_recovery_time = sum(r.recovery_time_seconds for r in results) / total_tests
        total_errors = sum(r.error_count for r in results)

        # System impact summary
        all_impacts = [r.system_impact for r in results if r.system_impact]
        avg_impact_score = (
            sum(imp.get("overall_impact_score", 0) for imp in all_impacts) / len(all_impacts)
            if all_impacts
            else 0
        )

        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests / total_tests * 100,
                "total_errors": total_errors,
            },
            "averages": {
                "duration_seconds": avg_duration,
                "recovery_time_seconds": avg_recovery_time,
                "impact_score": avg_impact_score,
            },
            "scenario_breakdown": scenario_stats,
            "detailed_results": [
                {
                    "scenario": r.scenario,
                    "success": r.success,
                    "duration": r.duration_seconds,
                    "errors": r.error_count,
                    "recovery_time": r.recovery_time_seconds,
                    "recovery_successful": r.recovery_successful,
                    "impact_score": r.system_impact.get("overall_impact_score", 0),
                }
                for r in results
            ],
        }

    def cleanup(self):
        """Clean up all chaos testing resources."""
        self.injector.cleanup_all_injections()
        self.monitor.stop_monitoring()
        logger.info("Chaos testing cleanup completed")


# Global chaos tester instance
chaos_tester = ChaosTester()
