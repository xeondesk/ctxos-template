"""
Memory isolation and sandboxing for secure execution.
"""
import os
import sys
import resource
import signal
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from contextlib import contextmanager
import psutil
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IsolationType(str, Enum):
    """Types of isolation mechanisms."""

    PROCESS = "process"
    CONTAINER = "container"
    VM = "vm"
    CHROOT = "chroot"
    NAMESPACE = "namespace"


class SecurityLevel(str, Enum):
    """Security levels for isolation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class ResourceLimits:
    """Resource limits for isolated execution."""

    max_memory_mb: int = 512
    max_cpu_time_seconds: int = 30
    max_processes: int = 10
    max_file_size_mb: int = 100
    max_open_files: int = 50
    max_network_connections: int = 5


@dataclass
class IsolationConfig:
    """Configuration for isolation environment."""

    isolation_type: IsolationType = IsolationType.PROCESS
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    resource_limits: ResourceLimits = ResourceLimits()
    allowed_paths: List[str] = None
    blocked_paths: List[str] = None
    environment_variables: Dict[str, str] = None
    network_access: bool = False
    temp_dir_size_mb: int = 100

    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = []
        if self.blocked_paths is None:
            self.blocked_paths = ["/etc", "/var", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc"]
        if self.environment_variables is None:
            self.environment_variables = {}


class MemoryIsolationError(Exception):
    """Custom exception for memory isolation errors."""

    pass


class ProcessIsolator:
    """Process-based isolation using resource limits and chroot."""

    def __init__(self, config: IsolationConfig):
        self.config = config
        self.temp_dir = None
        self.process = None

    @contextmanager
    def isolated_environment(self):
        """Create an isolated environment for execution."""
        self.temp_dir = tempfile.mkdtemp(prefix="ctxos_isolated_")

        try:
            # Setup isolated environment
            self._setup_chroot()
            self._setup_resource_limits()

            yield self.temp_dir

        finally:
            self._cleanup()

    def _setup_chroot(self):
        """Setup chroot jail if available."""
        if os.getuid() != 0:
            logger.warning("Not running as root, skipping chroot setup")
            return

        try:
            # Create minimal filesystem structure
            jail_path = Path(self.temp_dir) / "jail"
            jail_path.mkdir(exist_ok=True)

            # Create essential directories
            (jail_path / "tmp").mkdir(exist_ok=True)
            (jail_path / "dev").mkdir(exist_ok=True)

            # Create essential device nodes
            (jail_path / "dev" / "null").mknod(mode=0o666, device=os.makedev(1, 3))
            (jail_path / "dev" / "zero").mknod(mode=0o666, device=os.makedev(1, 5))
            (jail_path / "dev" / "random").mknod(mode=0o666, device=os.makedev(1, 8))

            # Copy necessary binaries
            for binary in ["/bin/sh", "/bin/bash", "/usr/bin/python3"]:
                if os.path.exists(binary):
                    dest = jail_path / binary.lstrip("/")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(binary, dest)

            logger.info(f"Chroot jail setup at {jail_path}")

        except Exception as e:
            logger.error(f"Failed to setup chroot: {e}")
            raise MemoryIsolationError(f"Chroot setup failed: {e}")

    def _setup_resource_limits(self):
        """Setup resource limits for the process."""
        limits = self.config.resource_limits

        try:
            # Memory limit
            resource.setrlimit(
                resource.RLIMIT_AS,
                (limits.max_memory_mb * 1024 * 1024, limits.max_memory_mb * 1024 * 1024),
            )

            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU, (limits.max_cpu_time_seconds, limits.max_cpu_time_seconds)
            )

            # Process limit
            resource.setrlimit(resource.RLIMIT_NPROC, (limits.max_processes, limits.max_processes))

            # File size limit
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (limits.max_file_size_mb * 1024 * 1024, limits.max_file_size_mb * 1024 * 1024),
            )

            # Open files limit
            resource.setrlimit(
                resource.RLIMIT_NOFILE, (limits.max_open_files, limits.max_open_files)
            )

            logger.info("Resource limits applied")

        except Exception as e:
            logger.error(f"Failed to set resource limits: {e}")
            raise MemoryIsolationError(f"Resource limit setup failed: {e}")

    def execute_isolated(
        self, command: List[str], input_data: Optional[bytes] = None, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute command in isolated environment."""
        timeout = timeout or self.config.resource_limits.max_cpu_time_seconds

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.environment_variables)

            # Remove sensitive environment variables
            sensitive_vars = ["PATH", "LD_LIBRARY_PATH", "PYTHONPATH"]
            for var in sensitive_vars:
                if var not in self.config.environment_variables:
                    env.pop(var, None)

            # Execute process
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.temp_dir,
                preexec_fn=self._setup_child_process,
            )

            self.process = process

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                return_code = process.returncode

                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": return_code,
                    "success": return_code == 0,
                    "timeout": False,
                }

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

                return {
                    "stdout": b"",
                    "stderr": b"Process timed out",
                    "return_code": -1,
                    "success": False,
                    "timeout": True,
                }

        except Exception as e:
            logger.error(f"Isolated execution failed: {e}")
            return {
                "stdout": b"",
                "stderr": str(e).encode(),
                "return_code": -1,
                "success": False,
                "timeout": False,
                "error": str(e),
            }

    def _setup_child_process(self):
        """Setup child process for isolation."""
        # Set resource limits for child
        self._setup_resource_limits()

        # Change to temporary directory
        os.chdir(self.temp_dir)

        # Set process group
        os.setsid()

        # Drop privileges if running as root
        if os.getuid() == 0:
            try:
                # Switch to nobody user
                os.setgid(65534)  # nobody group
                os.setuid(65534)  # nobody user
            except OSError:
                logger.warning("Failed to drop privileges")

    def _cleanup(self):
        """Clean up isolated environment."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.error(f"Failed to cleanup temp directory: {e}")


class ContainerIsolator:
    """Container-based isolation using Docker or similar."""

    def __init__(self, config: IsolationConfig):
        self.config = config
        self.container_id = None

    def execute_isolated(
        self, command: List[str], input_data: Optional[bytes] = None, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute command in isolated container."""
        try:
            # Check if Docker is available
            subprocess.run(["docker", "--version"], check=True, capture_output=True)

            # Create Docker command
            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "--memory",
                f"{self.config.resource_limits.max_memory_mb}m",
                "--cpus",
                "1",
                "--pids-limit",
                str(self.config.resource_limits.max_processes),
                "--network",
                "none" if not self.config.network_access else "bridge",
                "--read-only",
                "--tmpfs",
                "/tmp:noexec,nosuid,size=100m",
                "--drop-all",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
            ]

            # Add volume mounts for allowed paths
            for path in self.config.allowed_paths:
                docker_cmd.extend(["-v", f"{path}:{path}:ro"])

            # Add environment variables
            for key, value in self.config.environment_variables.items():
                docker_cmd.extend(["-e", f"{key}={value}"])

            # Add the command
            docker_cmd.extend(["ubuntu:20.04"] + command)

            # Execute
            process = subprocess.Popen(
                docker_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate(input=input_data, timeout=timeout)

            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "success": process.returncode == 0,
                "timeout": False,
            }

        except subprocess.CalledProcessError:
            return {
                "stdout": b"",
                "stderr": b"Docker not available",
                "return_code": -1,
                "success": False,
                "timeout": False,
            }
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return {
                "stdout": b"",
                "stderr": str(e).encode(),
                "return_code": -1,
                "success": False,
                "timeout": False,
                "error": str(e),
            }


