#!/bin/bash

# Directory containing .tif files
input_dir="./noncorrected"
output_file="output/output.nc"
temp_dir="temp_nc_files"

mkdir -p "$temp_dir"

# Create a list of individual NetCDF files
nc_files=()

# Process each .tif file
for tif_file in "$input_dir"/*.tif; do
    # Extract base name
    base_name=$(basename "$tif_file" .tif)
    
    # Extract date components (assuming format vietnam_YYYYMM)
    year=${base_name:8:4}
    month=${base_name:12:2}
    
    # Convert to NetCDF using gdal_translate
    nc_temp_file="$temp_dir/${base_name}.nc"
    gdal_translate -of netCDF "$tif_file" "$nc_temp_file"
    
    # Fix anomalies by setting values > 60 to NaN
    #cdo -setrtomiss,500,99999999 "$nc_temp_file" "${nc_temp_file}_clean"
    # set below 0 to NaN 
    cdo -setrtomiss,-9999,0 "$nc_temp_file" "${nc_temp_file}_clean"

    # Remove the uncleaned file
    rm "$nc_temp_file"
    
    # Append cleaned file to the list
    nc_files+=("${nc_temp_file}_clean")
    
    # Set time information
    cdo -setdate,${year}-${month}-01 -setcalendar,standard "${nc_temp_file}_clean" "${nc_temp_file}_time"
    
    # Update the list with the time-adjusted file
    nc_files[-1]="${nc_temp_file}_time"
    
    # Remove the intermediate clean file
    rm "${nc_temp_file}_clean"
done

# Merge all individual NetCDF files into one with a time dimension
cdo -O mergetime "${nc_files[@]}" "$output_file"

# Clean up temporary files
rm -r "$temp_dir"

echo "Conversion completed. Output saved to $output_file"

