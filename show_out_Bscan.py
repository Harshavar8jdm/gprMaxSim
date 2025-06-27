import os
import subprocess

def merge_outfiles(output_files, output_files_dir):
    for i, output_filename in enumerate(output_files):
        output_filepath = os.path.join(output_files_dir, output_filename)

        print(f"\n--- Merging for file {i+1}/{len(output_files)}: {output_filename} ---")

        command = [
            "python",
            "-m",
            "tools.outputfiles_merge",
            output_filepath,
            "--remove-files"
        ]

        try:
            subprocess.run(command, check=True)
            print(f"{output_filename} merge completed.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Merge failed for {output_filename}.")
        except FileNotFoundError:
            print("ERROR: Python or gprMax not found. Check your environment setup.")
        except Exception as e:
            print(f"Unexpected error: {e}")

def show_Bscan(output_files, output_files_dir):
    for i, output_filename in enumerate(output_files):
        output_filepath = os.path.join(output_files_dir, output_filename)

        print(f"\n--- Plotting B-scan for file {i+1}/{len(output_files)}: {output_filename} ---")

        command = [
            "python",
            "-m",
            "tools.plot_Bscan",
            output_filepath,
            "Ez"  # You can change this to Ex, Ey, Hx, etc.
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Plot for {output_filename} completed.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Plotting failed for {output_filename}.")
        except FileNotFoundError:
            print("ERROR: Python or gprMax not found. Check your environment setup.")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__": 
    # Path to directory containing your .out files
    output_files_dir = "C:/Users/Harsha/gprMax/scripts/simulations_radii"
    os.makedirs(output_files_dir, exist_ok=True)

    # Get a list of all .out files
    output_files = [f for f in os.listdir(output_files_dir) if f.endswith(".out")]
    output_files.sort()

    if not output_files:
        print("No .out files found in the directory.")
    else:
        print(f"Found {len(output_files)} .out files to process.")

        merge_outfiles(output_files, output_files_dir)
        show_Bscan(output_files, output_files_dir)

        print("\nAll simulations processed and B-scans generated.")