class PythonSandbox:
    """Python code execution sandbox."""

    def __init__(self, config: IsolationConfig):
        self.config = config
        self.process_isolator = ProcessIsolator(config)

    def execute_python_code(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute Python code in sandbox."""
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            script_path = f.name

        try:
            # Execute in isolated environment
            with self.process_isolator.isolated_environment():
                result = self.process_isolator.execute_isolated(
                    ["python3", script_path], timeout=timeout
                )

            return result

        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except OSError:
                pass


class MemoryMonitor:
    """Monitor memory usage of processes."""

    def __init__(self):
        self.processes = {}

    def start_monitoring(self, pid: int, max_memory_mb: int):
        """Start monitoring a process."""
        try:
            process = psutil.Process(pid)
            self.processes[pid] = {
                "process": process,
                "max_memory_mb": max_memory_mb,
                "start_time": psutil.time.time(),
            }
            logger.info(f"Started monitoring process {pid}")
        except psutil.NoSuchProcess:
            logger.error(f"Process {pid} not found")

    def check_memory_usage(self, pid: int) -> Dict[str, Any]:
        """Check memory usage of a monitored process."""
        if pid not in self.processes:
            return {"error": "Process not being monitored"}

        try:
            process_info = self.processes[pid]
            process = process_info["process"]

            # Get memory info
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # Check if over limit
            over_limit = memory_mb > process_info["max_memory_mb"]

            # Get CPU usage
            cpu_percent = process.cpu_percent()

            return {
                "pid": pid,
                "memory_mb": memory_mb,
                "max_memory_mb": process_info["max_memory_mb"],
                "over_limit": over_limit,
                "cpu_percent": cpu_percent,
                "status": process.status(),
                "create_time": process.create_time(),
                "monitoring_duration": psutil.time.time() - process_info["start_time"],
            }

        except psutil.NoSuchProcess:
            return {"error": "Process no longer exists"}
        except Exception as e:
            return {"error": str(e)}

    def kill_if_over_limit(self, pid: int) -> bool:
        """Kill process if it's over memory limit."""
        usage = self.check_memory_usage(pid)

        if "error" in usage:
            return False

        if usage["over_limit"]:
            try:
                process = self.processes[pid]["process"]
                process.kill()
                logger.warning(f"Killed process {pid} for exceeding memory limit")
                return True
            except psutil.NoSuchProcess:
                logger.info(f"Process {pid} already terminated")
                return True
            except Exception as e:
                logger.error(f"Failed to kill process {pid}: {e}")
                return False

        return False

    def stop_monitoring(self, pid: int):
        """Stop monitoring a process."""
        if pid in self.processes:
            del self.processes[pid]
            logger.info(f"Stopped monitoring process {pid}")


class IsolationManager:
    """Main isolation manager."""

    def __init__(self, default_config: IsolationConfig = None):
        self.default_config = default_config or IsolationConfig()
        self.memory_monitor = MemoryMonitor()

    def create_isolator(
        self, config: IsolationConfig = None
    ) -> Union[ProcessIsolator, ContainerIsolator]:
        """Create appropriate isolator based on configuration."""
        config = config or self.default_config

        if config.isolation_type == IsolationType.CONTAINER:
            return ContainerIsolator(config)
        else:
            return ProcessIsolator(config)

    def create_python_sandbox(self, config: IsolationConfig = None) -> PythonSandbox:
        """Create Python sandbox."""
        config = config or self.default_config
        return PythonSandbox(config)

    def get_security_config(self, level: SecurityLevel) -> IsolationConfig:
        """Get predefined security configuration."""
        configs = {
            SecurityLevel.LOW: IsolationConfig(
                isolation_type=IsolationType.PROCESS,
                security_level=SecurityLevel.LOW,
                resource_limits=ResourceLimits(
                    max_memory_mb=1024, max_cpu_time_seconds=60, max_processes=50
                ),
                network_access=True,
            ),
            SecurityLevel.MEDIUM: IsolationConfig(
                isolation_type=IsolationType.PROCESS,
                security_level=SecurityLevel.MEDIUM,
                resource_limits=ResourceLimits(
                    max_memory_mb=512, max_cpu_time_seconds=30, max_processes=10
                ),
                network_access=False,
            ),
            SecurityLevel.HIGH: IsolationConfig(
                isolation_type=IsolationType.CONTAINER,
                security_level=SecurityLevel.HIGH,
                resource_limits=ResourceLimits(
                    max_memory_mb=256, max_cpu_time_seconds=15, max_processes=5
                ),
                network_access=False,
            ),
            SecurityLevel.MAXIMUM: IsolationConfig(
                isolation_type=IsolationType.CONTAINER,
                security_level=SecurityLevel.MAXIMUM,
                resource_limits=ResourceLimits(
                    max_memory_mb=128, max_cpu_time_seconds=10, max_processes=3
                ),
                network_access=False,
                allowed_paths=[],
            ),
        }

        return configs.get(level, configs[SecurityLevel.MEDIUM])


# Global isolation manager
isolation_manager = IsolationManager()
