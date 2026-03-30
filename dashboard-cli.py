#!/usr/bin/env python3
"""
Command-line interface to start the Fleet dashboard.

Usage:
    uv run python dashboard-cli.py [--host HOST] [--port PORT] [QUEUE_DIR]

Examples:
    uv run python dashboard-cli.py
    uv run python dashboard-cli.py --host 0.0.0.0 --port 8080
    uv run python dashboard-cli.py ./my-queue
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Start the Fleet dashboard")
    parser.add_argument(
        "queue_dir",
        nargs="?",
        default="./queue",
        help="Path to the queue directory (default: ./queue)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    from dashboard import run_dashboard
    
    queue_path = Path(args.queue_dir)
    print(f"Starting Fleet Dashboard...")
    print(f"Queue directory: {queue_path.absolute()}")
    print(f"Dashboard URL: http://{args.host}:{args.port}")
    print()
    print("Press Ctrl+C to stop")
    
    run_dashboard(queue_path, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
