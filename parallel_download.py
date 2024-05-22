import os
import requests
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import box
import tarfile
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import concurrent.futures
import pandas as pd

def scrape_url(year, month):
    index_url = f"https://eogdata.mines.edu/nighttime_light/monthly/v10/{year}/{year}{month:02d}/vcmslcfg/"
    try:
        response = requests.get(index_url)
        if response.status_code != 200:
            print(f"Failed to access {index_url} with status code {response.status_code}")
            return None
        soup = BeautifulSoup(response.content, 'lxml')
        search_pattern = f"SVDNB_npp_{year}{month:02d}01-{year}{month:02d}"
        for link in soup.find_all('a'):
            href = link.get('href')
            if href.startswith(search_pattern) and '75N060E' in href and href.endswith('.tgz'):
                return f"{index_url}{href}"
        print(f"No matching file found for {year}-{month:02d}")
    except Exception as e:
        print(f"Error while scraping URL for {year}-{month:02d}: {e}")
    return None

def download_and_process_file(year, month, vietnam_bounds):
    file_url = scrape_url(year, month)
    if not file_url:
        return None

    print(f"Downloading from {file_url}")
    try:
        response = requests.get(file_url, stream=True)
        if response.status_code == 200:
            tgz_path = f"{year}{month:02d}.tgz"
            with open(tgz_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {tgz_path}")

            with tarfile.open(tgz_path, 'r:gz') as tar:
                tif_path = None
                for member in tar.getmembers():
                    if 'rade9h.tif' in member.name:
                        tar.extract(member)
                        tif_path = member.name
                        break
                if tif_path:
                    print(f"Extracted {tif_path}")
                    with rasterio.open(tif_path) as src:
                        out_image, out_transform = mask(src, [vietnam_bounds], crop=True)
                        out_meta = src.meta.copy()
                        out_meta.update({
                            "driver": "GTiff",
                            "height": out_image.shape[1],
                            "width": out_image.shape[2],
                            "transform": out_transform
                        })

                        clipped_tif_path = f"vietnam_{year}{month:02d}.tif"
                        with rasterio.open(clipped_tif_path, "w", **out_meta) as dest:
                            dest.write(out_image[0], 1)
                        print(f"Clipped to {clipped_tif_path}")

                        # Extract 'cf_cvg' and 'cvg' values
                        cf_cvg = out_image[0].mean()  # Example of calculating mean value
                        cvg = out_image[0].std()  # Example of calculating standard deviation

                        os.remove(tgz_path)
                        os.remove(tif_path)

                        return (f"{year}{month:02d}", cf_cvg, cvg)
                else:
                    print("No rade9h.tif file found in the archive.")
        else:
            print(f"Failed to download file with status code {response.status_code}")
    except Exception as e:
        print(f"Error during download and processing for {year}-{month:02d}: {e}")
    return None

def download_and_process(start_year, start_month, end_year, end_month):
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1)
    current_date = start_date

    # Define the geographic bounds of Vietnam (approximate bounding box)
    vietnam_bounds = box(102.14441, 8.19304, 109.46917, 23.39211)

    date_list = []
    while current_date <= end_date:
        date_list.append((current_date.year, current_date.month))
        current_date += relativedelta(months=1)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(download_and_process_file, year, month, vietnam_bounds) for year, month in date_list]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    # Save results to a CSV
    df = pd.DataFrame(results, columns=["Date", "cf_cvg", "cvg"])
    df.to_csv("vietnam_nighttime_light_coverage.csv", index=False)
    print("Data saved to vietnam_nighttime_light.csv")

# Usage
download_and_process(2014, 1, 2023, 12)

