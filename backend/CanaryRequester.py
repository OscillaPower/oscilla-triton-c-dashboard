import socket

import pandas as pd
import requests

from Logger import Logger

# Abstracts access to the Oscilla Power Triton-C Canary server
# Follows Canary 21.1 documentation: https://readapi.canarylabs.com/21.1/
class CanaryRequester:
    def __init__(self, ip_address):
        self.ip = ip_address
        self.port = "55235"
        self.entry_url = f"http://{self.ip}:{self.port}/api/v2/"

        # This dictates the number of responses before pagination kicks in. To
        # simplify this code we set this to a relatively large number and run
        # this code fairly frequently (every 5 minutes). The caveat is that if
        # the data generated by the WEC exceeds this limit we will not collect
        # all data. TODO: The statements above should be verified when the WEC
        # and canary server is running consistently
        self.default_max_size = 100_000

        # List of all tags available on the canary server
        self.raw_tags = []

        self.logger = Logger()

        self.all_data_request_bundle = {
            "WIN-SUARIOMU79L.Dataset 1.Pos_Lat": "GPS_Lat",
            "WIN-SUARIOMU79L.Dataset 1.Pos_Long": "GPS_Lng",
            "WIN-SUARIOMU79L.Dataset 1.Is_Deployed": "Is_Deployed",
            "WIN-SUARIOMU79L.Dataset 1.Is_Maint": "Is_Maint",
            "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period": "Mean_Wave_Period",
            "WIN-SUARIOMU79L.Dataset 1.Wave_Height": "Mean_Wave_Height",
            "WIN-SUARIOMU79L.Dataset 1.JI1607.PV": "PTO_Bow_Power_kW",
            "WIN-SUARIOMU79L.Dataset 1.JI2607.PV": "PTO_Starboard_Power_kW",
            "WIN-SUARIOMU79L.Dataset 1.JI3607.PV": "PTO_Port_Power_kW",
        }
        self.all_data_df = None

        # Dict of tags to request and specification of the output DataFrame column names
        self.power_performance_request_bundle = {
            "WIN-SUARIOMU79L.Dataset 1.Is_Deployed": "Is_Deployed",
            "WIN-SUARIOMU79L.Dataset 1.Is_Maint": "Is_Maint",
            "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period": "Mean_Wave_Period",
            "WIN-SUARIOMU79L.Dataset 1.Wave_Height": "Mean_Wave_Height",
            "WIN-SUARIOMU79L.Dataset 1.JI1607.PV": "PTO_Bow_Power_kW",
            "WIN-SUARIOMU79L.Dataset 1.JI2607.PV": "PTO_Starboard_Power_kW",
            "WIN-SUARIOMU79L.Dataset 1.JI3607.PV": "PTO_Port_Power_kW",
        }
        self.power_performance_df = None
        self.power_performance_duration_string = ""
        self.power_performance_save_dir = "power_performance"

        # Dict of tags to request with the DataFrame column names
        self.gps_coords_request_bundle = {
            "WIN-SUARIOMU79L.Dataset 1.Pos_Lat": "GPS_Lat",
            "WIN-SUARIOMU79L.Dataset 1.Pos_Long": "GPS_Lng",
        }
        self.gps_coords_df = None
        self.gps_coords_duration_string = ""
        self.gps_coords_save_dir = "gps_coords"

        self.deployment_state_request_bundle = {
            "WIN-SUARIOMU79L.Dataset 1.Is_Deployed": "Is_Deployed",
            "WIN-SUARIOMU79L.Dataset 1.Is_Maint": "Is_Maint",
        }
        self.deployment_state_df = None
        self.deployment_state_duration_string = None
        self.deployment_state_save_dir = "deployment_state"

    def setup(self):
        self.logger.info(__name__, "Beginning Triton-C Canary Request")
        is_online = self.is_online()
        if is_online != True:
            message = (
                f"Triton-C Canary Server @ {self.entry_url} not responding! Exiting..."
            )
            self.logger.error(__name__, message)
            exit(message)

        self.init_tags()

        if len(self.raw_tags) < 1:
            self.logger.warning(
                __name__,
                f"Triton-C Canary Server returned {len(self.raw_tags)} tags! Proceeding, but there may be errors...",
            )

        return True

    def __repr__(self):
        return self.entry_url

    def is_online(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        try:
            is_open = sock.connect_ex((self.ip, int(self.port))) == 0

            if is_open:
                sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            is_open = False

        sock.close()

        return is_open

    # Request data from the specified canary endpoint
    # Returns a dict of results
    # Example result.text:
    # {
    #     "statusCode": "Good",
    #     "errors": [],
    #     "data": {
    #         "WIN-SUARIOMU79L.Dataset 1.Is_Deployed": [
    #             {"t": "2022-01-31T17:04:04.0000000-10:00", "v": false},
    #             {"t": "2022-01-31T17:18:23.0000001-10:00", "v": null},
    #             {"t": "2022-02-02T09:56:55.5000000-10:00", "v": false},
    #             {"t": "2022-02-02T09:56:55.5000001-10:00", "v": null},
    #             {"t": "2022-02-02T10:01:27.0000000-10:00", "v": false},
    #             {"t": "2022-02-02T10:01:27.0000001-10:00", "v": null},
    #             {"t": "2022-02-02T10:04:29.5000000-10:00", "v": false},
    #             {"t": "2022-02-04T15:47:14.0000001-10:00", "v": null},
    #             {"t": "2022-02-22T11:02:37.0000000-10:00", "v": false},
    #             {"t": "2022-02-24T16:52:59.0000000-10:00", "v": false},
    #         ]
    #     },
    #     "continuation": null,
    # }
    def request_endpoint(self, endpoint, params):
        try:
            result = requests.get(f"{self.entry_url}{endpoint}", params)
        except requests.exceptions.RequestException as e:
            self.logger.error(
                __name__,
                f"Request: {self.entry_url}{endpoint} with params: {params} failed!",
            )
            raise SystemExit(e)

        data = result.json()

        return data

    # Query the canary server for all tags
    def init_tags(self):
        params = {
            "deep": True,
            "maxSize": 10000,
        }
        data = self.request_endpoint("browseTags", params)
        tags = data["tags"]
        self.raw_tags = tags

    def request_timeseries(self, tag, duration_string, column_name_str, max_items=None):
        if max_items is None:
            max_items = self.default_max_size

        params = {
            "tags": [tag],
            "startTime": duration_string,
            "endTime": "Now",
            "maxSize": max_items,
        }

        response = self.request_endpoint("getTagData", params=params)
        data = response["data"][tag]

        timestamps = []
        values = []

        for row in data:
            timestamps.append(row["t"])
            values.append(row["v"])

        df = pd.DataFrame(
            zip(timestamps, values), columns=["timestamp", column_name_str]
        )

        return df

    # Be aware that there is no way to sort these requests to get the latest results first
    # The latest results will always be at the END of the array.
    # To ensure all results are returned either increase `max_items` or decrease `duration_string`
    # TODO: Validate that a tag exists, can be helpful to eliminate typos
    def request_multiple_timeseries(self, item_dict, duration_string, max_items=None):
        if max_items is None:
            max_items = self.default_max_size

        tags = list(item_dict.keys())
        column_names = list(item_dict.values())

        params = {
            "tags": tags,
            "startTime": duration_string,
            "endTime": "Now",
            "maxSize": max_items,
        }

        response = self.request_endpoint("getTagData", params=params)
        data = response["data"]

        response_tags = list(data.keys())

        # To convert the response into a DataFrame we need to iterate over each
        # set of responses and map the values to timestamps. We do this by
        # creating a dictionary with timestamps as keys and values as named
        # values. This organizes the canary response into a sane format for
        # further processing
        response_dict = {}

        empty_row = {}

        for col in column_names:
            empty_row[col] = None

        for key in response_tags:
            values = data[key]
            col_name = item_dict[key]
            for row in values:
                timestamp = row["t"]
                value = row["v"]

                if timestamp not in response_dict:
                    response_dict[timestamp] = empty_row

                response_dict[timestamp][col_name] = value

        # Check the response dict for values
        num_responses = len(response_dict.keys())

        if num_responses == 0:
            self.logger.error(
                __name__,
                f"Timeseries request: {tags} returned {num_responses} responses.",
            )
            return None

        # Convert the response dict into a dataframe with the timestamp string as the index
        df = pd.DataFrame.from_dict(response_dict, orient="index")

        # Set Raw_Timestamp to the "t" values from the response
        df["Raw_Timestamp"] = response_dict.keys()

        # Set the index to unix epoch ns integer
        timestamps = pd.to_datetime(df["Raw_Timestamp"])
        df.index = pd.to_numeric(timestamps)

        # Sort the response from newest to oldest
        df = df.sort_index(ascending=False)

        # Below keeps parquet happy, it may be needed if the above approach doesn't work
        # Convert the timestamp string to a pandas timestamp
        # df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        # This timestamp conversion keeps parquet happy
        # df["Timestamp"] = df["Raw_Timestamp"].astype("datetime64[s]")

        # Sort by timestamp with the most recent values first
        # df = df.sort_values("Timestamp", ascending=False)

        # Change the column order so timestamp comes before everything else
        # column_names.insert(0, "Timestamp")
        # df = df[column_names]

        # Reset the index so it starts from zero
        # df: pd.DataFrame = df.reset_index(drop=True)

        return df

    def request_all_data(self, duration_string):
        response = self.request_multiple_timeseries(
            self.all_data_request_bundle, duration_string, self.default_max_size
        )

        if isinstance(response, pd.DataFrame):
            df: pd.DataFrame = response
        else:
            return None

        df["Total_Power_kW"] = (
            df["PTO_Bow_Power_kW"]
            + df["PTO_Port_Power_kW"]
            + df["PTO_Starboard_Power_kW"]
        )

        self.all_data_df = df

        return self.all_data_df

    def request_gps_coords(self, duration_string):
        self.gps_coords_df = self.request_multiple_timeseries(
            self.gps_coords_request_bundle, duration_string, self.default_max_size
        )
        self.gps_coords_duration_string = duration_string

        return self.gps_coords_df

    def request_deployment_state(self, duration_string):
        self.deployment_state_df = self.request_multiple_timeseries(
            self.deployment_state_request_bundle, duration_string, self.default_max_size
        )
        self.deployment_state_duration_string = duration_string

        return self.deployment_state_df

    def request_power_performance_data(self, duration_string):
        response = self.request_multiple_timeseries(
            self.power_performance_request_bundle,
            duration_string,
            self.default_max_size,
        )

        if isinstance(response, pd.DataFrame):
            df: pd.DataFrame = response
        else:
            return None

        df["Total_Power_kW"] = (
            df["PTO_Bow_Power_kW"]
            + df["PTO_Port_Power_kW"]
            + df["PTO_Starboard_Power_kW"]
        )

        self.power_performance_df = df
        self.power_performance_duration_string = duration_string

        return self.power_performance_df
