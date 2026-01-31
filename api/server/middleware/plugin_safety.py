"""
Plugin safety and isolation for WASM and Python plugins.
"""
import os
import sys
import json
import hashlib
import tempfile
import subprocess
import importlib.util
import ast
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import threading
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    """Types of plugins supported."""
    PYTHON = "python"
    WASM = "wasm"
    BINARY = "binary"


class PluginStatus(str, Enum):
    """Plugin status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class RiskLevel(str, Enum):
    """Risk level for plugins."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    plugin_type: PluginType
    author: str
    description: str
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    checksum: str = ""
    created_at: float = field(default_factory=time.time)
    signature: Optional[str] = None


@dataclass
class SecurityPolicy:
    """Security policy for plugin execution."""
    max_memory_mb: int = 256
    max_cpu_time_seconds: int = 30
    max_file_operations: int = 100
    allowed_imports: List[str] = field(default_factory=list)
    blocked_imports: List[str] = field(default_factory=lambda: [
        'os', 'sys', 'subprocess', 'socket', 'threading', 'multiprocessing',
        'ctypes', 'pickle', 'marshal', 'shelve', 'dbm', 'sqlite3'
    ])
    allowed_file_paths: List[str] = field(default_factory=list)
    blocked_file_paths: List[str] = field(default_factory=lambda: [
        '/etc', '/var', '/usr', '/bin', '/sbin', '/boot', '/sys', '/proc'
    ])
    network_access: bool = False
    file_system_access: bool = False
    system_calls: List[str] = field(default_factory=list)


class PluginValidationError(Exception):
    """Exception for plugin validation errors."""
    pass


class PythonPluginValidator:
    """Validator for Python plugins."""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        
    def validate_plugin(self, plugin_path: str, metadata: PluginMetadata) -> Dict[str, Any]:
        """Validate Python plugin against security policy."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "risk_score": 0
        }
        
        try:
            # Read plugin code
            with open(plugin_path, 'r') as f:
                code = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Syntax error: {e}")
                return validation_result
            
            # Check imports
            self._check_imports(tree, validation_result)
            
            # Check function calls
            self._check_function_calls(tree, validation_result)
            
            # Check file operations
            self._check_file_operations(tree, validation_result)
            
            # Check network operations
            self._check_network_operations(tree, validation_result)
            
            # Check system calls
            self._check_system_calls(tree, validation_result)
            
            # Calculate risk score
            validation_result["risk_score"] = self._calculate_risk_score(validation_result)
            
            # Determine if plugin is safe
            if validation_result["risk_score"] > 70:
                validation_result["valid"] = False
                validation_result["errors"].append("Risk score too high")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {e}")
        
        return validation_result
    
    def _check_imports(self, tree: ast.AST, result: Dict[str, Any]):
        """Check for dangerous imports."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    self._check_single_import(module_name, result)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module
                    self._check_single_import(module_name, result)
    
    def _check_single_import(self, module_name: str, result: Dict[str, Any]):
        """Check a single import against policy."""
        # Check blocked imports
        for blocked in self.policy.blocked_imports:
            if module_name.startswith(blocked):
                result["valid"] = False
                result["errors"].append(f"Blocked import: {module_name}")
                result["risk_score"] += 20
                return
        
        # Check allowed imports
        if self.policy.allowed_imports:
            allowed = False
            for allowed_import in self.policy.allowed_imports:
                if module_name.startswith(allowed_import):
                    allowed = True
                    break
            
            if not allowed:
                result["warnings"].append(f"Import not in allowlist: {module_name}")
                result["risk_score"] += 5
    
    def _check_function_calls(self, tree: ast.AST, result: Dict[str, Any]):
        """Check for dangerous function calls."""
        dangerous_functions = [
            'eval', 'exec', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'reload', 'vars', 'globals', 'locals',
            'dir', 'getattr', 'setattr', 'delattr', 'hasattr'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in dangerous_functions:
                        result["warnings"].append(f"Dangerous function call: {func_name}")
                        result["risk_score"] += 10
    
    def _check_file_operations(self, tree: ast.AST, result: Dict[str, Any]):
        """Check for file system operations."""
        if not self.policy.file_system_access:
            # Look for file operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in ['open', 'file', 'read', 'write', 'remove', 'mkdir']:
                            result["warnings"].append(f"File operation detected: {func_name}")
                            result["risk_score"] += 15
    
    def _check_network_operations(self, tree: ast.AST, result: Dict[str, Any]):
        """Check for network operations."""
        if not self.policy.network_access:
            network_modules = ['socket', 'urllib', 'requests', 'http', 'https', 'ftplib', 'smtplib']
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if any(alias.name.startswith(module) for module in network_modules):
                            result["warnings"].append(f"Network module imported: {alias.name}")
                            result["risk_score"] += 15
    
    def _check_system_calls(self, tree: ast.AST, result: Dict[str, Any]):
        """Check for system calls."""
        system_functions = ['os.system', 'subprocess.run', 'subprocess.call', 'subprocess.Popen']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.value.id}.{node.func.attr}" if hasattr(node.func.value, 'id') else str(node.func.attr)
                    if func_name in system_functions:
                        result["warnings"].append(f"System call detected: {func_name}")
                        result["risk_score"] += 20
    
    def _calculate_risk_score(self, result: Dict[str, Any]) -> int:
        """Calculate overall risk score."""
        base_score = 0
        base_score += len(result["errors"]) * 25
        base_score += len(result["warnings"]) * 5
        return min(base_score, 100)


