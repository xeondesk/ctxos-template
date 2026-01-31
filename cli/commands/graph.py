"""Graph command for building and analyzing entity graphs."""


def add_command(subparsers):
    """Register the graph command."""
    parser = subparsers.add_parser(
        "graph",
        help="Build and analyze entity relationship graphs",
        description="Create, visualize, and analyze security context graphs",
    )

    parser.add_argument(
        "action",
        nargs="?",
        choices=["build", "analyze", "export", "visualize"],
        default="build",
        help="Graph action to perform",
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input file (JSON) with entities and signals",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for graph results",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "graphml", "dot", "png"],
        default="json",
        help="Output format",
    )

    parser.set_defaults(func=handle_graph)


def handle_graph(args):
    """Handle graph command execution."""
    if not args.input:
        print("Error: --input is required for graph command")
        return 1

    if args.verbose:
        print(f"[INFO] Graph action: {args.action}")
        print(f"[INFO] Input: {args.input}")
        print(f"[INFO] Output format: {args.format}")

    print(f"Building graph from {args.input}...")
    # Actual graph logic would go here
    return 0
