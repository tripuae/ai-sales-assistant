import os
import sys
import subprocess
import time

def update_github_repository():
    """
    Script to update the GitHub repository with all new files from TripUAE-Assistant.
    """
    print("===== GitHub Repository Update Tool =====")
    
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Git is not installed or not in PATH. Please install Git first.")
        sys.exit(1)
    
    # Make sure we're in the correct directory
    current_dir = os.getcwd()
    expected_dir = "/Users/tripuae/Desktop/TripUAE-Assistant"
    
    if current_dir != expected_dir:
        print(f"Changing directory to {expected_dir}...")
        try:
            os.chdir(expected_dir)
            print(f"✅ Now in: {os.getcwd()}")
        except FileNotFoundError:
            print(f"❌ Error: Directory {expected_dir} not found.")
            sys.exit(1)
    
    # Check if .git directory exists
    if not os.path.exists(".git"):
        print("Repository not initialized. Setting up Git repository...")
        
        # Initialize git repository
        subprocess.run(["git", "init"], check=True)
        
        # Configure remote repository
        repo_url = "https://github.com/tripuae/ai-sales-assistant.git"
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        
        print("✅ Git repository initialized and remote added.")
    else:
        print("✅ Git repository already initialized.")
    
    # Check remote repository
    try:
        remote_result = subprocess.run(
            ["git", "remote", "-v"], 
            check=True, 
            stdout=subprocess.PIPE,
            text=True
        )
        print("\nConfigured remotes:")
        print(remote_result.stdout)
    except subprocess.CalledProcessError:
        print("❌ Error checking remotes. Trying to add origin...")
        repo_url = "https://github.com/tripuae/ai-sales-assistant.git"
        subprocess.run(["git", "remote", "add", "origin", repo_url])
    
    # Create .gitignore if it doesn't exist
    if not os.path.exists(".gitignore"):
        print("Creating .gitignore file...")
        with open(".gitignore", "w") as f:
            f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env

# IDE files
.idea/
.vscode/
*.swp
*.swo

# macOS
.DS_Store

# Logs
*.log
""")
        print("✅ Created .gitignore file")
    
    # Check for .env file and make sure it's in .gitignore
    if os.path.exists(".env"):
        print("\nFound .env file. Ensuring it's not tracked by Git...")
        
        # Create/copy .env.example if it doesn't exist
        if not os.path.exists(".env.example"):
            print("Creating .env.example from .env (with placeholder values)...")
            with open(".env", "r") as env_file:
                env_content = env_file.read()
            
            # Replace actual keys with placeholders
            env_example_content = env_content
            env_lines = env_content.split('\n')
            env_example_lines = []
            
            for line in env_lines:
                if '=' in line and not line.startswith('#'):
                    key, _ = line.split('=', 1)
                    env_example_lines.append(f"{key}=your_{key.lower()}_here")
                else:
                    env_example_lines.append(line)
            
            with open(".env.example", "w") as example_file:
                example_file.write('\n'.join(env_example_lines))
            
            print("✅ Created .env.example with placeholder values")
    
    # Add all files
    print("\nAdding files to Git...")
    subprocess.run(["git", "add", "."], check=True)
    
    # Check status
    status_result = subprocess.run(
        ["git", "status"], 
        check=True,
        stdout=subprocess.PIPE,
        text=True
    )
    print("\nGit status:")
    print(status_result.stdout)
    
    # Commit changes
    commit_message = f"Update TripUAE Assistant with new files and improvements"
    print(f"\nCommitting changes with message: '{commit_message}'")
    
    try:
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print("✅ Changes committed successfully")
    except subprocess.CalledProcessError:
        print("No changes to commit or there was an error.")
    
    # Push to GitHub
    print("\nPushing to GitHub repository...")
    
    # Ask for credentials if needed
    print("\nYou may be prompted for your GitHub username and password/token.")
    time.sleep(1)
    
    try:
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        print("✅ Successfully pushed to GitHub!")
    except subprocess.CalledProcessError:
        print("❌ Error pushing to GitHub. Trying to push to master branch instead...")
        
        try:
            subprocess.run(["git", "push", "-u", "origin", "master"], check=True)
            print("✅ Successfully pushed to GitHub master branch!")
        except subprocess.CalledProcessError:
            print("\n❌ Failed to push to GitHub. Common issues:")
            print("1. Repository might not exist or you don't have access")
            print("2. Remote branch might be ahead of your local branch")
            print("3. Authentication failure")
            
            print("\nIf you're using HTTPS, make sure your GitHub token has repo permissions.")
            print("You might want to try pulling first with: git pull origin main --rebase")
    
    print("\n===== GitHub Update Complete =====")

if __name__ == "__main__":
    update_github_repository()
