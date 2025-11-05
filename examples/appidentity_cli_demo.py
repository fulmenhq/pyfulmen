#!/usr/bin/env python3
"""
PyFulmen AppIdentity CLI Demonstration

This script demonstrates the CLI commands available for app identity
management, including show and validate operations.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and display results."""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return e.returncode
    except FileNotFoundError:
        print("❌ Command not found. Make sure pyfulmen is installed and in PATH.")
        return 1


def main():
    """Demonstrate AppIdentity CLI commands."""
    print("PyFulmen AppIdentity CLI Demonstration")
    print("=" * 50)
    
    # Change to the repository root to find .fulmen/app.yaml
    repo_root = Path(__file__).parent.parent
    import os
    os.chdir(repo_root)
    
    commands = [
        # Show current identity (text format)
        [
            sys.executable, "-m", "pyfulmen.cli", "appidentity", "show"
        ],
        "Show current application identity (text format)",
        
        # Show current identity (JSON format)
        [
            sys.executable, "-m", "pyfulmen.cli", "appidentity", "show", "--format", "json"
        ],
        "Show current application identity (JSON format)",
        
        # Validate the current identity file
        [
            sys.executable, "-m", "pyfulmen.cli", "appidentity", "validate", ".fulmen/app.yaml"
        ],
        "Validate the current .fulmen/app.yaml file",
        
        # Show help
        [
            sys.executable, "-m", "pyfulmen.cli", "appidentity", "--help"
        ],
        "Show AppIdentity CLI help",
    ]
    
    exit_codes = []
    
    for i in range(0, len(commands), 2):
        cmd = commands[i]
        description = commands[i + 1]
        exit_code = run_command(cmd, description)
        exit_codes.append(exit_code)
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if all(code == 0 for code in exit_codes):
        print("✅ All CLI commands executed successfully")
    else:
        failed_count = sum(1 for code in exit_codes if code != 0)
        print(f"❌ {failed_count} command(s) failed")
    
    print("\n💡 Tips:")
    print("- Use 'pyfulmen appidentity show' to inspect current configuration")
    print("- Use 'pyfulmen appidentity validate <file>' to check configuration files")
    print("- Add '--format json' for machine-readable output")
    print("- Set FULMEN_APP_IDENTITY_PATH to override discovery")
    
    return 0 if all(code == 0 for code in exit_codes) else 1


if __name__ == "__main__":
    sys.exit(main())