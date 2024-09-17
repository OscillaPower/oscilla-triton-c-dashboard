import os

import pandas as pd

import numpy as np
import mhkit
import requests
import xarray as xr

from Logger import Logger


# Download and parse CDIP nc file into wave QOI
class CDIPRealTimeParser:
    def __init__(self, station_id):
        self.station_id = station_id
        self.ndbc_thredds_url = f"https://thredds.cdip.ucsd.edu/thredds/fileServer/cdip/realtime/{self.station_id}p1_rt.nc"
        self.logger = Logger()

    def download_nc_file(self):
        """Download the nc file using requests and save it locally."""
        try:
            local_filename = f"{self.station_id}_realtime.nc"
            with requests.get(self.ndbc_thredds_url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return local_filename
        except Exception as e:
            self.logger.error(
                __name__, f"Download {self.ndbc_thredds_url} failed with error {e}"
            )
            return None

    def parse_latest_nc_file(self):
        """Download, parse the nc file, and delete it after processing."""
        local_nc_file = self.download_nc_file()
        if not local_nc_file:
            return None, None

        try:
            ds = xr.open_dataset(local_nc_file)

            wave_energy_density = ds.waveEnergyDensity.to_pandas()
            station_depth = float(ds.metaWaterDepth.values)

            df = wave_energy_density
            df.columns = [float(col) for col in df.columns]
            df = df.T

            Hm_0 = mhkit.wave.resource.significant_wave_height(df)
            T_e = mhkit.wave.resource.energy_period(df)
            J = mhkit.wave.resource.energy_flux(df, station_depth)
            T_avg = mhkit.wave.resource.average_crest_period(df)
            T_m = mhkit.wave.resource.average_wave_period(df)
            T_p = mhkit.wave.resource.peak_period(df)
            T_z = mhkit.wave.resource.average_zero_crossing_period(df)

            # Join all columns in "other" with Hm_0 using the index
            result_df = Hm_0.join([T_z, T_avg, T_m, T_p, T_e, J], how="left")

            result_df = result_df.add_prefix("Spectral_")

            result_df["WMI_waveHs"] = ds.waveHs.values
            result_df["WMI_waveTp"] = ds.waveTp.values
            result_df["WMI_waveTa"] = ds.waveTa.values
            result_df["WMI_waveDp"] = ds.waveDp.values
            result_df["WMI_wavePeakPSD"] = ds.wavePeakPSD.values
            result_df["WMI_waveTz"] = ds.waveTz.values

            result_df.index = pd.to_datetime(result_df.index, utc=True)
            result_df.index.name = "time"

            # Unix seconds
            result_df["Timestamp"] = result_df.index.astype(np.int64) // 10**9
            result_df["Raw_Timestamp"] = result_df.index.astype(str)

            # This is dumb but everything else is in unix seconds
            result_df.index = result_df["Timestamp"]

            return result_df, ds
        except Exception as e:
            self.logger.error(
                __name__, f"Failed to parse nc file {local_nc_file} with error {e}"
            )
            return None, None
        finally:
            # Remove the file after processing
            if os.path.exists(local_nc_file):
                os.remove(local_nc_file)


if __name__ == "__main__":
    parser = CDIPRealTimeParser("225")
    df, ds_new = parser.parse_latest_nc_file()
    if df is not None:
        print(df.info())
        print(df.head())
