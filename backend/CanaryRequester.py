# Abstracts access to the Oscilla Power Triton-C Canary server
# Follows Canary 21.1 documentation: https://readapi.canarylabs.com/21.1/
# To build the dashboard we need to access specific canary api endpoints
# The `CanaryRequest` class queries the server for the available endpoints and allows actions the validated (WIP) endpoints

from datetime import datetime
import logging
import os
import socket

import pandas as pd
import requests


# Cleanly request data from the canary server
class CanaryRequest:
    def __init__(self):
        self.ip = "10.0.2.8"
        self.port = "55235"
        self.entry_url = f"http://{self.ip}:{self.port}/api/v2/"
        self.raw_tags = []
        self.save_dir = "../data"
        self.logging_dir = "../logs/CanaryRequest.log"

        if os.getenv("CANARY_REQUEST_PRODUCTION", "test") != "test":
            self.save_dir = "/home/nrel@oscillapower.local/dashboard/data"
            self.logging_dir = (
                "/home/nrel@oscillapower.local/dashboard/logs/CanaryRequest.log"
            )

        logging.basicConfig(
            filename=self.logging_dir,
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%Y_%m_%d-%H:%M:%S",
            level=logging.INFO,
        )

        self.logger = Logger()

        # Dict of tags to request and specification of the output DataFrame column names
        self.power_performance_request_bundle = {
            "WIN-SUARIOMU79L.Dataset 1.Is_Deployed": "Is_Deployed",
            "WIN-SUARIOMU79L.Dataset 1.Is_Maint": "Is_Maint",
            "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period": "Mean_Wave_Period_Te",
            "WIN-SUARIOMU79L.Dataset 1.Wave_Height": "Mean_Wave_Height_Hm0",
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

        self.setup()

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

    def request_timeseries(
        self, tag, duration_string, column_name_str, max_items=10000
    ):
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
    def request_multiple_timeseries(self, item_dict, duration_string, max_items=10000):
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

        # To convert the response into a DataFrame we need to iterate over each set of responses and map the values to timestamps
        # We do this by creating a dictionary with timestamps as keys and values as named values
        # This organized the canary response into a sane format for further processing
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

        # Extract "Timestamp" into a separate column and create a new index
        df["Timestamp"] = df.index
        df = df.reset_index(level=0)

        # Convert the timestamp string to a pandas timestamp
        # df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        # This timestamp conversion keeps parquet happy
        df["Timestamp"] = df["Timestamp"].astype("datetime64[s]")

        # Sort by timestamp with the most recent values first
        df = df.sort_values("Timestamp", ascending=False)

        # Change the column order so timestamp comes before everything else
        column_names.insert(0, "Timestamp")
        df = df[column_names]

        # Reset the index so it starts from zero
        df: pd.DataFrame = df.reset_index(drop=True)

        return df

    def request_gps_coords(self, duration_string):
        self.gps_coords_df = self.request_multiple_timeseries(
            self.gps_coords_request_bundle, duration_string, 5000
        )
        self.gps_coords_duration_string = duration_string

        return self.gps_coords_df

    def request_deployment_state(self, duration_string):
        self.deployment_state_df = self.request_multiple_timeseries(
            self.deployment_state_request_bundle, duration_string, 10000
        )
        self.deployment_state_duration_string = duration_string

        return self.deployment_state_df

    def request_power_performance_data(self, duration_string):
        response = self.request_multiple_timeseries(
            self.power_performance_request_bundle, duration_string, 10000
        )

        if isinstance(response, pd.DataFrame):
            df: pd.DataFrame = response
        else:
            return None

        df["Total_Power"] = (
            df["PTO_Bow_Power_kW"]
            + df["PTO_Port_Power_kW"]
            + df["PTO_Starboard_Power_kW"]
        )

        self.power_performance_df = df
        self.power_performance_duration_string = duration_string

        return self.power_performance_df

    def save_df_to_file(self, input_df, name, time_period_str, folder):
        now = datetime.now()
        date_string = now.strftime("%Y_%m_%d_%H_%M_%S")
        save_dir = os.path.join(self.save_dir, folder)
        filename = f"{date_string}_triton_c_{name}_{time_period_str}"

        input_df.to_csv(os.path.join(save_dir, f"{filename}.csv"))
        input_df.to_json(
            os.path.join(save_dir, f"{filename}.json"),
            orient="split",
            index=False,
        )
        # Example json output:
        # test = {
        #     "columns": ["Timestamp", "GPS_Lat", "GPS_Lng"],
        #     "data": [
        #         [1675463845000, 21.3102664948, -157.8704528809],
        #         [1675463836000, 21.3102664948, -157.8704528809],
        #         [1675463835000, 21.3102664948, -157.8704528809],
        #         [1675463827000, 21.3102664948, -157.8704528809],
        #         [1675463818000, 21.3102664948, -157.8704528809],
        #     ],
        # }
        input_df.to_parquet(
            os.path.join(save_dir, f"{filename}.parquet"),
            compression=None,
        )

        logging.info(
            f"triton_c_{name}_{date_string}_{time_period_str} save successful!"
        )

        return True

    def save(self):

        if isinstance(self.deployment_state_df, pd.DataFrame):
            self.save_df_to_file(
                self.deployment_state_df,
                "deployment_state",
                self.deployment_state_duration_string,
                self.deployment_state_save_dir,
            )

        if isinstance(self.power_performance_df, pd.DataFrame):
            self.save_df_to_file(
                self.power_performance_df,
                "power_performance",
                self.power_performance_duration_string,
                self.power_performance_save_dir,
            )

        if isinstance(self.gps_coords_df, pd.DataFrame):
            self.save_df_to_file(
                self.gps_coords_df,
                "gps_coords",
                self.gps_coords_duration_string,
                self.gps_coords_save_dir,
            )

    def request_is_deployed(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Is_Deployed", duration_string, "Is_Deployed"
        )

    def request_is_maint(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Is_Maint", duration_string, "Is_Maint"
        )

    # Return a DataFrame of mean wave period data
    def request_mean_wave_period(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period", duration_string, "Te"
        )

    def request_wave_height(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Wave_Height", duration_string, "Hm0"
        )

    def request_pto_1_power(self, duration_string):
        # 'JI-1607_PV'  - PTO 1 Power (Bow) [kW]
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.JI1607.PV", duration_string, "PTO_Bow_Power_kW"
        )

    def request_pto_2_power(self, duration_string):
        # 'JI-2607_PV'   - PTO 2 Power (Starboard) [kW]
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.JI2607.PV",
            duration_string,
            "PTO_Starboard_Power_kW",
        )

    def request_pto_3_power(self, duration_string):
        # 'JI-3607_PV'   - PTO 3 Power (Port) [kW]
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.JI3607.PV", duration_string, "PTO_Port_Power_kW"
        )

    def request_latitude(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Pos_Lat", duration_string, "GPS_Lat"
        )

    def request_longitude(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Pos_Long", duration_string, "GPS_Lng"
        )


