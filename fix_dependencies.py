import subprocess
import sys

def print_package_version(package_name):
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                print(f"{package_name} version: {line.split(':', 1)[1].strip()}")
                return
        print(f"{package_name} is installed but couldn't determine version")
    except subprocess.CalledProcessError:
        print(f"{package_name} is not installed")

def fix_dependencies():
    print("Diagnosing dependency issues...")
    
    # Check current versions
    print("\nCurrent package versions:")
    print_package_version("anthropic")
    print_package_version("httpx")
    
    # Install compatible versions
    print("\nInstalling compatible versions...")
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "anthropic", "httpx"],
        check=True
    )
    
    # Install specific versions known to work together
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "httpx==0.24.1"],
        check=True
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "anthropic==0.5.0"],
        check=True
    )
    
    print("\nAfter fix:")
    print_package_version("anthropic")
    print_package_version("httpx")
    
    print("\nDependency fix complete. Try running your code again.")

if __name__ == "__main__":
    fix_dependencies()
