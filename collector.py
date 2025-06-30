import os
import re
import subprocess
from collections import defaultdict

# Directory where your .out files are located
directory = '.'  # Current folder

# Dictionary to group files by their base filename (without the numeric suffix)
file_groups = defaultdict(list)

# Step 1: Group .out files based on common prefix
for filename in os.listdir(directory):
    if filename.endswith(".out"):
        # Remove the number at the end to get base filename
        match = re.match(r"(gpr_.+)_\d+\.out", filename)
        if match:
            base_name = match.group(1)
            file_groups[base_name].append(filename)

# Step 2: Process only those groups with exactly 225 files
for base_name, files in file_groups.items():
    if len(files) == 225:
        print(f"✅ Processing {base_name} with 225 files")

        try:
            # Run the merge command
            subprocess.run(['python', '-m', 'tools.outputfiles_merge', base_name], check=True)

            # Construct merged filename
            merged_filename = f"{base_name}__merged.out"

            # Run the B-scan plot command
            subprocess.run(['python', '-m', 'tools.plot_Bscan', merged_filename, 'Ez'], check=True)

        except subprocess.CalledProcessError as e:
            print(f"❌ Error while processing {base_name}: {e}")
    else:
        print(f"⏩ Skipping {base_name} — only {len(files)} files found (needs 225)")
