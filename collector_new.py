import os
import re
import time
import subprocess
from collections import defaultdict

directory = '.'  # current folder
file_groups = defaultdict(list)

# Group files based on base name (excluding final _###)
for filename in os.listdir(directory):
    if filename.endswith(".out"):
        match = re.match(r"(gpr_.+)_\d+\.out", filename)
        if match:
            base_name = match.group(1)
            file_groups[base_name].append(filename)

for base_name, files in file_groups.items():
    if len(files) == 225:
        print(f"✅ Processing {base_name} with 225 files")

        try:
            subprocess.run(['python', '-m', 'tools.outputfiles_merge', base_name], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Merge failed for {base_name}: {e}")
            continue

        # ⏳ Wait for file to be written to disk
        time.sleep(7)

        merged_filename = f"{base_name}__merged.out"

        if os.path.exists(merged_filename):
            try:
                subprocess.run(['python', '-m', 'tools.plot_Bscan', merged_filename, 'Ez'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Plotting failed for {merged_filename}: {e}")
        else:
            print(f"❌ Merged file not found for {base_name} even after waiting.")
    else:
        print(f"⏩ Skipping {base_name} — only {len(files)} files found (needs 225)")
