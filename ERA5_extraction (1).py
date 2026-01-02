# final_fast_era5.py
import geopandas as gpd
from rasterstats import zonal_stats
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import re
import rasterio
import warnings
warnings.filterwarnings("ignore")  # removes NodataWarning

# === PATHS ===
GRID_PATH = Path(r"D:\GEM\UCLouvain\Sem1\Datascience\Datas\india_grid_10x10km.geojson")
TIF_DIR   = Path(r"D:\GEM\UCLouvain\Sem1\Datascience\Datas\weather-era5")
OUT_CSV   = Path(r"D:\GEM\UCLouvain\Sem1\Datascience\Datas\era5_extracted.csv")

BANDS = {1:"tmean",2:"tmin",3:"tmax",4:"prcp",5:"wind10m",6:"sp",7:"swdown",8:"imerg",9:"cloud"}

print("Loading grid...")
grid = gpd.read_file(GRID_PATH).to_crs(epsg=4326)
print(f"Grid: {len(grid):,} cells")

records = []
tif_files = sorted(TIF_DIR.glob("india_monthly_climate_*.tif"))

print(f"Found {len(tif_files)} TIFs → starting extraction...")
for tif in tqdm(tif_files, desc="TIFs"):
    m = re.search(r"_(\d{6})\.tif$", tif.name)
    if not m: continue
    month = int(m.group(1))

    with rasterio.open(tif) as src:
        nodata = src.nodata if src.nodata is not None else -9999
        for b, name in BANDS.items():
            if b > src.count: continue
            stats = zonal_stats(
                grid["geometry"], str(tif),
                stats="mean", band=b, nodata=nodata, all_touched=True
            )
            for i, s in enumerate(stats):
                if s["mean"] is not None:
                    records.append({
                        "grid_id": grid.iloc[i]["grid_id"],
                        "month": month,
                        "variable": name,
                        "value": round(s["mean"], 6)
                    })

df = pd.DataFrame(records)
df = df.sort_values(["grid_id", "month", "variable"]).reset_index(drop=True)
df.to_csv(OUT_CSV, index=False)

print(f"\nFINISHED! {len(df):,} rows saved to:\n   {OUT_CSV}")
print(f"Time estimate: ~20s per file → {len(tif_files)*0.35:.0f} seconds total")