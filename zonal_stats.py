import os
import glob
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterstats import zonal_stats
import pandas as pd

def get_tif_files(folder):
    return glob.glob(os.path.join(folder, '*.tif'))

def extract_date_from_filename(filename):
    basename = os.path.basename(filename)
    date_str = basename.split('_')[-1].split('.')[0]
    year = date_str[:4]
    month = date_str[4:6]
    return year, month, f"{year}-{month}"

def calculate_zonal_stats(raster_path, vector_path):
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        zones = gpd.read_file(vector_path)
        
        # Reproject zones to raster CRS if necessary
        if zones.crs != raster_crs:
            zones = zones.to_crs(raster_crs)
        
        stats = []

        for zone in zones.itertuples():
            geom = [zone.geometry.__geo_interface__]
            try:
                out_image, out_transform = mask(src, geom, crop=True)
                zone_stats = zonal_stats(
                    geom,
                    out_image[0],
                    affine=out_transform,
                    nodata=src.nodata,
                    stats=['mean', 'max', 'min', 'median', 'percentile_10', 'percentile_25', 'percentile_75', 'percentile_90']
                )
                zone_stats[0]['zone_id'] = zone.Index  # Add zone identifier for reference
                stats.append(zone_stats[0])
            except ValueError as e:
                if "Input shapes do not overlap raster" in str(e):
                    print(f"Zone {zone.Index} does not overlap raster, skipping.")
                else:
                    print(f"Error processing zone {zone.Index}: {e}")
            except Exception as e:
                print(f"Error processing zone {zone.Index}: {e}")

    return pd.DataFrame(stats)

def main():
    folder = './noncorrected/'  # Folder containing .tif files
    vector_path = 'adm_level_3.gpkg'  # GPKG file for zones
    output_gpkg = 'zonal_statistics_adm4.gpkg'  # Output GPKG file

    tif_files = get_tif_files(folder)
    zones = gpd.read_file(vector_path)
    all_stats = []

    for tif_file in tif_files:
        year, month, timestamp = extract_date_from_filename(tif_file)
        stats_df = calculate_zonal_stats(tif_file, vector_path)
        if not stats_df.empty:
            stats_df['year'] = year
            stats_df['month'] = month
            stats_df['timestamp'] = timestamp
            all_stats.append(stats_df)

    combined_stats_df = pd.concat(all_stats).reset_index(drop=True)
    
    # Create a new GeoDataFrame by duplicating the zones for each time period
    combined_zones_stats = gpd.GeoDataFrame(pd.concat([zones] * len(tif_files), ignore_index=True))
    
    for col in combined_stats_df.columns:
        if col != 'zone_id':
            combined_zones_stats[col] = combined_stats_df[col]
    
    combined_zones_stats.to_file(output_gpkg, layer='zonal_stats', driver="GPKG")

if __name__ == "__main__":
    main()