class WASMPluginValidator:
    """Validator for WebAssembly plugins."""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
    
    def validate_plugin(self, plugin_path: str, metadata: PluginMetadata) -> Dict[str, Any]:
        """Validate WASM plugin against security policy."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "risk_score": 0
        }
        
        try:
            # Check file size
            file_size = os.path.getsize(plugin_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                validation_result["valid"] = False
                validation_result["errors"].append("Plugin file too large")
                validation_result["risk_score"] += 30
            
            # Check WASM header
            with open(plugin_path, 'rb') as f:
                header = f.read(4)
                if header != b'\x00asm':
                    validation_result["valid"] = False
                    validation_result["errors"].append("Invalid WASM file format")
                    validation_result["risk_score"] += 50
            
            # Use wasm-validate if available
            try:
                result = subprocess.run(
                    ['wasm-validate', plugin_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"WASM validation failed: {result.stderr}")
                    validation_result["risk_score"] += 40
            except FileNotFoundError:
                validation_result["warnings"].append("wasm-validate not available, skipping validation")
                validation_result["risk_score"] += 10
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {e}")
            validation_result["risk_score"] += 20
        
        return validation_result


class PluginSandbox:
    """Sandbox for executing plugins safely."""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.active_plugins = {}
        self.plugin_threads = {}
        
    @contextmanager
    def execute_python_plugin(self, plugin_path: str, metadata: PluginMetadata, *args, **kwargs):
        """Execute Python plugin in sandbox."""
        plugin_id = f"{metadata.name}_{metadata.version}_{int(time.time())}"
        
        try:
            # Setup execution environment
            execution_env = self._setup_python_environment()
            
            # Load plugin
            plugin_module = self._load_python_plugin(plugin_path, metadata, execution_env)
            
            # Start execution with timeout
            result = self._execute_with_timeout(
                plugin_module, 
                metadata.entry_point,
                args, 
                kwargs,
                timeout=self.policy.max_cpu_time_seconds
            )
            
            yield result
            
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            raise
        finally:
            # Cleanup
            self._cleanup_plugin(plugin_id)
    
    def _setup_python_environment(self) -> Dict[str, Any]:
        """Setup restricted Python environment."""
        # Create restricted globals
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
            }
        }
        
        return restricted_globals
    
    def _load_python_plugin(self, plugin_path: str, metadata: PluginMetadata, env: Dict[str, Any]):
        """Load Python plugin in restricted environment."""
        spec = importlib.util.spec_from_file_location(metadata.name, plugin_path)
        if spec is None or spec.loader is None:
            raise PluginValidationError("Failed to load plugin specification")
        
        module = importlib.util.module_from_spec(spec)
        
        # Inject restricted globals
        module.__dict__.update(env)
        
        # Execute the module
        spec.loader.exec_module(module)
        
        return module
    
    def _execute_with_timeout(self, module, entry_point: str, args, kwargs, timeout: int):
        """Execute plugin function with timeout."""
        if not hasattr(module, entry_point):
            raise PluginValidationError(f"Entry point '{entry_point}' not found in plugin")
        
        func = getattr(module, entry_point)
        
        # Execute in separate thread with timeout
        result_container = {}
        exception_container = {}
        
        def target():
            try:
                result_container['result'] = func(*args, **kwargs)
            except Exception as e:
                exception_container['exception'] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout occurred
            raise PluginValidationError(f"Plugin execution timed out after {timeout} seconds")
        
        if 'exception' in exception_container:
            raise exception_container['exception']
        
        return result_container.get('result')
    
    def _cleanup_plugin(self, plugin_id: str):
        """Cleanup plugin resources."""
        if plugin_id in self.active_plugins:
            del self.active_plugins[plugin_id]
        
        if plugin_id in self.plugin_threads:
            thread = self.plugin_threads[plugin_id]
            if thread.is_alive():
                thread.join(timeout=1)
            del self.plugin_threads[plugin_id]


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self.plugins = {}
        self.approved_plugins = {}
        self.blacklisted_plugins = set()
        self.plugin_signatures = {}
        
    def register_plugin(self, metadata: PluginMetadata, plugin_path: str) -> bool:
        """Register a new plugin."""
        plugin_id = f"{metadata.name}:{metadata.version}"
        
        # Check if already registered
        if plugin_id in self.plugins:
            logger.warning(f"Plugin {plugin_id} already registered")
            return False
        
        # Calculate checksum
        checksum = self._calculate_checksum(plugin_path)
        metadata.checksum = checksum
        
        # Store plugin
        self.plugins[plugin_id] = {
            "metadata": metadata,
            "path": plugin_path,
            "status": PluginStatus.PENDING,
            "registered_at": time.time()
        }
        
        logger.info(f"Plugin {plugin_id} registered successfully")
        return True
    
    def approve_plugin(self, plugin_id: str, approved_by: str) -> bool:
        """Approve a plugin."""
        if plugin_id not in self.plugins:
            return False
        
        self.plugins[plugin_id]["status"] = PluginStatus.APPROVED
        self.plugins[plugin_id]["approved_by"] = approved_by
        self.plugins[plugin_id]["approved_at"] = time.time()
        
        self.approved_plugins[plugin_id] = self.plugins[plugin_id]
        
        logger.info(f"Plugin {plugin_id} approved by {approved_by}")
        return True
    
    def blacklist_plugin(self, plugin_id: str, reason: str) -> bool:
        """Blacklist a plugin."""
        if plugin_id not in self.plugins:
            return False
        
        self.plugins[plugin_id]["status"] = PluginStatus.BLACKLISTED
        self.plugins[plugin_id]["blacklist_reason"] = reason
        self.plugins[plugin_id]["blacklisted_at"] = time.time()
        
        self.blacklisted_plugins.add(plugin_id)
        
        if plugin_id in self.approved_plugins:
            del self.approved_plugins[plugin_id]
        
        logger.warning(f"Plugin {plugin_id} blacklisted: {reason}")
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin information."""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self, status: Optional[PluginStatus] = None) -> List[Dict[str, Any]]:
        """List plugins, optionally filtered by status."""
        plugins = list(self.plugins.values())
        
        if status:
            plugins = [p for p in plugins if p["status"] == status]
        
        return plugins
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()


