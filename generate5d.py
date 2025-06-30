import os
import math

# Define parameter ranges
radii = [round(r, 2) for r in [x / 100 for x in range(5, 85, 5)]]  # 5cm to 80cm
depths = [round(d, 2) for d in [x / 100 for x in range(10, 310, 10)]]  # 10cm to 3.10m
angles = list(range(15, 76, 15))  # 15° to 60°

materials = ["clay", "wet_concrete", "pec", "pvc"]  # order corresponds to splits

def format_value(val):
    return str(val).replace(".", "_")

def generate_simulation_files():
    base_dir = "simulations_full_strategy_split"
    os.makedirs(base_dir, exist_ok=True)

    # Create split directories, one per material
    split_dirs = {}
    for i, material in enumerate(materials):
        split_path = os.path.join(base_dir, f"split_{i+1}")
        os.makedirs(split_path, exist_ok=True)
        split_dirs[material] = split_path  # map material to its split folder

    count = 0
    for material in materials:
        folder = split_dirs[material]  # folder for this material (split)

        for radius in radii:
            for depth in depths:
                for angle in angles:
                    angle_rad = math.radians(angle)
                    x0, y0 = 6.0, depth
                    pipe_len = 1.0
                    x1 = round(x0 + pipe_len * math.cos(angle_rad), 3)
                    y1 = round(y0 + pipe_len * math.sin(angle_rad), 3)

                    r_str = format_value(radius)
                    d_str = format_value(depth)
                    a_str = str(angle)

                    filename = os.path.join(folder, f"gpr_{material}_r{r_str}_d{d_str}_a{a_str}_.in")

                    with open(filename, "w") as f:
                        f.write(f"#title: Material={material}, Radius={radius}, Depth={depth}, Angle={angle}\n")
                        f.write("#domain: 15 11 0.002\n")
                        f.write("#dx_dy_dz: 0.0075 0.0075 0.002\n")
                        f.write("#time_window: 50e-9\n\n")
                        f.write("#pml_cells: 10 5 0 5 5 0\n\n")
                        f.write("#material: 6 0 1 0 half_space\n")
                        f.write("#material: 1 0 1 0 air\n")
                        f.write("#material: 9 0 1 0 wet_concrete\n")
                        f.write("#material: 30 0 1 0 clay\n")
                        f.write("#material: 3.8 10e-6 1 0 pvc\n")
                        f.write("#waveform: ricker 1 500e6 my_ricker\n")
                        f.write("#hertzian_dipole: z 0.2 0.170 0 my_ricker\n")
                        f.write("#rx: 0.40 0.170 0\n")
                        f.write("#src_steps: 0.04 0 0\n")
                        f.write("#rx_steps: 0.04 0 0\n")
                        f.write("#box: 0 0 0 15 10 0.002 half_space\n\n")
                        f.write(f"#cylinder: {x0} {y0} 0 {x1} {y1} 0.002 {radius} {material}\n")
                        f.write("#output_dir: C:/Users/user/gprMax/batch_sim/outputs_simulations_full\n")

                    count += 1

    print(f"Generated {count} files across {len(materials)} folders in '{base_dir}'")

if __name__ == "__main__":
    generate_simulation_files()
