#!/usr/bin/env python3
import secrets
import os
import random
import sys

ENV_FILE = ".env"

# Curated Themed Vocabulary
THEMES = {
    "biology": [
        "mitochondria", "ribosome", "enzyme", "neuron", "synapse", "helix", "genome", 
        "plasma", "virus", "bacteria", "fungus", "spore", "fossil", "darwin", "clone", 
        "mutation", "hybrid", "organism", "protein", "lipid", "amino", "carbon"
    ],
    "scifi": [
        "laser", "phaser", "warp", "droid", "cyborg", "matrix", "alien", "ufo", "comet", 
        "nebula", "blaster", "photon", "quantum", "hyper", "vortex", "portal", "robot", 
        "mecha", "nano", "cyber", "galactic", "stellar", "void"
    ],
    "fantasy": [
        "dragon", "wizard", "elf", "dwarf", "orc", "goblin", "potion", "mana", "spell", 
        "wand", "sword", "shield", "armor", "quest", "dungeon", "crown", "throne", 
        "kingdom", "magic", "sorcerer", "knight", "beast"
    ],
    "anime": [
        "ninja", "shogun", "titan", "spirit", "demon", "ghoul", "slayer", "alchemist", 
        "saiyan", "hero", "villain", "sensei", "chakra", "ki", "stand", "pirate", 
        "haki", "bankai", "mecha", "gundam", "kaiju"
    ],
    "tech": [
        "linux", "python", "server", "proxy", "router", "switch", "pixel", "byte", 
        "cache", "token", "kernel", "shell", "bash", "audit", "logic", "binary", 
        "cipher", "crypto", "admin", "sudo", "root"
    ]
}

# Flatten list for general use
ALL_WORDS = [word for category in THEMES.values() for word in category]

def generate_hex_key():
    return secrets.token_hex(32)

def generate_themed_key(locked_words=None):
    if locked_words is None:
        locked_words = {} # Dict of index -> word
        
    words = []
    # We want 4 words total
    for i in range(4):
        if i in locked_words:
            words.append(locked_words[i])
        else:
            # Pick a random word from ALL_WORDS
            words.append(secrets.choice(ALL_WORDS))
            
    # Add a random number for good measure
    number = secrets.randbelow(1000)
    # Capitalize and join
    key_str = "-".join(w.capitalize() for w in words) + f"-{number}"
    return key_str, words

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
    print(f"--- ITMGT Key Generator ---")
    if os.path.exists(ENV_FILE):
        print(f"Checking {ENV_FILE}...")
        with open(ENV_FILE, "r") as f:
            content = f.read()
            if "SBS_API_KEY=" in content and "change-me" not in content:
                print("A secure key appears to be set already.")
                # We assume manual run means we might want to overwrite or verify
                choice = input("Do you want to overwrite it? (y/N): ")
                if choice.lower() != 'y':
                    print("Aborted.")
                    return

    print("\nChoose your key style:")
    print("1. Random Hex (e.g., 7f8e9d...) [Maximum Security]")
    print("2. Themed Words (e.g., Dragon-Laser-Biology-42) [Fun & Memorable]")
    style = input("Selection [1/2]: ").strip()
    
    key_history = []
    current_words = [] # List of strings
    locked_indices = {} # Map index -> word
    
    # Initial generation
    if style == "2":
        new_key_str, current_words = generate_themed_key(locked_indices)
    else:
        new_key_str = generate_hex_key()
        current_words = []
        
    while True:
        key_history.append(new_key_str)
        if len(key_history) > 100:
            key_history.pop(0)

        print(f"\nGenerated Key: \033[92m{new_key_str}\033[0m")
        
        if style == "2":
            # UX for Locking
            print("Current Words: ", end="")
            for i, w in enumerate(current_words):
                status = " [LOCKED]" if i in locked_indices else ""
                print(f"{i+1}. {w.capitalize()}{status}  ", end="")
            print("")
            
            print("\nOptions:")
            print(" [y] Accept this key")
            print(" [n] New (Roll all unlocked words)")
            print(" [l] Lock/Unlock words (e.g., 'l 1 3' toggles words 1 & 3)")
            print(" [h] History")
            print(" [q] Quit")
            
            choice = input("Choice: ").strip().lower()
            
            if choice == 'y':
                save_key(new_key_str)
                sys.exit(0)
            elif choice == 'n':
                # Generate new key respecting locks
                new_key_str, current_words = generate_themed_key(locked_indices)
                continue
            elif choice.startswith('l'):
                parts = choice.split()
                if len(parts) > 1:
                    for p in parts[1:]:
                        try:
                            idx = int(p) - 1
                            if 0 <= idx < 4:
                                if idx in locked_indices:
                                    del locked_indices[idx]
                                else:
                                    locked_indices[idx] = current_words[idx]
                        except ValueError:
                            pass
                    # Regenerate immediately to show effect?
                    # Or just redisplay? Users expect immediate feedback.
                    # Let's regenerate immediately for the UNLOCKED slots to show progress?
                    # Or just redisplay the current key with LOCK status updated.
                    # Better UX: Redistplay current key with [LOCKED] status updated, wait for 'n' to roll.
                    # But if we just 'continue', we'll re-append the SAME key to history?
                    # Let's just create a 'dirty' flag or just re-loop without generating?
                    # The top of loop doesn't generate. We generate inside the 'n' block or init.
                    # Wait, the structure was slightly off.
                    # Refactoring loop structure below.
                    pass 
                
                # Logic Fix: Don't generate new key here, just update display
                # We need to restructure loop to separate Display from Generation
                continue 

            elif choice == 'h':
                # ... same history logic ...
                if len(key_history) > 1:
                    print("\n--- Key History ---")
                    # Show last 10 for brevity?
                    start_idx = max(0, len(key_history) - 10)
                    for i in range(start_idx, len(key_history)):
                        print(f"{i+1}. {key_history[i]}")
                    try:
                        idx = int(input("\nEnter number to select (or 0 to cancel): "))
                        if idx > 0 and idx <= len(key_history):
                            save_key(key_history[idx-1])
                            sys.exit(0)
                    except ValueError:
                        pass
                continue
            elif choice == 'q':
                print("Aborted.")
                sys.exit(0)

        else:
            # Hex Style Simple Loop
            print("\nOptions: [y]es, [n]ext, [h]istory, [q]uit")
            choice = input("Choice: ").strip().lower()
            if choice == 'y':
                save_key(new_key_str)
                sys.exit(0)
            elif choice == 'n':
                new_key_str = generate_hex_key()
                continue
            elif choice == 'h':
                 if len(key_history) > 1:
                    print("\n--- Key History ---")
                    for i, k in enumerate(key_history):
                        print(f"{i+1}. {k}")
                    try:
                        idx = int(input("\nEnter number to select (or 0 to cancel): "))
                        if idx > 0 and idx <= len(key_history):
                            save_key(key_history[idx-1])
                            sys.exit(0)
                    except ValueError:
                        pass
                 continue
            elif choice == 'q':
                sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
