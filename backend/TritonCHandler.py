import glob
from pathlib import Path

import pandas as pd

from CanaryRequester import CanaryRequester
from DataHandler import DataHandler
from DirectoryManager import DirectoryManager
from FileManager import FileManager
from Logger import Logger
from SQLite import SQLite


class TritonC(DataHandler):
    def __init__(self):
        super().__init__()
        self.server = None
        self.db = SQLite()
        self.file_manager = FileManager()
        self.dirs = DirectoryManager()

        self.populate_count = {}
        self.logger = Logger()

        self.canary_ip_address = "10.0.2.8"

    def init_canary_request(self):
        self.server = CanaryRequester(self.canary_ip_address)
        self.server.setup()

    #  Populate -------------------------------------------------------------{{{

    def populate_from_files(
        self, dir_glob, insert_function, extract_timestamp_function, transpose_dict={}
    ):
        files = glob.glob(dir_glob)

        df_list = []

        for f in files:
            df = pd.read_json(f, orient="split", convert_dates=False)

            df = df.rename(columns=transpose_dict)

            if df is not None:
                if "Timestamp" in df.columns:
                    df.index = pd.to_numeric(df["Timestamp"])

            df_list.append(df)

        df = pd.concat(df_list)

        # df.index = pd.to_numeric(df["Timestamp"])
        df.index.name = "Timestamp"
        df = df.drop(["Timestamp"], axis=1, errors="ignore")

        # Remove rows with where the indexes are duplicates
        # Because the SQL timestamp is unique, this is important to do before insertion
        df = df[~df.index.duplicated()]

        df.sort_index(inplace=True)

        result = self.unique_insert(df, insert_function, extract_timestamp_function)
        return result

    #  End Populate ---------------------------------------------------------}}}
    #  triton_c -------------------------------------------------------------{{{

    # Populate `triton_c` table from json files
    # Right now this uses the legacy `gps_coords`, `power_performance`, and `deployment_state` files.
    # When the `triton_c` files get populated, we can switch over to using them.
    def populate_triton_c(self):
        gps_files = glob.glob(str(Path(self.dirs.gps_coords, "*.json")))
        power_performance_files = glob.glob(
            str(Path(self.dirs.power_performance, "*.json"))
        )
        deployment_state_files = glob.glob(
            str(Path(self.dirs.deployment_state, "*.json"))
        )

        gps_df_list = [pd.read_json(f, orient="split") for f in gps_files]
        power_performance_df_list = [
            pd.read_json(f, orient="split") for f in power_performance_files
        ]
        deployment_state_df_list = [
            pd.read_json(f, orient="split") for f in deployment_state_files
        ]

        gps_df = pd.concat(gps_df_list)
        gps_df.drop_duplicates(inplace=True, subset="Timestamp")

        power_performance_df = pd.concat(power_performance_df_list)
        power_performance_df.drop_duplicates(inplace=True, subset="Timestamp")

        deployment_state_df = pd.concat(deployment_state_df_list)
        deployment_state_df.drop_duplicates(inplace=True, subset="Timestamp")

        df = pd.concat([gps_df, power_performance_df, deployment_state_df])

        transpose_col = {
            "Mean_Wave_Period_Te": "Mean_Wave_Period",
            "Mean_Wave_Height_Hm0": "Mean_Wave_Height",
            "Total_Power": "Total_Power_kW",
        }
        df = df.rename(columns=transpose_col)

        df.index = pd.to_numeric(df["Timestamp"])
        df.index.name = "Timestamp"
        df = df.drop(["Timestamp"], axis=1)

        # Remove rows with where the indexes are duplicates
        # Because the SQL timestamp is unique, this is important to do before insertion
        df = df[~df.index.duplicated()]

        df.sort_index(inplace=True)

        self.file_manager.save_triton_c_all(df)

        self.db_update_triton_c(df)

        return df

    def db_update_triton_c(self, df):
        super(TritonC, self).unique_insert(
            df, self.db.insert_triton_c, self.db.select_matching_triton_c_timestamps
        )

    def update_triton_c(self, canary_time_interval):
        self.init_canary_request()

        if self.server is not None:
            df = self.server.request_all_data(canary_time_interval)
            if df is None or df.empty is True:
                self.logger.info(
                    __name__,
                    "Canary is running but there is no available data, returning...",
                )
                return

            self.file_manager.save_triton_c_all(df)

            super(TritonC, self).unique_insert(
                df, self.db.insert_triton_c, self.db.select_matching_triton_c_timestamps
            )

    #  End triton_c ---------------------------------------------------------}}}
    #  Gps Coords -----------------------------------------------------------{{{

    def populate_gps_coords(self):
        self.populate_from_files(
            str(Path(self.dirs.gps_coords, "*.json")),
            self.db.insert_gps_coords,
            self.db.select_matching_gps_timestamps,
        )

    def update_gps_coords(self, canary_time_interval):
        if self.server is None:
            self.init_canary_request()

        if self.server is not None:
            coords_df = self.server.request_gps_coords(canary_time_interval)
            if coords_df is not None:
                self.file_manager.save_power_performance(coords_df)
                super(TritonC, self).unique_insert(
                    coords_df,
                    self.db.insert_power_performance,
                    self.db.select_matching_gps_timestamps,
                )

                return coords_df

        return None

    def read_gps_coords(self, num_entries):
        return self.db.select_power_performance(num_entries)

    #  End Gps Coords -------------------------------------------------------}}}
    #  Deployment State -----------------------------------------------------{{{

    def populate_deployment_state(self):
        self.populate_from_files(
            str(Path(self.dirs.deployment_state, "*.json")),
            self.db.insert_deployment_state,
            self.db.select_matching_deployment_state_timestamps,
        )

    def update_deployment_state(self, canary_time_interval):
        if self.server is None:
            self.init_canary_request()

        if self.server is not None:
            df = self.server.request_all_data(canary_time_interval)
            if df is not None:
                self.file_manager.save_deployment_state(df)

                super(TritonC, self).unique_insert(
                    df,
                    self.db.insert_deployment_state,
                    self.db.select_matching_deployment_state_timestamps,
                )

                return df

    def read_deployment_state(self, num_entries):
        return self.db.select_deployment_state(num_entries)

    #  End Deployment State -------------------------------------------------}}}
    #  Power Performance ----------------------------------------------------{{{

    def populate_power_performance(self):
        transpose_col = {
            "Mean_Wave_Period_Te": "Mean_Wave_Period",
            "Mean_Wave_Height_Hm0": "Mean_Wave_Height",
            "Total_Power": "Total_Power_kW",
        }

        self.populate_from_files(
            str(Path(self.dirs.power_performance, "*.json")),
            self.db.insert_power_performance,
            self.db.select_matching_power_performance_timestamps,
            transpose_dict=transpose_col,
        )

    def update_power_performance(self, canary_time_interval):
        if self.server is None:
            self.init_canary_request()

        if self.server is not None:
            df = self.server.request_power_performance_data(canary_time_interval)
            if df is not None:
                self.file_manager.save_power_performance(df)
                super(TritonC, self).unique_insert(
                    df,
                    self.db.insert_power_performance,
                    self.db.select_matching_power_performance_timestamps,
                )

                return df

    def read_power_performance(self, num_entries):
        return self.db.select_power_performance(num_entries)

    #  End Power Performance ------------------------------------------------}}}
