import os
import subprocess

# --- User-defined fixed number of traces ---
# This will be applied to ALL simulations run by this script.
# Make sure this value aligns with how you've set up your #rx and #rx_steps in your .in files.
FIXED_NUMBER_OF_TRACES = 225 # <--- SET YOUR DESIRED NUMBER OF TRACES HERE

# Define the directory where your generated .in files are located
input_files_dir = "C:/Users/user/gprMax/batch_sim/simulations_full_strategy_split/split_1"

# Define the directory where gprMax should save its output files
output_results_dir = "C:/Users/user/gprMax/batch_sim/outputs_simulations_full"
#os.makedirs(output_results_dir, exist_ok=True)

# Get a list of all .in files in the input directory
input_files = [f for f in os.listdir(input_files_dir) if f.endswith(".in")]
input_files.sort()

print(f"Found {len(input_files)} .in files to simulate.")
print(f"Each simulation will run with -n {FIXED_NUMBER_OF_TRACES} traces.")

# Loop through each input file and run gprMax
for i, input_filename in enumerate(input_files):
    input_filepath = os.path.join(input_files_dir, input_filename)

    print(f"\n--- Simulating file {i+1}/{len(input_files)}: {input_filename} ---")

    # The gprMax command with the fixed -n argument:
    # python -m gprMax path/to/your/input_file.in -n <FIXED_INTEGER> --output-dir=[output_dir]
    command = [
        "python",
        "-m",
        "gprMax",
        input_filepath,
        "-n",
        str(FIXED_NUMBER_OF_TRACES),
        "-gpu"

    ]

    # Optional: Add GPU flag if you're using it
    # command.append("-gpu") # Appends "-gpu" if you want to use GPU, defaults to device 0

    try:
        process = subprocess.run(command, capture_output=False, check=True)
        print(f"Simulation for {input_filename} completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Simulation for {input_filename} failed.")
        print(f"Command: {' '.join(e.cmd)}")
        if e.stdout:
            print(f"Stdout: {e.stdout.decode()}")
        if e.stderr:
            print(f"Stderr: {e.stderr.decode()}")
    except FileNotFoundError:
        print("ERROR: 'python' or 'gprMax' command not found. "
              "Ensure gprMax is installed and your Python environment is correctly set up "
              "(e.g., gprMax conda environment activated).")
    except Exception as e:
        print(f"An unexpected error occurred during simulation of {input_filename}: {e}")

print("\nAll simulations attempted.")