import os
from dotenv import load_dotenv

def fix_env_file():
    """Fix the token in the .env file by removing quotes"""
    print("===== Fixing .env Token Format =====")
    
    # Path to .env file
    env_path = os.path.join(os.getcwd(), '.env')
    
    # Read the file
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Fix the lines
        new_lines = []
        for line in lines:
            if line.startswith('TELEGRAM_BOT_TOKEN'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    # Remove single or double quotes if present
                    if (value.startswith("'") and value.endswith("'")) or \
                       (value.startswith('"') and value.endswith('"')):
                        value = value[1:-1]
                    new_lines.append(f"TELEGRAM_BOT_TOKEN={value}\n")
                    print(f"Fixed TELEGRAM_BOT_TOKEN: {value}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Write back to the file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        print("✅ .env file updated successfully!")
    else:
        print("❌ .env file not found!")

if __name__ == "__main__":
    fix_env_file()