#  Tags -----------------------------------------------------------------{{{


# List of tags from last query: 1/31/23
tags = [
    "WIN-SUARIOMU79L.Dataset 1.Axiom_Heartbeat",
    "WIN-SUARIOMU79L.Dataset 1.Bow_Sheave_Speed_rpm",
    "WIN-SUARIOMU79L.Dataset 1.Dominant_Wave_Period",
    "WIN-SUARIOMU79L.Dataset 1.Is_Deployed",
    "WIN-SUARIOMU79L.Dataset 1.Is_Maint",
    "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Direction",
    "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period",
    "WIN-SUARIOMU79L.Dataset 1.Port_Sheave_Speed_rpm",
    "WIN-SUARIOMU79L.Dataset 1.Pos_Lat",
    "WIN-SUARIOMU79L.Dataset 1.Pos_Lat_m_rel",
    "WIN-SUARIOMU79L.Dataset 1.Pos_Long",
    "WIN-SUARIOMU79L.Dataset 1.Pos_Long_m_rel",
    "WIN-SUARIOMU79L.Dataset 1.Power_export",
    "WIN-SUARIOMU79L.Dataset 1.Stbd_Sheave_Speed_rpm",
    "WIN-SUARIOMU79L.Dataset 1.System_Deactivate",
    "WIN-SUARIOMU79L.Dataset 1.Total_Power",
    "WIN-SUARIOMU79L.Dataset 1.Total_Power_Avg",
    "WIN-SUARIOMU79L.Dataset 1.Wave_Height",
    "WIN-SUARIOMU79L.Dataset 1.ZT1303",
    "WIN-SUARIOMU79L.Dataset 1.ZT2303",
    "WIN-SUARIOMU79L.Dataset 1.ZT3303",
    "WIN-SUARIOMU79L.Dataset 1.DBT5230.PV",
    "WIN-SUARIOMU79L.Dataset 1.DT5701.PV",
    "WIN-SUARIOMU79L.Dataset 1.DTH5707.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI1605.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI1611.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI2605.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI2611.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI3605.PV",
    "WIN-SUARIOMU79L.Dataset 1.EI3611.PV",
    "WIN-SUARIOMU79L.Dataset 1.HS1101.STS",
    "WIN-SUARIOMU79L.Dataset 1.HS2101.STS",
    "WIN-SUARIOMU79L.Dataset 1.HS3101.STS",
    "WIN-SUARIOMU79L.Dataset 1.II1606.PV",
    "WIN-SUARIOMU79L.Dataset 1.II2606.PV",
    "WIN-SUARIOMU79L.Dataset 1.II3606.PV",
    "WIN-SUARIOMU79L.Dataset 1.JI1607.PV",
    "WIN-SUARIOMU79L.Dataset 1.JI2607.PV",
    "WIN-SUARIOMU79L.Dataset 1.JI3607.PV",
    "WIN-SUARIOMU79L.Dataset 1.JI5604.PV",
    "WIN-SUARIOMU79L.Dataset 1.LS5001.STS",
    "WIN-SUARIOMU79L.Dataset 1.LS5002.STS",
    "WIN-SUARIOMU79L.Dataset 1.LS5350.STS",
    "WIN-SUARIOMU79L.Dataset 1.LS5351.STS",
    "WIN-SUARIOMU79L.Dataset 1.LS5352.STS",
    "WIN-SUARIOMU79L.Dataset 1.LT1401.PV",
    "WIN-SUARIOMU79L.Dataset 1.LT2401.PV",
    "WIN-SUARIOMU79L.Dataset 1.LT3401.PV",
    "WIN-SUARIOMU79L.Dataset 1.NC1609.CV",
    "WIN-SUARIOMU79L.Dataset 1.NC2609.CV",
    "WIN-SUARIOMU79L.Dataset 1.NC3609.CV",
    "WIN-SUARIOMU79L.Dataset 1.NI1608.PV",
    "WIN-SUARIOMU79L.Dataset 1.NI2608.PV",
    "WIN-SUARIOMU79L.Dataset 1.NI3608.PV",
    "WIN-SUARIOMU79L.Dataset 1.PDT5318.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1013.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1014.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1015.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1016.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1017.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1021.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1022.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1023.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1103.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1104.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT1201.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2013.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2014.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2015.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2016.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2017.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2021.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2022.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2023.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2103.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2104.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT2201.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3013.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3014.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3015.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3016.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3017.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3021.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3022.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3023.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3103.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3104.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT3201.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5101.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5103.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5104.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5105.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5302.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5303.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5306.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5319.PV",
    "WIN-SUARIOMU79L.Dataset 1.PT5705.PV",
    "WIN-SUARIOMU79L.Dataset 1.PV1030.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV1030.PV",
    "WIN-SUARIOMU79L.Dataset 1.PV1030.SP",
    "WIN-SUARIOMU79L.Dataset 1.PV1203.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV2030.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV2030.PV",
    "WIN-SUARIOMU79L.Dataset 1.PV2030.SP",
    "WIN-SUARIOMU79L.Dataset 1.PV2203.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV3030.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV3030.PV",
    "WIN-SUARIOMU79L.Dataset 1.PV3030.SP",
    "WIN-SUARIOMU79L.Dataset 1.PV3203.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV5110.CV",
    "WIN-SUARIOMU79L.Dataset 1.PV5111.CV",
    "WIN-SUARIOMU79L.Dataset 1.QI5112.PV",
    "WIN-SUARIOMU79L.Dataset 1.QT5221.PV",
    "WIN-SUARIOMU79L.Dataset 1.QT5704.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5121.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5121.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5121.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SC5122.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5122.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5122.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SC5341.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5341.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5341.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SC5342.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5342.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5342.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SC5343.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5343.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5343.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SC5344.Motor_State",
    "WIN-SUARIOMU79L.Dataset 1.SC5344.PV",
    "WIN-SUARIOMU79L.Dataset 1.SC5344.Setpoint",
    "WIN-SUARIOMU79L.Dataset 1.SG5211.PV",
    "WIN-SUARIOMU79L.Dataset 1.SG5212.PV",
    "WIN-SUARIOMU79L.Dataset 1.SG5213.PV",
    "WIN-SUARIOMU79L.Dataset 1.SG5214.PV",
    "WIN-SUARIOMU79L.Dataset 1.SG5215.PV",
    "WIN-SUARIOMU79L.Dataset 1.SG5216.PV",
    "WIN-SUARIOMU79L.Dataset 1.SI1604.PV",
    "WIN-SUARIOMU79L.Dataset 1.SI2604.PV",
    "WIN-SUARIOMU79L.Dataset 1.SI3604.PV",
    "WIN-SUARIOMU79L.Dataset 1.ST1303.PV",
    "WIN-SUARIOMU79L.Dataset 1.ST2303.PV",
    "WIN-SUARIOMU79L.Dataset 1.ST3303.PV",
    "WIN-SUARIOMU79L.Dataset 1.ST5702.PV",
    "WIN-SUARIOMU79L.Dataset 1.STH5708.PV",
    "WIN-SUARIOMU79L.Dataset 1.SV1001.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1002.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1003.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1007.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1008.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1009.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1010.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV1102.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2001.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2002.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2003.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2007.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2008.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2009.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2010.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV2102.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3001.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3002.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3003.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3007.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3008.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3009.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3010.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV3102.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5100.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5340.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5341.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5342.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5343.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5344.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5345.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.SV5346.Valve_State",
    "WIN-SUARIOMU79L.Dataset 1.TI1601.PV",
    "WIN-SUARIOMU79L.Dataset 1.TI1602.PV",
    "WIN-SUARIOMU79L.Dataset 1.TI2601.PV",
    "WIN-SUARIOMU79L.Dataset 1.TI2602.PV",
    "WIN-SUARIOMU79L.Dataset 1.TI3601.PV",
    "WIN-SUARIOMU79L.Dataset 1.TI3602.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5307.CV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5307.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5307.SP",
    "WIN-SUARIOMU79L.Dataset 1.TIC5323.CV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5323.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5323.SP",
    "WIN-SUARIOMU79L.Dataset 1.TIC5326.CV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5326.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5326.SP",
    "WIN-SUARIOMU79L.Dataset 1.TIC5329.CV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5329.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5329.SP",
    "WIN-SUARIOMU79L.Dataset 1.TIC5330.CV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5330.PV",
    "WIN-SUARIOMU79L.Dataset 1.TIC5330.SP",
    "WIN-SUARIOMU79L.Dataset 1.TT1024.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1025.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1026.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1027.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1028.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1110.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1302.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT1402.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2024.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2025.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2026.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2027.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2028.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2110.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2302.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT2402.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3024.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3025.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3026.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3027.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3028.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3110.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3302.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT3402.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5107.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5220.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5304.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5305.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5307.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5310.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5313.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5316.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5317.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5320.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5507.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5508.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5509.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5602.PV",
    "WIN-SUARIOMU79L.Dataset 1.TT5703.PV",
    "WIN-SUARIOMU79L.Dataset 1.TTX5706.PV",
    "WIN-SUARIOMU79L.Dataset 1.TV5321.CV",
    "WIN-SUARIOMU79L.Dataset 1.TV5322.CV",
    "WIN-SUARIOMU79L.Dataset 1.TV5324.CV",
    "WIN-SUARIOMU79L.Dataset 1.TV5325.CV",
    "WIN-SUARIOMU79L.Dataset 1.TV5327.CV",
    "WIN-SUARIOMU79L.Dataset 1.TV5328.CV",
    "WIN-SUARIOMU79L.Dataset 1.UI1610.PV",
    "WIN-SUARIOMU79L.Dataset 1.UI2610.PV",
    "WIN-SUARIOMU79L.Dataset 1.UI3610.PV",
    "WIN-SUARIOMU79L.Dataset 1.VT1301.PV",
    "WIN-SUARIOMU79L.Dataset 1.VT2301.PV",
    "WIN-SUARIOMU79L.Dataset 1.VT3301.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5401.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5402.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5403.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5501.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5502.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5503.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5504.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5505.PV",
    "WIN-SUARIOMU79L.Dataset 1.WT5506.PV",
    "WIN-SUARIOMU79L.Dataset 1.XA1004.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1005.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1006.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1014.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1015.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1016.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1029.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1102.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1201.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1601.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1608.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA1609.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2004.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2005.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2006.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2014.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2015.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2016.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2029.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2102.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2201.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2601.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2608.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA2609.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3004.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3005.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3006.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3014.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3015.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3016.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3029.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3102.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3201.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3601.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3608.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA3609.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5101.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5121.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5122.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5321.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5322.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5323.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5324.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5325.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5326.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5327.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5328.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5329.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5330.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5341.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5343.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5400.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5401.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5402.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5603.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5800.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA5901.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6101.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6102.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6103.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6104.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6105.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6106.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6107.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6108.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6109.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6110.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6111.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6112.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6113.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6114.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6115.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6116.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6117.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6118.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6201.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6202.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6203.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6204.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6205.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6301.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6302.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6303.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6320.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6321.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6322.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6323.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6324.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6325.STS",
    "WIN-SUARIOMU79L.Dataset 1.XA6326.STS",
    "WIN-SUARIOMU79L.Dataset 1.XV1004.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV1005.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV1006.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV1029.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV2004.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV2005.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV2006.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV2029.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV3004.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV3005.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV3006.CV",
    "WIN-SUARIOMU79L.Dataset 1.XV3029.CV",
    "WIN-SUARIOMU79L.Dataset 1.ZI1603.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZI2603.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZI3603.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZI5113.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT1004.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT1005.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT1006.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT1029.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT2004.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT2005.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT2006.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT2029.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT3004.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT3005.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT3006.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZT3029.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5321.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5322.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5323.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5324.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5325.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5326.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5327.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5328.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5329.PV",
    "WIN-SUARIOMU79L.Dataset 1.ZV5330.PV",
    "WIN-SUARIOMU79L.{Diagnostics}.AdminRequests/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.HistoryMax-ms",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.HistoryRequests/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.LiveMax-ms",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.LiveRequests/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.LiveTVQs/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.NumClients",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.TagHandles",
    "WIN-SUARIOMU79L.{Diagnostics}.Reading.TVQs/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.CPU Usage Historian",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.CPU Usage Total",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Historian Handle Count",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Historian Thread Count",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Historian Working Set (memory)",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Memory Page",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Memory Physical",
    "WIN-SUARIOMU79L.{Diagnostics}.Sys.Memory Virtual",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.APICallCount/min",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.AxiomCallCount",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.AxiomLiveCallCount",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.AxiomLiveMax-ms",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.AxiomLivePixelMax-ms",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.AxiomTotalTVQS",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.GetRawCount",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.GetRawMax-ms",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.TotalConnections/min",
    "WIN-SUARIOMU79L.{Diagnostics}.Views.TotalTVQs/min",
    "WIN-SUARIOMU79L.{Diagnostics}.Writing.NumClients",
    "WIN-SUARIOMU79L.{Diagnostics}.Writing.Requests/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Writing.TagHandles",
    "WIN-SUARIOMU79L.{Diagnostics}.Writing.TVQ TimeExtensions/sec",
    "WIN-SUARIOMU79L.{Diagnostics}.Writing.TVQs/sec",
]

#  End Tags -------------------------------------------------------------}}}

if __name__ == "__main__":

    triton_c = CanaryRequest()

    long_time_period = "Now-1Month"
    short_time_period = "Now-1Hour"

    gps_coords_df = triton_c.request_gps_coords(short_time_period)

    deployment_state_df = triton_c.request_deployment_state(short_time_period)

    power_performance_data_df = triton_c.request_power_performance_data(
        short_time_period
    )

    triton_c.save()

    logging.info("Triton-C data successfully requested and saved!")
