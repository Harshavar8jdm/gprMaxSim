import os
import re

directory = '.'  # or full path to folder with .png files
copy_pattern = re.compile(r"(.*?) - Copy(?: \((\d+)\))?\.png", re.IGNORECASE)

for filename in os.listdir(directory):
    if not filename.endswith(".png"):
        continue

    old_path = os.path.join(directory, filename)

    # Handle Windows-style duplicate copies like "- Copy.png" or "- Copy (2).png"
    match = copy_pattern.match(filename)
    if match:
        base_name = match.group(1)  # filename without " - Copy"
        copy_number = match.group(2)

        # Apply clay → wet_concrete replacement
        new_base = base_name.replace("clay", "wet_concrete")

        if copy_number:
            new_filename = f"{new_base}_copy{copy_number}.png"
        else:
            new_filename = f"{new_base}_copy1.png"
    else:
        # Regular filename, just do the replacement
        new_filename = filename.replace("clay", "wet_concrete")

    new_path = os.path.join(directory, new_filename)

    # Skip renaming if already correct
    if old_path == new_path:
        continue

    # Prevent overwrite
    if os.path.exists(new_path):
        print(f"⚠️ Skipping: {new_filename} already exists.")
        continue

    print(f"🔁 Renaming: {filename} → {new_filename}")
    os.rename(old_path, new_path)
