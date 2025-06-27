import os


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

# Radii from 0.01 to 0.5 (inclusive) with 0.01 steps
radii = [round(r, 3) for r in [i * 0.01 for i in range(1, 51)]]

# Output folder
output_dir = "simulations_material_radii"
os.makedirs(output_dir, exist_ok=True)

def generate_inputs():
    for mat in materials:
        for radius in radii:
            filename = f"{mat['name']}_{radius:.3f}.in"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                f.write(f"#title: GPR simulation for {mat['name']} with radius {radius}\n")
                f.write("#domain: 1.0 0.5 0.01\n")
                f.write("#dx_dy_dz: 0.01 0.01 0.01\n")
                f.write("#time_window: 20e-9\n\n")
                f.write("#waveform: ricker 1 1.0e9 my_ricker\n\n")
                f.write("#hertzian_dipole: z 0.18 0.4 0 my_ricker\n")
                f.write("#rx: 0.2 0.4 0\n")

                # Half-space as background material
                f.write("material: 6 0 1 0 half_space\n")
                f.write(f"box: 0 1 0 0.5 0 0.01 half_space\n\n")

                # Cylinder of specified material and radius
                f.write(f"material: {mat['first']} {mat['second']} {mat['third']} {mat['fourth']} {mat['name']}\n")
                f.write(f"cylinder: 0.4 0.3 0.0  0.4 0.3 0.002 {radius} {mat['name']}\n")

    print(f"Generated {len(materials) * len(radii)} simulation files in '{output_dir}'")

if __name__ == "__main__":
    generate_inputs()
