#!/usr/bin/env python3
import secrets
import os

ENV_FILE = ".env"

def generate_key():
    return secrets.token_hex(32)

def main():
    if os.path.exists(ENV_FILE):
        print(f"Checking {ENV_FILE}...")
        with open(ENV_FILE, "r") as f:
            content = f.read()
            if "SBS_API_KEY=" in content and "change-me" not in content:
                print("A secure key appears to be set already.")
                choice = input("Do you want to overwrite it? (y/N): ")
                if choice.lower() != 'y':
                    print("Aborted.")
                    return

    new_key = generate_key()
    
    # Read existing content or start fresh
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
    else:
        # Try to copy from example if it exists
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                lines = f.readlines()
        else:
            lines = []

    # Filter out any existing key line
    lines = [line for line in lines if not line.strip().startswith("SBS_API_KEY=")]
    
    # Check if file ends with newline
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
        
    # Append new key
    lines.append(f"SBS_API_KEY={new_key}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

    print(f"\nSUCCESS! New API Key generated and saved to {ENV_FILE}")
    print(f"Key: {new_key}")
    print("\nIMPORTANT: Copy this key to your client's config.json file!")

if __name__ == "__main__":
    main()
