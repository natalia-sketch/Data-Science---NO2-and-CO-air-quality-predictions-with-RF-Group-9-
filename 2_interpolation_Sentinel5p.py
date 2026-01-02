import xarray as xr
import rioxarray
import numpy as np
from scipy.ndimage import generic_filter

da = (
    rioxarray
    .open_rasterio(r"C:\Users\natal\Documents\UCLouvain\Data Science\cleaned-data-datascience-louvain-pollution-2025\sentinel5p\S5P_OFFL_L3__CO_____20240607T065440_20240607T083610_34460_03_020600_20240612T034539_CO_column_number_density.tif")
    .squeeze()
)
arr = da.values

# choose window: 3 -> 3x3 (up to 8 neighbors), 5 -> 5x5 (up to 24 neighbors)
WINDOW = 5
MIN_VALID = 4   # require at least 4 real pixels in the window to fill

def fill_func(window):
    vals = window[~np.isnan(window)]
    if vals.size >= MIN_VALID:
        return vals.mean()
    else:
        return np.nan

footprint = np.ones((WINDOW, WINDOW), dtype=bool)

filled_arr = generic_filter(
    arr,
    function=fill_func,
    footprint=footprint,
    mode="nearest"  # or 'mirror'
)

# now: keep original where it exists, use filled where original is NaN
out_arr = np.where(np.isnan(arr), filled_arr, arr)

filled_da = xr.DataArray(
    out_arr,
    coords=da.coords,
    dims=da.dims,
    attrs=da.attrs,
).rio.write_crs(da.rio.crs)

filled_da.rio.to_raster(r"C:\Users\natal\Documents\UCLouvain\Data Science\Output_Sentinel5p\s5p_localfilled.tif")
