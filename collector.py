import os
import re
import time
import subprocess
from collections import defaultdict

# Define the working directory (current directory in this case)
directory = '.'

# Dictionary to hold grouped .out files by base name (excluding index suffix)
file_groups = defaultdict(list)

# ----------------------------------------------------------------------
# Step 1: Identify and group related output files
# ----------------------------------------------------------------------
# Files are expected to follow the pattern: baseName_index.out (e.g., scan_1.out, scan_2.out, ...)
# Files with the same baseName are grouped together for batch processing.
for filename in os.listdir(directory):
    if filename.endswith('.out'):
        # Match files ending in "_<number>.out" (e.g., model_123.out)
        match = re.match(r"(.+_)\d+\.out", filename)
        if match:
            # Extract the base name without the trailing underscore for consistency
            base_name = match.group(1)[:-1]
            file_groups[base_name].append(filename)

# ----------------------------------------------------------------------
# Step 2: Process only file groups that have exactly 225 members
# ----------------------------------------------------------------------
# This ensures we're only merging and plotting datasets that are complete
for base_name, files in file_groups.items():
    if len(files) == 225:
        print(f"Processing {base_name}_ with 225 files")

        # Attempt to merge files using a module named `tools.outputfiles_merge`
        # The argument passed is the prefix used to identify the group of files
        try:
            subprocess.run(['python', '-m', 'tools.outputfiles_merge', f"{base_name}_"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Merge failed for {base_name}_: {e}")
            continue  # Skip to the next group if merge fails

        # Wait for the merged file to be generated before plotting
        time.sleep(7)

        # Construct the expected merged output filename
        # The merged file is assumed to follow the naming: baseName__merged.out
        merged_filename = f"{base_name}__merged.out"

        # Check if the merged file exists before attempting to plot
        if os.path.exists(merged_filename):
            try:
                # Plot B-scan of the merged output using 'Ez' field
                subprocess.run(['python', '-m', 'tools.plot_Bscan', merged_filename, 'Ez'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Plotting failed for {merged_filename}: {e}")
        else:
            print(f"Merged file not found: {merged_filename}")
    else:
        # Informative message for incomplete groups
        print(f"Skipping {base_name}_ — only {len(files)} files found (needs 225)")
