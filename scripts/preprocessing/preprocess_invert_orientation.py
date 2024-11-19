"""Simple script to change the order of files.

Used to transform file names (xxx_001.tiff) to reverse their order, to go from
caudo-rostral to rostro-caudal.

"""

import os

import numpy as np

input_directory = "/path/to/directory"  # path to tiff files
output_directory = "/path/to/directory/new"  # output directory, must be different
file_extension = ".ome.tiff"  # file extension with dots
file_prefix = "mouse0_"  # full prefix before the numbering digits
ndigits = 3  # number of digits for numbering (both inputs and outputs)
dry_run = True  # if True, do not actually rename the files

list_files = [
    filename
    for filename in os.listdir(input_directory)
    if filename.startswith(file_prefix) & filename.endswith(file_extension)
]

nfiles = len(list_files)
new_numbers = np.arange(nfiles, 0, -1)

if not os.path.isdir(output_directory):
    os.mkdir(output_directory)

for oldi, newi in enumerate(new_numbers):
    old_name = f"{file_prefix}{str(oldi + 1).zfill(ndigits)}{file_extension}"
    new_name = f"{file_prefix}{str(newi).zfill(ndigits)}{file_extension}"
    old_file = os.path.join(input_directory, old_name)
    new_file = os.path.join(output_directory, new_name)

    print(f"rename: {old_name} -> {new_name}")
    if not dry_run:
        os.rename(old_file, new_file)
