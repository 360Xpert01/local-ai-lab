#!/usr/bin/env python3
"""Test runner for Local AI Lab CLI."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, failfast=False):
    """Run the test suite.
    
    Args:
        test_type: Type of tests to run (unit, integration, e2e, all)
        verbose: Whether to show verbose output
        failfast: Stop on first failure
    """
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add failfast
    if failfast:
        cmd.append("-x")
    
    # Determine test paths
    test_dir = Path(__file__).parent
    
    if test_type == "unit":
        cmd.append(str(test_dir / "unit"))
        cmd.append("-m")
        cmd.append("unit")
    elif test_type == "integration":
        cmd.append(str(test_dir / "integration"))
        cmd.append("-m")
        cmd.append("integration")
    elif test_type == "e2e":
        cmd.append(str(test_dir / "e2e"))
        cmd.append("-m")
        cmd.append("e2e")
    else:  # all
        cmd.append(str(test_dir))
    
    print(f"Running tests: {test_type}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=test_dir.parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run Local AI Lab tests")
    parser.add_argument(
        "type",
        nargs="?",
        default="all",
        choices=["unit", "integration", "e2e", "all"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-x", "--failfast",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        failfast=args.failfast
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
