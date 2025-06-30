import os
import re
import time
import subprocess
from collections import defaultdict

directory = '.'  # current directory
file_groups = defaultdict(list)

# Step 1: Group files like filename_1.out, filename_2.out etc.
for filename in os.listdir(directory):
    if filename.endswith('.out'):
        # Match pattern like: anything_###.out, but retain trailing _
        match = re.match(r"(.+_)\d+\.out", filename)
        if match:
            base_name = match.group(1)[:-1]  # remove trailing underscore for merge command
            file_groups[base_name].append(filename)

# Step 2: Process groups with exactly 225 files
for base_name, files in file_groups.items():
    if len(files) == 225:
        print(f"✅ Processing {base_name}_ with 225 files")

        # Use base_name (without trailing _) for command
        try:
            subprocess.run(['python', '-m', 'tools.outputfiles_merge', f"{base_name}_"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Merge failed for {base_name}_: {e}")
            continue

        # Wait for the merged file to appear
        time.sleep(7)

        # Construct filename with double underscore
        merged_filename = f"{base_name}__merged.out"

        if os.path.exists(merged_filename):
            try:
                subprocess.run(['python', '-m', 'tools.plot_Bscan', merged_filename, 'Ez'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Plotting failed for {merged_filename}: {e}")
        else:
            print(f"❌ Merged file not found: {merged_filename}")
    else:
        print(f"⏩ Skipping {base_name}_ — only {len(files)} files found (needs 225)")
