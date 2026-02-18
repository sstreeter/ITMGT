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

def generate_themed_key(count=4, locked_words=None):
    if locked_words is None:
        locked_words = {} # Dict of index -> word
        
    words = []
    for i in range(count):
        if i in locked_words:
            words.append(locked_words[i])
        else:
            words.append(secrets.choice(ALL_WORDS))
    return words

def format_key(words, casing="sentence"):
    # Apply casing
    formatted_words = []
    for w in words:
        if casing == "sentence":
            formatted_words.append(w.capitalize())
        elif casing == "lower":
            formatted_words.append(w.lower())
        elif casing == "upper":
            formatted_words.append(w.upper())
        elif casing == "random":
            formatted_words.append(secrets.choice([w.upper(), w.lower(), w.capitalize()]))
            
    # Add number suffix? Maybe optional. For now, keep it for uniqueness.
    # But user asked for customization. Let's make it simple: 
    # Just words joined by dashes, maybe append number if not manually edited.
    # Actually, let's keep the number standard for entropy, but user can edit it out.
    number = secrets.randbelow(1000)
    key_str = "-".join(formatted_words) + f"-{number}"
    return key_str

def save_key(new_key):
    # Read existing content or start fresh
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
    else:
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                lines = f.readlines()
        else:
            lines = []

    lines = [line for line in lines if not line.strip().startswith("SBS_API_KEY=")]
    
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
        
    lines.append(f"SBS_API_KEY={new_key}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

    print(f"\nSUCCESS! New API Key generated and saved to {ENV_FILE}")
    print(f"Key: {new_key}")
    print("\nIMPORTANT: You must update your client's 'config.json' file with this key:")
    print(f'   "ApiKey": "{new_key}"')

def main():
    print(f"--- ITMGT Key Generator ---")
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

    print("\nChoose your key style:")
    print("1. Random Hex (e.g., 7f8e9d...) [Maximum Security]")
    print("2. Themed Words (e.g., Dragon-Laser-Biology-42) [Customizable]")
    style = input("Selection [1/2]: ").strip()
    
    key_history = []
    
    # Defaults
    current_count = 4
    current_casing = "sentence"
    current_words = []
    locked_indices = {}
    
    # Init
    if style == "2":
        current_words = generate_themed_key(current_count, locked_indices)
        new_key_str = format_key(current_words, current_casing)
    else:
        new_key_str = generate_hex_key()
        current_words = []
        
    while True:
        key_history.append(new_key_str)
        if len(key_history) > 100:
            key_history.pop(0)

        print(f"\nGenerared Key: \033[92m{new_key_str}\033[0m")
        
        if style == "2":
            # UX for Themed
            print(f"Details: {current_count} words | Case: {current_casing}")
            print("Current Words: ", end="")
            for i, w in enumerate(current_words):
                status = " 🔒" if i in locked_indices else ""
                print(f"{i+1}.{w}{status}  ", end="")
            print("")
            
            print("\nOptions:")
            print(" [y] Accept")
            print(" [n] New roll (respects locks)")
            print(" [l] Lock/Unlock (e.g. 'l 1 3')")
            print(" [c] Count (change # of words)")
            print(" [s] Style (upper, lower, sentence, random)")
            print(" [e] Edit manually")
            print(" [h] History")
            print(" [q] Quit")
            
            choice = input("Choice: ").strip().lower()
            
            if choice == 'y':
                save_key(new_key_str)
                sys.exit(0)
            elif choice == 'n':
                current_words = generate_themed_key(current_count, locked_indices)
                new_key_str = format_key(current_words, current_casing)
                continue
            elif choice.startswith('l'):
                parts = choice.split()
                if len(parts) > 1:
                    for p in parts[1:]:
                        try:
                            idx = int(p) - 1
                            if 0 <= idx < current_count:
                                if idx in locked_indices:
                                    del locked_indices[idx]
                                else:
                                    locked_indices[idx] = current_words[idx]
                        except ValueError:
                            pass
                continue
            elif choice == 'c':
                try:
                    new_c = int(input("Enter new word count (3-10): "))
                    if 3 <= new_c <= 10:
                        current_count = new_c
                        # Reset locks that are out of bounds
                        locked_indices = {i: w for i, w in locked_indices.items() if i < current_count}
                        # Regenerate to fit new count
                        current_words = generate_themed_key(current_count, locked_indices)
                        new_key_str = format_key(current_words, current_casing)
                except ValueError:
                    print("Invalid number.")
                continue
            elif choice == 's':
                print("Styles: [u]pper, [l]ower, [s]entence, [r]andom")
                s = input("Select style: ").strip().lower()
                if s.startswith('u'): current_casing = "upper"
                elif s.startswith('l'): current_casing = "lower"
                elif s.startswith('s'): current_casing = "sentence"
                elif s.startswith('r'): current_casing = "random"
                new_key_str = format_key(current_words, current_casing)
                continue
            elif choice == 'e':
                print(f"Current: {new_key_str}")
                edited = input("Edit:    ").strip()
                if edited:
                    new_key_str = edited
                    # Note: Editing breaks the word tracking/locking loop usually, 
                    # but we can just treat it as a final override.
                    # We'll put it in history.
                    # If they continue 'n', it discards edits and rolls fresh.
                    pass
                continue
            elif choice == 'h':
                # History...
                if len(key_history) > 1:
                    print("\n--- Key History ---")
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
                sys.exit(0)

        else:
            # Hex Loop
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
