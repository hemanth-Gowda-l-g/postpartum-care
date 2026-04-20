import sys
import subprocess
import importlib.util
from typing import List, Tuple

def get_installed_packages() -> List[str]:
    """Get list of installed packages using pip."""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
            return [pkg['name'].lower() for pkg in packages]
        return []
    except Exception:
        return []

def check_package(package_name: str) -> Tuple[bool, str]:
    """Check if a package is installed and importable."""
    # First check if package is in pip list
    installed_packages = get_installed_packages()
    package_name_lower = package_name.lower()
    
    if package_name_lower not in installed_packages:
        return False, f"Package '{package_name}' is not installed"
    
    # Try to import the package
    try:
        # Handle special cases for package names
        import_name = package_name
        if package_name == 'flask_cors':
            import_name = 'flask_cors'
        elif package_name == 'flask_pymongo':
            import_name = 'flask_pymongo'
        elif package_name == 'flask_jwt_extended':
            import_name = 'flask_jwt_extended'
        elif package_name == 'sklearn':
            import_name = 'sklearn'
        
        importlib.import_module(import_name)
        return True, f"✓ {package_name} is installed and importable"
    except ImportError as e:
        return False, f"✗ {package_name} is installed but not importable: {str(e)}"

def main():
    required_packages = [
        'flask',
        'flask_cors',
        'flask_pymongo',
        'flask_jwt_extended',
        'python-dotenv',
        'pymongo',
        'sklearn',
        'numpy',
        'pandas',
        'joblib'
    ]

    print("Checking Python version...")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    print("\nChecking required packages...")
    all_installed = True
    for package in required_packages:
        is_installed, message = check_package(package)
        print(message)
        if not is_installed:
            all_installed = False

    if all_installed:
        print("\nAll dependencies are properly installed!")
    else:
        print("\nSome dependencies are missing or not properly installed.")
        print("Please try the following steps:")
        print("1. Run 'install.bat' again")
        print("2. If the issue persists, try manually installing the missing packages:")
        print("   pip install -r requirements.txt")
        print("3. If you still have issues, try creating a new virtual environment:")
        print("   python -m venv .venv")
        print("   .venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main() 