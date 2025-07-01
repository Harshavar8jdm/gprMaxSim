# Copyright (C) 2015-2023: The University of Edinburgh
#                 Authors: Craig Warren and Antonis Giannopoulos
#
# This file is part of gprMax.
#
# gprMax is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gprMax is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gprMax.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os

import h5py
import numpy as np
import matplotlib.pyplot as plt

from gprMax.exceptions import CmdInputError
from .outputfiles_merge import get_output_data


def mpl_plot(filename, outputdata, dt, rxnumber, rxcomponent):
    """Creates and saves a plot (with matplotlib) of the B-scan."""
    
    (path, base_filename) = os.path.split(filename)

    fig = plt.figure(num=base_filename + ' - rx' + str(rxnumber),
                     figsize=(20, 10), facecolor='w', edgecolor='w')
    plt.imshow(outputdata,
               extent=[0, outputdata.shape[1], outputdata.shape[0] * dt, 0],
               interpolation='nearest', aspect='auto', cmap='grey',
               vmin=-np.amax(np.abs(outputdata)), vmax=np.amax(np.abs(outputdata)))
    plt.xlabel('Trace number')
    plt.ylabel('Time [s]')

    cb = plt.colorbar()
    if 'E' in rxcomponent:
        cb.set_label('Field strength [V/m]')
    elif 'H' in rxcomponent:
        cb.set_label('Field strength [A/m]')
    elif 'I' in rxcomponent:
        cb.set_label('Current [A]')

    save_dir = os.path.join(os.getcwd(), 'saved_bscans')  
    os.makedirs(save_dir, exist_ok=True)  
    save_filename = f"{os.path.splitext(base_filename)[0]}_rx{rxnumber}_{rxcomponent}.png"  
    save_path = os.path.join(save_dir, save_filename)  
    fig.savefig(save_path, dpi=300, bbox_inches='tight')  
    print(f"[✔] Saved B-scan image to: {save_path}")  

    return plt


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Plots a B-scan image.', 
                                     usage='cd gprMax; python -m tools.plot_Bscan outputfile output')
    parser.add_argument('outputfile', help='name of output file including path')
    parser.add_argument('rx_component', help='name of output component to be plotted', 
                        choices=['Ex', 'Ey', 'Ez', 'Hx', 'Hy', 'Hz', 'Ix', 'Iy', 'Iz'])
    args = parser.parse_args()

    # Open output file and read number of outputs (receivers)
    f = h5py.File(args.outputfile, 'r')
    nrx = f.attrs['nrx']
    f.close()

    # Check there are any receivers
    if nrx == 0:
        raise CmdInputError('No receivers found in {}'.format(args.outputfile))

    # Create output folder
    output_dir = os.path.join(os.getcwd(), 'saved_plots')
    os.makedirs(output_dir, exist_ok=True)

    for rx in range(1, nrx + 1):
        outputdata, dt = get_output_data(args.outputfile, rx, args.rx_component)
        plthandle = mpl_plot(args.outputfile, outputdata, dt, rx, args.rx_component)

        # Create output filename
        filename_base = os.path.basename(args.outputfile).replace('__merged.out', '')
        save_path = os.path.join(output_dir, f'{filename_base}_rx{rx}_{args.rx_component}.png')

        # Save the figure
        plthandle.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Plot saved: {save_path}")

    # Optional: Comment this out if you don’t want the GUI plot to open
    # plthandle.show()

