import os
import rasterio
import numpy as np
from netCDF4 import Dataset, date2num
from datetime import datetime
from glob import glob

# Define the directory containing the .tif files
input_dir = './'
output_file = 'output.nc'

# Get list of all .tif files in the directory
tif_files = sorted(glob(os.path.join(input_dir, '*.tif')))

# Extract dates from filenames
dates = [os.path.basename(f)[-10:-4] for f in tif_files]
times = [datetime.strptime(date, '%Y%m') for date in dates]

# Read the first .tif file to get metadata
with rasterio.open(tif_files[0]) as src:
    meta = src.meta
    height, width = src.shape
    transform = src.transform

# Create NetCDF file
with Dataset(output_file, 'w', format='NETCDF4') as ncfile:
    # Create dimensions

    print(f'Creating NetCDF file: {output_file}')
    ncfile.createDimension('time', len(tif_files))
    ncfile.createDimension('lat', height)
    ncfile.createDimension('lon', width)
    
    # Create variables
    times_var = ncfile.createVariable('time', 'f8', ('time',))
    lats = ncfile.createVariable('lat', 'f4', ('lat',))
    lons = ncfile.createVariable('lon', 'f4', ('lon',))
    luminosity = ncfile.createVariable('luminosity', 'f4', ('time', 'lat', 'lon'), zlib=True)
    
    # Set variable attributes
    lats.units = 'degrees_north'
    lons.units = 'degrees_east'
    luminosity.units = 'luminosity'
    times_var.units = 'days since 1900-01-01 00:00:00.0'
    times_var.calendar = 'gregorian'
    
    # Set global attributes
    ncfile.description = 'Luminosity data from .tif files'
    
    # Assign latitude and longitude values
    lats[:] = np.linspace(transform[5] + transform[4] * 0.5, transform[5] + transform[4] * (height - 0.5), height)
    lons[:] = np.linspace(transform[2] + transform[0] * 0.5, transform[2] + transform[0] * (width - 0.5), width)
    
    # Assign time values
    times_num = date2num(times, units=times_var.units, calendar=times_var.calendar)
    times_var[:] = times_num
    
    # Process each .tif file and write to NetCDF
    for i, tif_file in enumerate(tif_files):
        print(f'Processing file: {tif_file}')
        with rasterio.open(tif_file) as src:
            luminosity_data = src.read(1)
            luminosity[i, :, :] = luminosity_data
    
    print(f'Successfully created NetCDF file: {output_file}')

