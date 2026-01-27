"""
Unit tests for CLI module.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from cli.ctxos import main, CLIConfig, setup_global_parser, setup_subparsers


class TestCLIConfig:
    """Tests for CLIConfig."""
    
    def test_cli_config_defaults(self):
        """Test default configuration."""
        config = CLIConfig()
        assert config.project == "default"
        assert config.config == "configs/default.yaml"
        assert config.verbose is False
    
    def test_cli_config_with_values(self):
        """Test configuration with values."""
        config = CLIConfig(project="test", config="test.yaml", verbose=True)
        assert config.project == "test"
        assert config.config == "test.yaml"
        assert config.verbose is True
    
    def test_cli_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict("os.environ", {"CTXOS_PROJECT": "env-project", "CTXOS_CONFIG": "env.yaml"}):
            config = CLIConfig()
            assert config.project == "env-project"
            assert config.config == "env.yaml"
    
    def test_cli_config_repr(self):
        """Test string representation."""
        config = CLIConfig(project="test", config="test.yaml")
        repr_str = repr(config)
        assert "project=test" in repr_str
        assert "config=test.yaml" in repr_str


class TestGlobalParser:
    """Tests for global argument parser."""
    
    def test_parser_creation(self):
        """Test parser is created successfully."""
        parser = setup_global_parser()
        assert parser is not None
        assert parser.prog == "ctxos"
    
    def test_version_flag(self):
        """Test version flag."""
        parser = setup_global_parser()
        
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        
        assert exc_info.value.code == 0
    
    def test_global_options(self):
        """Test parsing global options."""
        parser = setup_global_parser()
        args = parser.parse_args(["--project", "test", "--config", "test.yaml", "--verbose"])
        
        assert args.project == "test"
        assert args.config == "test.yaml"
        assert args.verbose is True
    
    def test_help_flag(self):
        """Test help flag."""
        parser = setup_global_parser()
        
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        
        assert exc_info.value.code == 0


class TestSubparsers:
    """Tests for subparsers setup."""
    
    def test_subparsers_created(self):
        """Test subparsers are created."""
        parser = setup_global_parser()
        subparsers = setup_subparsers(parser)
        assert subparsers is not None
    
    def test_collect_command_exists(self):
        """Test collect command is registered."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["collect", "example.com"])
        assert args.command == "collect"
        assert args.target == "example.com"
    
    def test_graph_command_exists(self):
        """Test graph command is registered."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["graph", "analyze", "-i", "input.json"])
        assert args.command == "graph"
        assert args.action == "analyze"
    
    def test_risk_command_exists(self):
        """Test risk command is registered."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["risk", "-i", "input.json", "--engine", "risk"])
        assert args.command == "risk"
        assert args.engine == "risk"
    
    def test_agent_command_exists(self):
        """Test agent command is registered."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["agent", "summarize", "-i", "input.json"])
        assert args.command == "agent"
        assert args.agent == "summarize"


class TestCollectCommand:
    """Tests for collect command."""
    
    def test_collect_with_target(self):
        """Test collect command with target."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["collect", "example.com"])
        assert args.command == "collect"
        assert args.target == "example.com"
        assert args.source == "all"
        assert args.parallel == 4
    
    def test_collect_with_source_option(self):
        """Test collect with source option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["collect", "example.com", "--source", "dns"])
        assert args.source == "dns"
    
    def test_collect_with_output_option(self):
        """Test collect with output option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["collect", "example.com", "-o", "output.json"])
        assert args.output == "output.json"
    
    def test_collect_with_parallel_option(self):
        """Test collect with parallel option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["collect", "example.com", "--parallel", "8"])
        assert args.parallel == 8


class TestGraphCommand:
    """Tests for graph command."""
    
    def test_graph_default_action(self):
        """Test graph command with default action."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["graph"])
        assert args.command == "graph"
        assert args.action == "build"
    
    def test_graph_with_action(self):
        """Test graph command with specific action."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["graph", "export"])
        assert args.action == "export"
    
    def test_graph_with_format_option(self):
        """Test graph with format option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["graph", "-f", "graphml"])
        assert args.format == "graphml"


class TestRiskCommand:
    """Tests for risk command."""
    
    def test_risk_with_input(self):
        """Test risk command with input."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["risk", "-i", "input.json"])
        assert args.command == "risk"
        assert args.input == "input.json"
        assert args.engine == "all"
        assert args.threshold == 0.7
    
    def test_risk_with_engine_option(self):
        """Test risk with engine option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["risk", "-i", "input.json", "--engine", "exposure"])
        assert args.engine == "exposure"
    
    def test_risk_with_threshold_option(self):
        """Test risk with threshold option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["risk", "-i", "input.json", "--threshold", "0.9"])
        assert args.threshold == 0.9


class TestAgentCommand:
    """Tests for agent command."""
    
    def test_agent_default(self):
        """Test agent command with default."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["agent"])
        assert args.command == "agent"
        assert args.agent == "all"
    
    def test_agent_with_type(self):
        """Test agent command with specific type."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["agent", "gap-detect", "-i", "input.json"])
        assert args.agent == "gap-detect"
        assert args.input == "input.json"
    
    def test_agent_with_timeout(self):
        """Test agent with timeout option."""
        parser = setup_global_parser()
        setup_subparsers(parser)
        
        args = parser.parse_args(["agent", "-i", "input.json", "--timeout", "600"])
        assert args.timeout == 600


class TestMainFunction:
    """Tests for main function."""
    
    def test_main_no_command(self):
        """Test main with no command."""
        with patch("sys.argv", ["ctxos"]):
            result = main()
            assert result == 0
    
    def test_main_help(self):
        """Test main with help."""
        with patch("sys.argv", ["ctxos", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_main_with_verbose(self):
        """Test main with verbose flag."""
        with patch("sys.argv", ["ctxos", "--verbose", "collect", "example.com"]):
            result = main()
            assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
