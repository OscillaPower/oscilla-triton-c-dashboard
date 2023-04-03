from mhkit import wave
import pandas as pd

from DataHandler import DataHandler
from FileManager import FileManager
from NDBCRealTimeRawSpectralParser import NDBCRealTimeRawSpectralParser
from SQLite import SQLite


class SpectraHandler(DataHandler):
    def __init__(self):
        super().__init__()
        self.DEPLOYMENT_DEPTH_METERS = 30
        # http://cdip.ucsd.edu/m/products/?stn=225p1
        # https://www.ndbc.noaa.gov/station_page.php/?station=51210
        self.NDBC_BUOY_STATION_NUMBER = "51210"

        self.db = SQLite()
        self.file_manager = FileManager()

    def update_spectra(self):
        parser = NDBCRealTimeRawSpectralParser(self.NDBC_BUOY_STATION_NUMBER)
        spectra_df, raw_timestamps = parser.parse_latest_spec_file()

        timestamps = spectra_df.index

        save_spectra_df = spectra_df.copy()

        save_spectra_df["Raw_Timestamp"] = raw_timestamps

        self.file_manager.save_raw_spectra(
            save_spectra_df,
            self.NDBC_BUOY_STATION_NUMBER,
            str(raw_timestamps[0]).replace(":", "_"),
            str(raw_timestamps[-1]).replace(":", "_"),
        )

        # Format spectra for mhkit processing
        spectra_df = spectra_df.T

        Te = wave.resource.energy_period(spectra_df).squeeze()

        Hm0 = wave.resource.significant_wave_height(spectra_df).squeeze()
        J = wave.resource.energy_flux(
            spectra_df, self.DEPLOYMENT_DEPTH_METERS
        ).squeeze()

        df = pd.DataFrame(
            list(zip(raw_timestamps, Te, Hm0, J)),
            columns=["Raw_Timestamp", "Te", "Hm0", "J"],
        )

        df.index = pd.to_numeric(timestamps)
        df.index.name = "Timestamp"

        self.file_manager.save_spectra_calc(
            df,
            self.NDBC_BUOY_STATION_NUMBER,
            str(timestamps[0]).replace(":", "_"),
            str(timestamps[-1]).replace(":", "_"),
        )

        super(SpectraHandler, self).unique_insert(
            df, self.db.insert_spectra, self.db.select_matching_spectra_timestamps
        )

        return df

    def read_spectra(self):
        return self.db.select_spectra()