class PluginManager:
    """Main plugin manager."""
    
    def __init__(self, default_policy: SecurityPolicy = None):
        self.default_policy = default_policy or SecurityPolicy()
        self.registry = PluginRegistry()
        self.python_validator = PythonPluginValidator(self.default_policy)
        self.wasm_validator = WASMPluginValidator(self.default_policy)
        self.sandbox = PluginSandbox(self.default_policy)
        
    def upload_plugin(self, plugin_file: str, metadata: PluginMetadata) -> Dict[str, Any]:
        """Upload and validate a plugin."""
        result = {
            "success": False,
            "plugin_id": None,
            "validation_result": None,
            "errors": []
        }
        
        try:
            # Validate plugin
            if metadata.plugin_type == PluginType.PYTHON:
                validation_result = self.python_validator.validate_plugin(plugin_file, metadata)
            elif metadata.plugin_type == PluginType.WASM:
                validation_result = self.wasm_validator.validate_plugin(plugin_file, metadata)
            else:
                result["errors"].append(f"Unsupported plugin type: {metadata.plugin_type}")
                return result
            
            result["validation_result"] = validation_result
            
            # Check if validation passed
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                return result
            
            # Register plugin
            if not self.registry.register_plugin(metadata, plugin_file):
                result["errors"].append("Failed to register plugin")
                return result
            
            plugin_id = f"{metadata.name}:{metadata.version}"
            result["plugin_id"] = plugin_id
            result["success"] = True
            
            logger.info(f"Plugin {plugin_id} uploaded and validated successfully")
            
        except Exception as e:
            result["errors"].append(f"Upload failed: {e}")
            logger.error(f"Plugin upload failed: {e}")
        
        return result
    
    def execute_plugin(
        self, 
        plugin_id: str, 
        entry_point: str, 
        args: tuple = (), 
        kwargs: dict = None
    ) -> Any:
        """Execute an approved plugin."""
        kwargs = kwargs or {}
        
        # Get plugin
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            raise PluginValidationError(f"Plugin {plugin_id} not found")
        
        # Check if approved
        if plugin_info["status"] != PluginStatus.APPROVED:
            raise PluginValidationError(f"Plugin {plugin_id} is not approved")
        
        # Check if blacklisted
        if plugin_id in self.registry.blacklisted_plugins:
            raise PluginValidationError(f"Plugin {plugin_id} is blacklisted")
        
        metadata = plugin_info["metadata"]
        plugin_path = plugin_info["path"]
        
        # Execute in sandbox
        if metadata.plugin_type == PluginType.PYTHON:
            with self.sandbox.execute_python_plugin(plugin_path, metadata, *args, **kwargs) as result:
                return result
        else:
            raise PluginValidationError(f"Execution not supported for {metadata.plugin_type} plugins")
    
    def get_security_policy(self, risk_level: RiskLevel) -> SecurityPolicy:
        """Get security policy based on risk level."""
        policies = {
            RiskLevel.LOW: SecurityPolicy(
                max_memory_mb=512,
                max_cpu_time_seconds=60,
                network_access=True,
                file_system_access=True,
                allowed_imports=['datetime', 'json', 'math', 'random', 'string', 're']
            ),
            RiskLevel.MEDIUM: SecurityPolicy(
                max_memory_mb=256,
                max_cpu_time_seconds=30,
                network_access=False,
                file_system_access=False,
                allowed_imports=['datetime', 'json', 'math', 'random', 'string']
            ),
            RiskLevel.HIGH: SecurityPolicy(
                max_memory_mb=128,
                max_cpu_time_seconds=15,
                network_access=False,
                file_system_access=False,
                allowed_imports=['datetime', 'json', 'math']
            ),
            RiskLevel.CRITICAL: SecurityPolicy(
                max_memory_mb=64,
                max_cpu_time_seconds=10,
                network_access=False,
                file_system_access=False,
                allowed_imports=['json', 'math']
            )
        }
        
        return policies.get(risk_level, policies[RiskLevel.MEDIUM])


# Global plugin manager
plugin_manager = PluginManager()
