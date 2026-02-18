#!/usr/bin/env python3
import secrets
import os
import random
import sys

ENV_FILE = ".env"

# A small fallback list of friendly words
FALLBACK_WORDS = [
    "correct", "horse", "battery", "staple", "purple", "monkey", "dishwasher",
    "galaxy", "pizza", "noodle", "audit", "secure", "server", "linux", "power",
    "shell", "biology", "utah", "admin", "coffee", "bacon", "cheese", "dragon",
    "ninja", "wizard", "rocket", "laser", "turbo", "hyper", "mega", "ultra"
]

def get_word_list():
    # Try to load from system dictionary for variety
    system_dict = "/usr/share/dict/words"
    if os.path.exists(system_dict):
        try:
            with open(system_dict, "r") as f:
                # Filter for reasonable length, lowercase, no punctuation
                words = [w.strip().lower() for w in f if 3 < len(w.strip()) < 9 and w.strip().isalpha()]
            if len(words) > 1000:
                return words
        except Exception:
            pass # Fail silently using fallback
    
    return FALLBACK_WORDS

def generate_hex_key():
    return secrets.token_hex(32)

def generate_memorable_key():
    words = get_word_list()
    # Pick 4 random words (5 was getting long with bigger dictionary words)
    picked_words = [secrets.choice(words) for _ in range(4)]
    # Add a random number for good measure
    number = secrets.randbelow(1000)
    # Capitalize and join
    key = "-".join(w.capitalize() for w in picked_words) + f"-{number}"
    return key

def save_key(new_key):
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

def main():
    if os.path.exists(ENV_FILE):
        print(f"Checking {ENV_FILE}...")
        with open(ENV_FILE, "r") as f:
            content = f.read()
            if "SBS_API_KEY=" in content and "change-me" not in content:
                print("A secure key appears to be set already.")
                # Force interactive check only if run interactively, otherwise assume overwrite for automation? 
                # Actually, let's keep it safe.
                choice = input("Do you want to overwrite it? (y/N): ")
                if choice.lower() != 'y':
                    print("Aborted.")
                    return

    print("\nChoose your key style:")
    print("1. Random Hex (e.g., 7f8e9d...) [Maximum Security]")
    print("2. Memorable Words (e.g., Purple-Monkey-Dishwasher-42) [Easier to type]")
    style = input("Selection [1/2]: ").strip()
    
    key_history = []
    
    while True:
        if style == "2":
            new_key = generate_memorable_key()
        else:
            new_key = generate_hex_key()
            
        key_history.append(new_key)
        # Limit history to 100
        if len(key_history) > 100:
            key_history.pop(0)
            
        print(f"\nGenerated Key: \033[92m{new_key}\033[0m")
        print("Options: [y]es, [n]ext, [h]istory, [q]uit")
        
        while True:
            choice = input("Choice: ").strip().lower()
            
            if choice == 'y':
                save_key(new_key)
                sys.exit(0)
            elif choice == 'n':
                break # Break inner loop to generate new key
            elif choice == 'q':
                print("Aborted.")
                sys.exit(0)
            elif choice == 'h':
                if len(key_history) <= 1:
                    print("No history yet.")
                    continue
                    
                print("\n--- Key History ---")
                for i, k in enumerate(key_history):
                    print(f"{i+1}. {k}")
                
                try:
                    idx_str = input("\nEnter number to select (or 0 to cancel): ")
                    idx = int(idx_str)
                    if idx > 0 and idx <= len(key_history):
                        selected_key = key_history[idx-1]
                        save_key(selected_key)
                        sys.exit(0)
                except ValueError:
                    pass
                print("Returning to current key...")
                print(f"Current Key: \033[92m{new_key}\033[0m")
                print("Options: [y]es, [n]ext, [h]istory, [q]uit")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
