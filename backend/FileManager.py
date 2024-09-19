import shutil

from datetime import datetime
from pathlib import Path

from DirectoryManager import DirectoryManager
from DataFrameArchiver import DataFrameArchiver


class FileManager:
    def __init__(self):
        self.dirs = DirectoryManager()

    def get_date_string(self):
        now = datetime.now()
        return now.strftime("%Y_%m_%d_%H_%M_%S")

    def get_filepath_that_may_not_exist(self, dir, filepath):
        this_path = Path(dir, filepath)

        if this_path.exists() == False:
            this_path.touch()

        return this_path

    def save_triton_c_data(self, df, dir, name):
        first_timestamp = df.index[0]
        last_timestamp = df.index[-1]

        filename = f"{self.get_date_string()}_{name}_{first_timestamp}-{last_timestamp}"
        DataFrameArchiver.save_df(df, dir, filename)

    def save_triton_c_all(self, df):
        self.save_triton_c_data(df, self.dirs.triton_c, "triton_c_all")

    def save_deployment_state(self, df):
        self.save_triton_c_data(df, self.dirs.deployment_state, "deployment_state")

    def save_gps_coords(self, df):
        self.save_triton_c_data(df, self.dirs.gps_coords, "gps_coords")

    def save_power_performance(self, df):
        self.save_triton_c_data(df, self.dirs.power_performance, "power_performance")

    def save_spectra(self, name, path, df, station, first_timestamp, last_timestamp):
        filename = f"{self.get_date_string()}_{station}_{name}_{first_timestamp}-{last_timestamp}"
        DataFrameArchiver.save_df(df, path, filename)

    def save_raw_spectra(self, df, station, first_timestamp, last_timestamp):
        path = self.dirs.raw_spectra
        self.save_spectra(
            "spectra_calc", path, df, station, first_timestamp, last_timestamp
        )

    def get_existing_cdip_realtime_nc_path(self, station):
        filename = f"concat_{station}p1_rt.nc"
        path = self.dirs.spectra_cdip_nc
        return Path(path, filename)

    def update_cdip_realtime_nc(self, new_ds, station):
        filename = f"concat_{station}p1_rt.nc"
        temp_filename = f"temp_{filename}"
        path = self.dirs.spectra_cdip_nc

        new_ds.to_netcdf(Path(path, temp_filename))

        shutil.move(Path(path, temp_filename), Path(path, filename))

    def save_spectra_calc(self, df, station, first_timestamp, last_timestamp):
        path = self.dirs.spectra_calc
        self.save_spectra(
            "spectra_calc", path, df, station, first_timestamp, last_timestamp
        )

    def get_power_matrix_latest_filename(self, pto_name, image_format):
        return Path(
            self.dirs.visualization_dir,
            f"{pto_name}_power_matrix_latest.{image_format}",
        )

    def get_log_filepath(self):
        return self.get_filepath_that_may_not_exist(
            self.dirs.log_dir, "Triton_C_Backend_Processes.log"
        )

    def get_db_filepath(self):
        return self.get_filepath_that_may_not_exist(self.dirs.data_dir, "triton_c.db")
