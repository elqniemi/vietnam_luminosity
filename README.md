# Nighttime Light Data Extraction for Vietnam

This Python script automates the process of downloading, extracting, and clipping nighttime light satellite imagery for Vietnam from the Earth Observation Group (EOG) at the Payne Institute for Public Policy.

## Overview

The script:
- Downloads monthly nighttime light data (.tgz files) from the EOG dataset for specified years.
- Extracts the TIF file that contains the term 'rade9h' from each archive.
- Clips the TIF image to the geographic extent of Vietnam.
- Saves the clipped image as a new GeoTIFF file.
- Removes the downloaded and extracted files to save space.

## Prerequisites

To run this script, you will need Python installed on your system along with several Python libraries. This project uses Poetry for dependency management.

### Installing Python

Make sure Python 3.8 or higher is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

### Installing Poetry

Poetry is used to manage dependencies and virtual environments. Install it by following the instructions on the [Poetry website](https://python-poetry.org/docs/#installation).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:elqniemi/vietnam_luminosity.git
   cd vietnam_luminosity
   ```
2. Install dependencies
```bash
poetry install
```

## Configuring the script
Before running the script, you might need to adjust the start and end dates within the script to match the range of data you want to download. Open download.py and modify the following line accordingly:
```python
download_and_process(2012, 3, 2023, 11)
```

## Output
The script will save clipped images to the current directory, naming them in the format vietnam_YYYYMM.tif, where YYYY is the year and MM is the month.

# Running the Nighttime Light Data Extraction Script on Google Colab

Google Colab provides an easy-to-use platform for running Python scripts with access to powerful computing resources. Follow these steps to modify and run the nighttime light data extraction script on Google Colab.

## Step 1: Set Up Your Notebook

1. **Open Google Colab**: Go to [Google Colab](https://colab.research.google.com/) and sign in with your Google account.
2. **Create a New Notebook**: Click on `New Notebook` to create a blank notebook.

## Step 2: Install Required Libraries

Since Google Colab environments are ephemeral, you need to install the required libraries each time you run the notebook. Add and run the following cell at the beginning of your notebook:

```python
!pip install rasterio geopandas requests bs4 lxml
```

## Step 3: Upload the script
1. Prepare the script
2. Upload to colab
    - In colab, click the folder icon
    - Click 'Upload to session storage'
    - Select the download.py file

## Step 4: Modify the script
Google Colab might not have direct support for certain operations like local file downloads to specific paths. Modify file path operations if necessary:
- Ensure any file paths in download.py are adjusted to write to Colab’s working directory, e.g., replace local/path/to/file.tif with ./file.tif.


