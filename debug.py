#!/usr/bin/env python3
"""
Diagnostic tool for TripUAE Assistant
This script checks all dependencies and connectivity required for the bot to function
"""

import sys
import os
import platform
import subprocess
from typing import Dict, Any
import importlib.util
import traceback
import json

# Terminal colors for better visibility
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m' 
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def colored(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"

def check_package(package_name: str, min_version: str = None) -> bool:
    """Check if a package is installed and optionally verify its version"""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print(colored(f"❌ Package '{package_name}' is not installed", Colors.RED))
            return False
        
        # Try to get version
        if min_version:
            try:
                module = importlib.import_module(package_name)
                version = getattr(module, "__version__", "unknown")
                if version == "unknown":
                    print(colored(f"✓ Package '{package_name}' is installed, but version couldn't be determined", Colors.YELLOW))
                else:
                    print(colored(f"✓ Package '{package_name}' version {version} is installed", Colors.GREEN))
                
                # Very basic version check (not handling complex version strings)
                if version != "unknown" and version < min_version:
                    print(colored(f"⚠️ Version {version} is older than minimum required {min_version}", Colors.YELLOW))
            except Exception as e:
                print(colored(f"✓ Package '{package_name}' is installed, but error checking version: {e}", Colors.YELLOW))
        else:
            print(colored(f"✓ Package '{package_name}' is installed", Colors.GREEN))
        return True
    except Exception as e:
        print(colored(f"❌ Error checking package '{package_name}': {e}", Colors.RED))
        return False

def check_env_vars() -> bool:
    """Check required environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print(colored("❌ python-dotenv package not installed, not loading .env file", Colors.RED))
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for generating responses",
        "TELEGRAM_BOT_TOKEN": "Telegram Bot token from BotFather"
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Show masked value for security
            masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
            print(colored(f"✓ {var} is set: {masked} ({description})", Colors.GREEN))
        else:
            print(colored(f"❌ {var} is not set! ({description})", Colors.RED))
            all_present = False
    
    return all_present

def check_openai_connectivity() -> bool:
    """Test connection to OpenAI API"""
    print(colored("\nTesting OpenAI API connection...", Colors.CYAN))
    try:
        from simple_openai_engine import test_openai
        if test_openai():
            print(colored("✓ Successfully connected to OpenAI API", Colors.GREEN))
            return True
        else:
            print(colored("❌ Failed to connect to OpenAI API", Colors.RED))
            return False
    except Exception as e:
        print(colored(f"❌ Error testing OpenAI connectivity: {e}", Colors.RED))
        traceback.print_exc()
        return False

def check_telegram_connectivity() -> bool:
    """Test connection to Telegram Bot API"""
    print(colored("\nTesting Telegram Bot API connection...", Colors.CYAN))
    try:
        from telegram import Bot
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print(colored("❌ TELEGRAM_BOT_TOKEN not found in environment", Colors.RED))
            return False
        
        bot = Bot(token=token)
        bot_info = bot.get_me()
        print(colored(f"✓ Successfully connected to Telegram as @{bot_info.username}", Colors.GREEN))
        return True
    except Exception as e:
        print(colored(f"❌ Error connecting to Telegram: {e}", Colors.RED))
        return False

def check_system_info() -> Dict[str, Any]:
    """Get system information"""
    info = {}
    try:
        info['platform'] = platform.platform()
        info['python_version'] = sys.version
        info['python_path'] = sys.executable
        
        # Check network connectivity
        try:
            print(colored("\nTesting general internet connectivity...", Colors.CYAN))
            # Try to connect to a reliable host
            import socket
            socket.create_connection(("www.google.com", 80), timeout=5)
            info['internet_connectivity'] = True
            print(colored("✓ Internet connection is working", Colors.GREEN))
        except OSError:
            info['internet_connectivity'] = False
            print(colored("❌ No internet connection available!", Colors.RED))
    
    except Exception as e:
        print(colored(f"Error getting system info: {e}", Colors.RED))
    
    return info

def main():
    """Run all diagnostic checks"""
    print(colored("\n===== TripUAE Assistant Diagnostic Tool =====", Colors.BOLD + Colors.CYAN))
    
    # System information
    print(colored("\n==== System Information ====", Colors.CYAN))
    sys_info = check_system_info()
    for key, value in sys_info.items():
        print(f"{key}: {value}")
    
    # Check required packages
    print(colored("\n==== Required Packages ====", Colors.CYAN))
    packages = [
        ('python-telegram-bot', '20.0'),
        ('openai', '1.0.0'),
        ('python-dotenv', '1.0.0'),
        ('requests', '2.25.0'),
    ]
    
    for package, min_version in packages:
        check_package(package, min_version)
    
    # Check environment variables
    print(colored("\n==== Environment Variables ====", Colors.CYAN))
    env_ok = check_env_vars()
    
    # Check API connectivity
    openai_ok = check_openai_connectivity()
    telegram_ok = check_telegram_connectivity()
    
    # Summary
    print(colored("\n==== Diagnostic Summary ====", Colors.CYAN))
    all_ok = env_ok and openai_ok and telegram_ok and sys_info.get('internet_connectivity', False)
    
    if all_ok:
        print(colored("✓ All checks passed! The bot should work correctly.", Colors.GREEN + Colors.BOLD))
    else:
        print(colored("❌ Some checks failed. Please fix the issues highlighted above.", Colors.RED + Colors.BOLD))
    
    print(colored("\nFor detailed logs, check bot_debug.log and openai_debug.log files", Colors.CYAN))
    print(colored("To start the bot, run: python telegram_bot.py", Colors.CYAN))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\nDiagnostic canceled by user", Colors.YELLOW))
    except Exception as e:
        print(colored(f"\nDiagnostic tool error: {e}", Colors.RED))
        traceback.print_exc()
