from pyhdf.SD import SD, SDC
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
from cartopy.io import DownloadWarning  # Import for warning suppression

# Suppress Cartopy download warnings
warnings.filterwarnings("ignore", category=DownloadWarning)

# Path to your MODIS HDF file
hdf_file = r"D:\GEM\UCLouvain\Sem1\Datascience\Datas\MODIS\MOD08_M3.A2025001.061.2025035173143.hdf"

# Open the HDF file
try:
    hdf = SD(hdf_file, SDC.READ)
    print("File opened successfully.")
except Exception as e:
    print(f"Error opening file: {e}")
    import traceback
    traceback.print_exc()
    exit()

# List all datasets (SDSs) with detailed output
print("Available datasets:")
try:
    sds_list = hdf.datasets()
    for name, info in sds_list.items():
        print(f"  {name}: {info}")
except Exception as e:
    print(f"Error listing datasets: {e}")
    traceback.print_exc()
    hdf.end()
    exit()

# Specify the AOD dataset
dataset_name = 'Aerosol_Optical_Depth_Land_QA_Mean_Mean'
if dataset_name not in sds_list:
    print(f"Dataset '{dataset_name}' not found. Check the list above.")
    hdf.end()
    exit()

# Extract the AOD dataset
try:
    sds = hdf.select(dataset_name)
    data = sds.get()  # Read as NumPy array
    print("Data shape:", data.shape)
    print("Data attributes:", sds.attributes())
except Exception as e:
    print(f"Error processing dataset: {e}")
    traceback.print_exc()
    exit()

# Get attributes for calibration
try:
    attrs = sds.attributes()
    scale_factor = attrs.get('scale_factor', 0.001)
    add_offset = attrs.get('add_offset', 0.0)
    fill_value = attrs.get('_FillValue', -9999)
except Exception as e:
    print(f"Error getting attributes: {e}")
    traceback.print_exc()
    exit()

# Apply calibration and mask invalid values
try:
    data = (data - add_offset) * scale_factor
    data = np.ma.masked_where(data == fill_value, data)
except Exception as e:
    print(f"Error calibrating data: {e}")
    traceback.print_exc()
    exit()

# Select the 0.55 micron layer
try:
    data_2d = data[1, :, :]  # 0.55 micron (middle wavelength)
    print(f"2D Data shape: {data_2d.shape}, Min: {np.nanmin(data_2d):.3f}, Max: {np.nanmax(data_2d):.3f}")
except Exception as e:
    print(f"Error selecting 2D data: {e}")
    traceback.print_exc()
    exit()

# Extract XDim and YDim as coordinates
try:
    xdim_sds = hdf.select('XDim')
    ydim_sds = hdf.select('YDim')
    lon = xdim_sds.get()  # Longitude values
    lat = ydim_sds.get()  # Latitude values
    print(f"XDim shape: {lon.shape}, Values: {lon}")
    print(f"YDim shape: {lat.shape}, Values: {lat}")
    
    # Create 2D grid
    lon, lat = np.meshgrid(lon, lat)
    print("Using XDim and YDim as coordinates.")
except Exception as e:
    print(f"Error extracting XDim/YDim coordinates: {e}")
    traceback.print_exc()
    print("XDim/YDim not found or invalid. Using fallback grid.")
    lat = np.linspace(-90, 90, 180, endpoint=False)  # 180 points
    lon = np.linspace(-180, 180, 360, endpoint=False)  # 360 points
    lon, lat = np.meshgrid(lon, lat)

# Verify grid matches data shape
try:
    if data_2d.shape != (180, 360):
        print(f"Warning: Expected (180, 360) data, got {data_2d.shape}. Adjusting may be needed.")
        data_2d = data_2d[:180, :360]  # Truncate if larger
except Exception as e:
    print(f"Error verifying grid: {e}")
    traceback.print_exc()
    exit()

# Create map plot
try:
    plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    im = ax.pcolormesh(lon, lat, data_2d, transform=ccrs.PlateCarree(), cmap='YlOrRd',
                       vmin=0, vmax=1.0)  # Typical AOD range
    plt.colorbar(im, ax=ax, label='Aerosol Optical Depth (0.55 micron)')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=True)
    ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())  # Explicit global bounds
    plt.title('MODIS AOD - Jan 2025')
    plt.show()
except Exception as e:
    print(f"Error creating plot: {e}")
    traceback.print_exc()
    exit()

# Cleanup
try:
    if 'xdim_sds' in locals(): xdim_sds.endaccess()
    if 'ydim_sds' in locals(): ydim_sds.endaccess()
    sds.endaccess()
    hdf.end()
except Exception as e:
    print(f"Error during cleanup: {e}")
    traceback.print_exc()