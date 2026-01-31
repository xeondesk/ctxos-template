#!/usr/bin/env python3
"""
CtxOS Command Line Interface (CLI)

Main entry point for the CtxOS command-line tool.
Provides commands for collecting, analyzing, and visualizing security context.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Import command modules
from cli.commands import collect, graph, risk, agent


class CLIConfig:
    """Configuration for the CLI."""

    def __init__(
        self, project: Optional[str] = None, config: Optional[str] = None, verbose: bool = False
    ):
        """Initialize CLI configuration."""
        self.project = project or os.getenv("CTXOS_PROJECT", "default")
        self.config = config or os.getenv("CTXOS_CONFIG", "configs/default.yaml")
        self.verbose = verbose

    def __repr__(self):
        return f"CLIConfig(project={self.project}, config={self.config}, verbose={self.verbose})"


def setup_global_parser() -> argparse.ArgumentParser:
    """Set up the main argument parser with global options."""
    parser = argparse.ArgumentParser(
        prog="ctxos",
        description="CtxOS - The Operating System for Security Context",
        epilog="For more information, visit: https://github.com/CtxOS/ctxos-template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Version
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show version and exit",
    )

    # Global options
    parser.add_argument(
        "-p",
        "--project",
        type=str,
        default=None,
        help="Project name (default: 'default', env: CTXOS_PROJECT)",
        metavar="PROJECT",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Path to config file (default: 'configs/default.yaml', env: CTXOS_CONFIG)",
        metavar="CONFIG",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser


def setup_subparsers(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    """Set up subparsers for commands."""
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Command to run",
    )

    # Register command modules
    collect.add_command(subparsers)
    graph.add_command(subparsers)
    risk.add_command(subparsers)
    agent.add_command(subparsers)

    return subparsers


def main() -> int:
    """Main entry point for the CLI."""
    parser = setup_global_parser()
    subparsers = setup_subparsers(parser)

    # Parse arguments
    args = parser.parse_args()

    # Create config
    cli_config = CLIConfig(
        project=args.project,
        config=args.config,
        verbose=args.verbose,
    )

    # Debug output
    if args.debug:
        print(f"[DEBUG] CLI Config: {cli_config}")
        print(f"[DEBUG] Arguments: {args}")

    # If no command specified, print help
    if not args.command:
        parser.print_help()
        return 0

    # Handle verbose flag
    if args.verbose:
        print(f"[INFO] Running command: {args.command}")
        print(f"[INFO] Project: {cli_config.project}")
        print(f"[INFO] Config: {cli_config.config}")

    # Execute command (commands should handle their own logic)
    # Return 0 for success, non-zero for failure
    return 0


if __name__ == "__main__":
    sys.exit(main())
