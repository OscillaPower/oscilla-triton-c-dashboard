import xarray as xr

from CDIPRealTimeParser import CDIPRealTimeParser
from DataHandler import DataHandler
from FileManager import FileManager
from Logger import Logger
from SQLite import SQLite


class SpectraHandler(DataHandler):
    def __init__(self):
        super().__init__()
        # https://cdip.ucsd.edu/m/products/?stn=225p1
        self.CDIP_KBAY_STATION_NUMBER = "225"

        self.db = SQLite()
        self.file_manager = FileManager()
        self.logger = Logger()

    def update_spectra(self):
        parser = CDIPRealTimeParser(self.CDIP_KBAY_STATION_NUMBER)
        wmi_df, ds_new = parser.parse_latest_nc_file()

        # Upload the vap calculations to the db
        super(SpectraHandler, self).unique_insert(
            wmi_df, self.db.insert_spectra, self.db.select_matching_spectra_timestamps
        )

        # Combine existing and new spectral data into one nc file and save it
        ds_existing_path = self.file_manager.get_existing_cdip_realtime_nc_path(
            self.CDIP_KBAY_STATION_NUMBER
        )

        ds_existing = xr.open_dataset(ds_existing_path)

        wave_time_vars_existing = {
            var: ds_existing[var]
            for var in ds_existing.data_vars
            if "waveTime" in ds_existing[var].dims
        }
        wave_time_vars_new = {
            var: ds_new[var]
            for var in ds_new.data_vars
            if "waveTime" in ds_new[var].dims
        }

        # Create new datasets with just the 'waveTime' related variables
        ds_existing_wave = xr.Dataset(wave_time_vars_existing)
        ds_new_wave = xr.Dataset(wave_time_vars_new)

        combined_wave_ds = xr.concat([ds_existing_wave, ds_new_wave], dim="waveTime")

        # Include global attributes from the existing dataset and check for differences
        combined_wave_ds.attrs = ds_existing.attrs
        for attr, value in ds_new.attrs.items():
            if attr in ds_existing.attrs and ds_existing.attrs[attr] != value:
                self.logger.warning(
                    __name__,
                    f"Attribute '{attr}' differs between datasets. Keeping value from the existing dataset.",
                )
            elif attr not in ds_existing.attrs:
                self.logger.warning(
                    __name__,
                    f"New attribute '{attr}' found in the new dataset. Ignoring it.",
                )

        # Add meta variables that don't have dimensions from the existing dataset
        meta_vars = [
            "metaStationName",
            "metaPlatform",
            "metaInstrumentation",
            "metaDeployLatitude",
            "metaDeployLongitude",
            "metaWaterDepth",
            "metaDeclination",
            "metaGridMapping",
        ]

        for var in meta_vars:
            if var in ds_existing.variables:
                combined_wave_ds[var] = ds_existing[var]
                # Check if the variable is in the new dataset and differs
                if var in ds_new.variables and not ds_existing[var].identical(
                    ds_new[var]
                ):
                    # warnings.warn(
                    self.logger.warning(
                        __name__,
                        f"Meta variable '{var}' differs between datasets. Keeping value from the existing dataset.",
                    )
            elif var in ds_new.variables:
                # Only add from the new dataset if it doesn't exist in the existing one
                combined_wave_ds[var] = ds_new[var]
                # warnings.warn(
                self.logger.warning(
                    __name__,
                    f"Meta variable '{var}' found only in the new dataset. Adding it to the output.",
                )

        self.file_manager.update_cdip_realtime_nc(
            combined_wave_ds, self.CDIP_KBAY_STATION_NUMBER
        )

        return wmi_df

    def read_spectra(self):
        return self.db.select_spectra()
