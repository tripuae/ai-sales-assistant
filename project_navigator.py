import os
import sys
import subprocess

def navigate_to_correct_directory():
    """
    Ensure we're in the correct project directory before running other scripts.
    """
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if we're in the correct directory
    target_dir = "/Users/tripuae/Desktop/TripUAE-Assistant"
    
    if current_dir != target_dir:
        print(f"You're in the wrong directory! Navigating to {target_dir}...")
        try:
            # Change to the correct directory
            os.chdir(target_dir)
            print(f"✅ Successfully changed to: {os.getcwd()}")
        except FileNotFoundError:
            print(f"❌ Error: The directory {target_dir} does not exist!")
            return False
        except PermissionError:
            print(f"❌ Error: No permission to access {target_dir}!")
            return False
    else:
        print("✅ Already in the correct directory.")
    
    # Display available scripts
    print("\nAvailable scripts:")
    for file in os.listdir("."):
        if file.endswith(".py"):
            print(f"- {file}")
    
    # Ask which script to run
    print("\nWhat would you like to do?")
    print("1. Set up environment (setup_env.py)")
    print("2. Run Telegram bot (claude_telegram_bot.py)")
    print("3. Test Claude directly (claude_main.py)")
    print("4. Find available Claude models (claude_model_finder.py)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == "1":
        subprocess.run([sys.executable, "setup_env.py"])
    elif choice == "2":
        subprocess.run([sys.executable, "claude_telegram_bot.py"])
    elif choice == "3":
        subprocess.run([sys.executable, "claude_main.py"])
    elif choice == "4":
        subprocess.run([sys.executable, "claude_model_finder.py"]) 
    elif choice == "5":
        print("Exiting...")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    navigate_to_correct_directory()
