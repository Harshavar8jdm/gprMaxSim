import os
import math


materials = [
    {"first": 1, "second": 0, "third": 1, "fourth": 0, "name": "air"},
    {"first": 6, "second": 0, "third": 1, "fourth": 0, "name": "half_space"},
    {"first": 9, "second": 0, "third": 1, "fourth": 0, "name": "wet_concrete"},
    {"first": 1, "second": 0.001, "third": 0.001, "fourth": 5, "name": "asphalt"},
    {"first": 1, "second": 0.01, "third": 0.01, "fourth": 6, "name": "brick"},
    {"first": 1, "second": 0.0001, "third": 0.0001, "fourth": 5, "name": "granite"},
    {"first": 1, "second": 0.00001, "third": 0.00001, "fourth": 3, "name": "wood"},
    {"first": 1, "second": 0.05, "third": 0.05, "fourth": 10, "name": "clay"},
    {"first": 1, "second": 0, "third": 0, "fourth": 3, "name": "pvc"},
    {"first": 1, "second": 10000000, "third": 10000000, "fourth": 0, "name": "steel"},
    {"first": 1, "second": 0.0001, "third": 0.0001, "fourth": 4, "name": "dry_sand"},
    {"first": 1, "second": 0.1, "third": 0.1, "fourth": 20, "name": "wet_sand"},
    {"first": 1, "second": 0.0001, "third": 0.0001, "fourth": 7, "name": "limestone"},
    {"first": 1, "second": 0.0001, "third": 0.0001, "fourth": 7, "name": "basalt"},
    {"first": 1, "second": 0.02, "third": 0.02, "fourth": 15, "name": "shale"},
    {"first": 1, "second": 0.00001, "third": 0.00001, "fourth": 6, "name": "marble"},
    {"first": 1, "second": 0.0001, "third": 0.0001, "fourth": 4, "name": "gypsum"},
    {"first": 1, "second": 0.000001, "third": 0.000001, "fourth": 6, "name": "glass"},
    {"first": 1, "second": 0.00001, "third": 0.00001, "fourth": 3.2, "name": "ice"},
    {"first": 1, "second": 0.000001, "third": 0.000001, "fourth": 1.5, "name": "snow"},
    {"first": 1, "second": 0, "third": 0, "fourth": 1, "name": "vaccum"},
    {"first": 1, "second": 0, "third": 0.0116, "fourth": 2.94, "name": "plasterboard"},
    {"first": 1, "second": 0, "third": 0.0116, "fourth": 2.94, "name": "plasterboard"},
    {"first": 1, "second": 0.0116, "third": 0.0005, "fourth": 1.5, "name": "ceilingboard"},
    {"first": 1, "second": 0.0005, "third": 0.0217, "fourth": 2.58, "name": "chipboard"},
    {"first": 1, "second": 0.0217, "third": 0.33, "fourth": 2.71, "name": "plywood"},
    {"first": 1, "second": 0.33, "third": 0.0044, "fourth": 3.66, "name": "floorboard"},
    {"first": 1, "second": 0.33, "third": 0.0044, "fourth": 3.66, "name": "floorboard"},
    {"first": 1, "second": 10000000, "third": 1e7 , "fourth": 0, "name": "metal"},

]



# Define parameter ranges
radii = [round(r, 2) for r in [x / 100 for x in range(5, 85, 5)]]  # 5cm to 80cm step 5cm
depths = [round(d, 2) for d in [x / 100 for x in range(10, 510, 10)]]  # 10cm to 500cm step 10cm
angles = list(range(15, 91, 15))  # 15° to 90° step 15°
materials = [{"first": 1, "second": 0.05, "third": 0.05, "fourth": 10, "name": "clay"}]
media_top_layers = ["asphalt", "concrete", "concrete_rebars"]
media = media_top_layers + ["none"]  # Include the "no top layer" case

def format_value(val):
    """Convert float like 0.05 -> '0_05', 1.25 -> '1_25' for safe filenames."""
    return str(val).replace(".", "_")

def generate_simulation_files():
    base_dir = "simulations_full_strategyy"
    os.makedirs(base_dir, exist_ok=True)

    count = 0

    for current_media in media:
        for material in materials:
            for radius in radii:
                for depth in depths:
                    for angle in angles:
                        # Convert angle to radians
                        angle_rad = math.radians(angle)

                        # Starting point of cylinder
                        x0, y0 = 6.0, depth

                        # End point calculated using trigonometry
                        pipe_len = 1.0  # meters
                        x1 = round(x0 + pipe_len * math.cos(angle_rad), 3)
                        y1 = round(y0 + pipe_len * math.sin(angle_rad), 3)

                        # Create filename
                        r_str = format_value(radius)
                        d_str = format_value(depth)
                        a_str = str(angle)
                        filename = f"{base_dir}/gpr_{material['name']}_r{r_str}_d{d_str}_a{a_str}_.in"


                        # Write the .in file
                        with open(filename, "w") as f:
                            f.write(f"#title: Media={current_media}, Material={material}, Radius={radius}, Depth={depth}, Angle={angle}\n")
                            f.write("#domain: 15 11 0.002\n")
                            f.write("#dx_dy_dz: 0.0075 0.0075 0.002\n")
                            f.write("#time_window: 50e-9\n\n")
                            f.write("#pml_cells: 10 5 0 5 5 0\n\n")
                            f.write("#material: 6 0 1 0 half_space\n")
                            f.write(f"#material: {material['first']} {material['second']} {material['third']} {material['fourth']} {material['name']}\n\n")
                            f.write("#waveform: ricker 1 500e6 my_ricker\n")
                            f.write("#hertzian_dipole: z 0.2 0.170 0 my_ricker\n")
                            f.write("#rx: 0.40 0.170 0\n")
                            f.write("#src_steps: 0.04 0 0\n")
                            f.write("#rx_steps: 0.04 0 0\n")
                            f.write("#box: 0 0 0 15 10 0.002 half_space\n\n")
                            f.write(f"#cylinder: {x0} {y0} 0 {x1} {y1} 0.002 {radius} {material['name']}\n")

                        count += 1

    print(f"Generated {count} files in '{base_dir}'")

if __name__ == "__main__":
    generate_simulation_files()
