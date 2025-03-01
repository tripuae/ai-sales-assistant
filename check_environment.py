#!/usr/bin/env python3
"""
Environment Check for TripUAE Assistant - Simplified Version

This script checks your environment to ensure the TripUAE Assistant bot can run properly.
It addresses common issues with dependencies, API keys, and network connectivity.
"""

import os
import sys
import platform
import logging
from importlib import import_module
import socket

# Colors for terminal output (works on most Unix-like systems)
class Colors:
    GREEN = '\033[92m' if sys.platform != 'win32' else ''
    YELLOW = '\033[93m' if sys.platform != 'win32' else ''
    RED = '\033[91m' if sys.platform != 'win32' else ''
    BLUE = '\033[94m' if sys.platform != 'win32' else ''
    BOLD = '\033[1m' if sys.platform != 'win32' else ''
    ENDC = '\033[0m' if sys.platform != 'win32' else ''

def print_colored(text, color):
    """Print colored text with fallback for non-ANSI terminals"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    """Print a section header"""
    print("\n" + "=" * 50)
    print_colored(text, Colors.BOLD + Colors.BLUE)
    print("=" * 50)

def check_package(package_name):
    """Check if a package is installed and importable"""
    try:
        # For packages with dashes, replace with underscores for importing
        import_name = package_name.replace("-", "_")
        
        # Try to import the package
        module = import_module(import_name)
        
        # Get version if available
        version = getattr(module, "__version__", "unknown")
        
        print_colored(f"✓ {package_name} is installed (version: {version})", Colors.GREEN)
        return True
    except ImportError:
        print_colored(f"✗ {package_name} is not installed", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"! Error checking {package_name}: {str(e)}", Colors.YELLOW)
        return False

def check_env_vars():
    """Check environment variables needed for the bot"""
    try:
        # Try to load .env file if python-dotenv is available
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print_colored("✓ Loaded .env file", Colors.GREEN)
        except ImportError:
            print_colored("! python-dotenv not installed, skipping .env file loading", Colors.YELLOW)
        
        # Check important environment variables
        env_vars = {
            "OPENAI_API_KEY": "OpenAI API key",
            "TELEGRAM_BOT_TOKEN": "Telegram Bot token"
        }
        
        all_ok = True
        for var, description in env_vars.items():
            value = os.environ.get(var)
            if value:
                # Mask API keys for security
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                print_colored(f"✓ {var} is set: {masked}", Colors.GREEN)
            else:
                print_colored(f"✗ {var} is not set - required for {description}", Colors.RED)
                all_ok = False
        
        return all_ok
    except Exception as e:
        print_colored(f"Error checking environment variables: {e}", Colors.RED)
        return False

def check_connectivity():
    """Basic connectivity check for APIs"""
    services = {
        "Internet (Google)": ("www.google.com", 80),
        "OpenAI API": ("api.openai.com", 443),
        "Telegram API": ("api.telegram.org", 443)
    }
    
    all_ok = True
    for name, (host, port) in services.items():
        try:
            print(f"Testing connection to {name}...")
            socket.create_connection((host, port), timeout=5)
            print_colored(f"✓ Connection to {name} successful", Colors.GREEN)
        except (socket.timeout, socket.error) as e:
            print_colored(f"✗ Cannot connect to {name}: {e}", Colors.RED)
            all_ok = False
    
    return all_ok

def main():
    """Run environment checks"""
    print_colored("TripUAE Assistant Environment Check", Colors.BOLD + Colors.BLUE)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Directory: {os.getcwd()}")
    
    print_header("Required Packages")
    packages = [
        "python-telegram-bot",
        "openai",
        "python-dotenv",
        "requests"
    ]
    
    packages_ok = True
    for package in packages:
        if not check_package(package):
            packages_ok = False
    
    print_header("Environment Variables")
    env_ok = check_env_vars()
    
    print_header("Network Connectivity")
    connectivity_ok = check_connectivity()
    
    # Check if we can actually import our own modules
    print_header("Project Files")
    project_files_ok = True
    
    try:
        print("Checking simple_openai_engine.py...")
        import simple_openai_engine
        print_colored("✓ Successfully imported simple_openai_engine.py", Colors.GREEN)
    except ImportError:
        print_colored("✗ Could not import simple_openai_engine.py - file may be missing or have errors", Colors.RED)
        project_files_ok = False
    except Exception as e:
        print_colored(f"✗ Error in simple_openai_engine.py: {str(e)}", Colors.RED)
        project_files_ok = False
    
    # Summary
    print_header("Results Summary")
    all_ok = packages_ok and env_ok and connectivity_ok and project_files_ok
    
    if all_ok:
        print_colored("✓ All checks passed! Your environment appears to be set up correctly.", Colors.GREEN)
        print("\nNext steps:")
        print("1. Run the bot: python telegram_bot.py")
    else:
        print_colored("✗ Some checks failed. Please address the issues above.", Colors.RED)
        print("\nNext steps:")
        if not packages_ok:
            print("1. Install missing packages: pip install -r requirements.txt")
        if not env_ok:
            print("2. Create/update your .env file with your API keys")
        if not connectivity_ok:
            print("3. Check your internet connection and firewall settings")
        if not project_files_ok:
            print("4. Make sure all required project files are in place and have no syntax errors")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_colored(f"Error running environment check: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)
