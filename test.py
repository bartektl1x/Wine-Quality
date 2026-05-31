import os
import json
from pathlib import Path

user = spark.sql("SELECT current_user()").collect()[0][0]

paths_to_check = {
    "Workspace Skills":        "/Workspace/.assistant/skills/",
    "Workspace Instructions":  "/Workspace/.assistant_workspace_instructions.md",
    "Your Personal Skills":    f"/Workspace/Users/{user}/.assistant/skills/",
    "Your Personal Instructions": f"/Workspace/Users/{user}/.assistant_instructions.md",
}

for label, path in paths_to_check.items():
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {path}")
    print('='*60)
    
    if not os.path.exists(path):
        print("  ⚠️  Not found — nothing configured here")
        continue

    if os.path.isfile(path):
        with open(path) as f:
            print(f.read())
    else:
        # It's a directory — walk it
        found_any = False
        for root, dirs, files in os.walk(path):
            for file in files:
                found_any = True
                filepath = os.path.join(root, file)
                rel = filepath.replace(path, "")
                print(f"\n  📄 {rel}")
                print("  " + "-"*40)
                with open(filepath) as f:
                    for line in f:
                        print("  " + line, end="")
        if not found_any:
            print("  ⚠️  Directory exists but is empty")
