import os

radii = [
    {"radius": 0.050}, {"radius": 0.100}, {"radius": 0.150}, {"radius": 0.200},
    {"radius": 0.250}, {"radius": 0.300}, {"radius": 0.350}, {"radius": 0.400},
    {"radius": 0.450}, {"radius": 0.500}
]

depths = [
    {"depth": 1.050}, {"depth": 1.100}, {"depth": 1.150}, {"depth": 1.200},
    {"depth": 1.250}, {"depth": 1.300}, {"depth": 1.350}, {"depth": 1.400},
    {"depth": 1.450}, {"depth": 1.500}, {"depth": 1.550}, {"depth": 1.600},
    {"depth": 1.650}, {"depth": 1.700}, {"depth": 1.750}, {"depth": 1.800},
    {"depth": 1.850}, {"depth": 1.900}, {"depth": 1.950}, {"depth": 2.000}
]

def format_value(val):
    """Converts 0.05 -> '005', 1.250 -> '1250' etc. Safe for filenames."""
    return str(val).replace(".", "_")

def radii_depth_loop():
    base_dir = "simulations_radii_depth_pvc"
    os.makedirs(base_dir, exist_ok=True)

    for rad in radii:
        for dep in depths:
            r_str = format_value(rad['radius'])   # e.g., 0.05 -> '0_05'
            d_str = format_value(dep['depth'])    # e.g., 1.25 -> '1_25'
            filename = f"{base_dir}/cylinder_r{r_str}d{d_str}_.in"


            with open(filename, "w") as f:
                f.write(f"#title: GPR simulation for cylinder r={rad['radius']} d={dep['depth']}\n")
                f.write("#domain: 15 11 0.002\n")
                f.write("#dx_dy_dz: 0.0075 0.0075 0.002\n")
                f.write("#time_window: 50e-9\n\n")
                f.write("#pml_cells: 10 5 0 5 5 0\n\n")
                f.write("#material: 6 0 1 0 half_space\n\n")
                f.write("#material: 3.4 1e-5 1 0 pvc\n\n")
                f.write("#waveform: ricker 1 500e6 my_ricker\n\n")
                f.write("#hertzian_dipole: z 0.2 0.170 0 my_ricker\n")
                f.write("#rx: 0.40 0.170 0\n")
                f.write("#src_steps: 0.04 0 0\n")
                f.write("#rx_steps: 0.04 0 0\n")
                f.write("#box: 0 0 0 15 10 0.002 half_space\n\n")
                f.write(f"#cylinder: 6 {dep['depth']} 0 6 {dep['depth']} 0.002 {rad['radius']} pvc")

    print(f"Generated {len(radii) * len(depths)} simulation files in '{base_dir}'")

if __name__ == "__main__":
    radii_depth_loop()