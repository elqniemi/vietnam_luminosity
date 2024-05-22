import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterstats import zonal_stats
import pandas as pd
import numpy as np
import tempfile
from netCDF4 import Dataset

def extract_time_from_nc(nc_dataset):
    times = nc_dataset.variables['time'][:]
    return times

def calculate_zonal_stats(raster_path, vector_path):
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        zones = gpd.read_file(vector_path)

        # Reproject zones to raster CRS if necessary
        if zones.crs != raster_crs:
            zones = zones.to_crs(raster_crs)

        # Debugging: check for overlaps
        overlap_count = 0

        stats = []

        for zone in zones.itertuples():
            geom = [zone.geometry.__geo_interface__]
            try:
                out_image, out_transform = mask(src, geom, crop=True)
                if out_image.any():
                    overlap_count += 1
                    zone_stats = zonal_stats(
                        geom,
                        out_image[0],
                        affine=out_transform,
                        nodata=src.nodata,
                        stats=['mean', 'max', 'min', 'median', 'percentile_10', 'percentile_25', 'percentile_75', 'percentile_90']
                    )
                    zone_stats[0]['zone_id'] = zone.Index  # Add zone identifier for reference
                    stats.append(zone_stats[0])
                else:
                    print(f"No overlap for zone {zone.Index}")
            except ValueError as e:
                if "Input shapes do not overlap raster" in str(e):
                    print(f"Zone {zone.Index} does not overlap raster, skipping.")
                else:
                    print(f"Error processing zone {zone.Index}: {e}")
            except Exception as e:
                print(f"Error processing zone {zone.Index}: {e}")

        print(f"Total overlapping zones: {overlap_count}")
    return pd.DataFrame(stats)

def main():
    nc_file = './output/output.nc'  # NetCDF file
    vector_path = 'adm_level_4.gpkg'  # GPKG file for zones
    output_gpkg = 'zonal_statistics_adm4.gpkg'  # Output GPKG file
    
    zones = gpd.read_file(vector_path)
    zones = zones[['osm_id', 'geometry']]

    nc_dataset = Dataset(nc_file, 'r')
    times = extract_time_from_nc(nc_dataset)
    all_stats = []

     # Assuming the variable names are identified as 'lat', 'lon', and 'data_var'
    data_var_name = 'Band1'

    for time_index, time_value in enumerate(times):
        with tempfile.NamedTemporaryFile(suffix='.tif') as tmpfile:
            # Extract the data for the current time step
            data = nc_dataset.variables[data_var_name][time_index, :, :]

            # Replace invalid values with NaN and convert to float32
            data = np.where(np.isfinite(data), data, np.nan).astype(np.float32)

            # Convert negative values to 0, except NoData values
            data = np.where((data < 0) & np.isfinite(data), 0, data)

            # Define the transform based on the dimensions
            transform = rasterio.transform.from_origin(
                nc_dataset.variables['lon'][0],
                nc_dataset.variables['lat'][0],
                nc_dataset.variables['lon'][1] - nc_dataset.variables['lon'][0],
                nc_dataset.variables['lat'][1] - nc_dataset.variables['lat'][0]
            )

            # Create a temporary raster file
            with rasterio.open(
                tmpfile.name,
                'w',
                driver='GTiff',
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                crs='EPSG:3857',
                transform=transform
            ) as dst:
                dst.write(data, 1)
            
            # Calculate zonal stats on the temporary file
            stats_df = calculate_zonal_stats(tmpfile.name, vector_path)
            if not stats_df.empty:
                stats_df['timestamp'] = pd.to_datetime(str(time_value))
                all_stats.append(stats_df)

    combined_stats_df = pd.concat(all_stats).reset_index(drop=True)

    # Create a new GeoDataFrame by duplicating the zones for each time period
    combined_zones_stats = gpd.GeoDataFrame(pd.concat([zones] * len(times), ignore_index=True))

    for col in combined_stats_df.columns:
        if col != 'osm_id':
            combined_zones_stats[col] = combined_stats_df[col]

    combined_zones_stats.to_file(output_gpkg, layer='zonal_stats', driver="GPKG")

   
if __name__ == "__main__":
    main()

