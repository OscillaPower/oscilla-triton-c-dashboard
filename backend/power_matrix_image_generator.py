# This script queries the Oscilla Power Canary server and produces a power matrix image
# that is saved to the local filesystem

import json
import os
from re import T
import time

import matplotlib.pyplot as plt
from mhkit import wave
import numpy as np
import pandas as pd
import requests


# Cleanly request data from the canary server
class CanaryRequest:
    def __init__(self):
        self.ip = "10.0.2.8"
        self.port = "55235"
        self.entry_url = f"http://{self.ip}:{self.port}/api/v2/"
        # self.endpoints = {
        #     "dataset_1": {"name": "WIN-SUARIOMU79L.Dataset 1", "tags": []}
        # }
        self.endpoints = {}

    def __repr__(self):
        return self.entry_url

    # Request data from the specified canary endpoint
    # Returns a dict of results
    # TODO: Handle errors accessing server
    def request_endpoint(self, endpoint, params):
        print(f"Requesting: {self.entry_url}{endpoint} with params: {params}")
        result = requests.get(f"{self.entry_url}{endpoint}", params)
        print(result.text)
        data = result.json()
        # An example result.text below:
        # {"statusCode":"Good","errors":[],"data":{"WIN-SUARIOMU79L.Dataset 1.Is_Deployed":[{"t":"2022-01-31T17:04:04.0000000-10:00","v":false},{"t":"2022-01-31T17:18:23.0000001-10:00","v":null},{"t":"2022-02-02T09:56:55.5000000-10:00","v":false},{"t":"2022-02-02T09:56:55.5000001-10:00","v":null},{"t":"2022-02-02T10:01:27.0000000-10:00","v":false},{"t":"2022-02-02T10:01:27.0000001-10:00","v":null},{"t":"2022-02-02T10:04:29.5000000-10:00","v":false},{"t":"2022-02-04T15:47:14.0000001-10:00","v":null},{"t":"2022-02-22T11:02:37.0000000-10:00","v":false},{"t":"2022-02-24T16:52:59.0000000-10:00","v":false}]},"continuation":null}

        return data

    def ping_server(self):
        result = self.request_endpoint("ping", {})
        if result["result"] == "success":
            print("Server is online!")
        else:
            print("Server is offline")
            exit()

    # Query the canary server for a list of endpoints
    def init_endpoints(self):
        data = self.request_endpoint("browseNodes", {})
        nodes = pd.DataFrame(data["nodes"])
        for col in nodes.columns:
            self.endpoints[col] = {}

    def init_endpoint_paths(self):
        for key in self.endpoints.keys():
            self.endpoints[key]["full_paths"] = []
            path = self.request_endpoint("browseNodes", {"path": key})
            nodes = path["nodes"]
            print(list(nodes.keys()))
            for node_key in nodes.keys():
                # print(self.endpoints.keys())
                # print(f"self.endpoints[{node_key}][{key}]['fullPath']")
                this_path = nodes[node_key]["fullPath"]
                print(this_path)
                self.endpoints[key]["full_paths"].append(this_path)

    # Populate self.endpoints[x]["tags"] with a list of tags from the server
    def request_tags_for_all_endpoints(self):
        for key in self.endpoints.keys():
            self.endpoints[key]["tags"] = []
            self.endpoints[key]["tag_paths"] = []
            full_paths = self.endpoints[key]["full_paths"]
            for path in full_paths:
                data = self.request_endpoint("browseTags", {"path": path})
                tags = data["tags"]
                # 0         WIN-SUARIOMU79L.Dataset 1.Axiom_Heartbeat
                # 1    WIN-SUARIOMU79L.Dataset 1.Bow_Sheave_Speed_rpm
                # 2    WIN-SUARIOMU79L.Dataset 1.Dominant_Wave_Period
                # 3             WIN-SUARIOMU79L.Dataset 1.Is_Deployed
                # 4                WIN-SUARIOMU79L.Dataset 1.Is_Maint
                # 5     WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Direction
                # 6        WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period
                # 7   WIN-SUARIOMU79L.Dataset 1.Port_Sheave_Speed_rpm
                # 8                 WIN-SUARIOMU79L.Dataset 1.Pos_Lat
                # 9           WIN-SUARIOMU79L.Dataset 1.Pos_Lat_m_rel
                # 10               WIN-SUARIOMU79L.Dataset 1.Pos_Long
                # 11         WIN-SUARIOMU79L.Dataset 1.Pos_Long_m_rel
                # 12           WIN-SUARIOMU79L.Dataset 1.Power_export
                # 13  WIN-SUARIOMU79L.Dataset 1.Stbd_Sheave_Speed_rpm
                # 14      WIN-SUARIOMU79L.Dataset 1.System_Deactivate
                # 15                WIN-SUARIOMU79L.Dataset 1.TEST_PV
                # 16            WIN-SUARIOMU79L.Dataset 1.Total_Power
                # 17        WIN-SUARIOMU79L.Dataset 1.Total_Power_Avg
                # 18            WIN-SUARIOMU79L.Dataset 1.Wave_Height
                sanitized_tags = [x.split(".")[-1] for x in tags]
                self.endpoints[key]["tags"].extend(sanitized_tags)
                self.endpoints[key]["tag_paths"].extend(tags)

    def request_timeseries(self, tag, duration_string, column_name_str):
        params = {
            "tags": [tag],
            "startTime": duration_string,
            "endTime": "Now",
        }

        response = self.request_endpoint("getTagData", params=params)
        data = response["data"][tag]
        # print(type(data))
        # print(data)
        # print(data[tag])
        # print(data[tag]["v"])

        # v = data[tag]["v"]

        # print(type(data))
        # print(type(data[0]))
        # print(data[0])

        timestamps = []
        values = []
        print(len(timestamps))
        print(len(values))

        for row in data:
            print(row)
            timestamps.append(row["t"])
            values.append(row["v"])

        print(len(timestamps))
        print(len(values))

        df = pd.DataFrame(
            zip(timestamps, values), columns=["timestamp", column_name_str]
        )
        # df = pd.DataFrame(data[tag]["v"]).T
        # df.columns = data[tag]["t"]
        # df = df.T
        # df.columns = [column_name_str]
        return df

    # Return a DataFrame of mean wave period data
    # Handle wrangling of canary data
    def request_mean_wave_period(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period", duration_string, "Te"
        )

    def request_wave_height(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Wave_Height", duration_string, "Hm0"
        )

    def request_total_power(self, duration_string):
        return self.request_timeseries(
            "WIN-SUARIOMU79L.Dataset 1.Total_Power", duration_string, "TotalPower"
        )

        # def extract_timeseries_to_dataframe(self, data, col_name):
        #     df = pd.DataFrame(data["v"]).T
        #     df.columns = data["t"]
        #     df = df.T
        #     df.columns = [col_name]
        #     return df


data_request = CanaryRequest()
print(data_request)

data_request.init_endpoints()

print(data_request.endpoints)

data_request.init_endpoint_paths()

print(data_request.endpoints)

data_request.request_tags_for_all_endpoints()

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
    "WIN-SUARIOMU79L.Dataset 1.TEST_PV",
    "WIN-SUARIOMU79L.Dataset 1.Total_Power",
    "WIN-SUARIOMU79L.Dataset 1.Total_Power_Avg",
    "WIN-SUARIOMU79L.Dataset 1.Wave_Height",
]


time_period = "Now-1Month"
mean_wave_period_te = data_request.request_mean_wave_period(time_period)
wave_height_Hm0 = data_request.request_wave_height(time_period)
total_power = data_request.request_total_power(time_period)
wave_energy_flux_J = total_power * mean_wave_period_te

exit()

# Requesting: http://10.0.2.8:55235/api/v2/browseTags with params: {'path': 'WIN-SUARIOMU79L.Dataset 1'}
# {"statusCode":"Good","errors":[],"tags":["WIN-SUARIOMU79L.Dataset 1.Axiom_Heartbeat","WIN-SUARIOMU79L.Dataset 1.Bow_Sheave_Speed_rpm","WIN-SUARIOMU79L.Dataset 1.Dominant_Wave_Period","WIN-SUARIOMU79L.Dataset 1.Is_Deployed","WIN-SUARIOMU79L.Dataset 1.Is_Maint","WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Direction","WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period","WIN-SUARIOMU79L.Dataset 1.Port_Sheave_Speed_rpm","WIN-SUARIOMU79L.Dataset 1.Pos_Lat","WIN-SUARIOMU79L.Dataset 1.Pos_Lat_m_rel","WIN-SUARIOMU79L.Dataset 1.Pos_Long","WIN-SUARIOMU79L.Dataset 1.Pos_Long_m_rel","WIN-SUARIOMU79L.Dataset 1.Power_export","WIN-SUARIOMU79L.Dataset 1.Stbd_Sheave_Speed_rpm","WIN-SUARIOMU79L.Dataset 1.System_Deactivate","WIN-SUARIOMU79L.Dataset 1.TEST_PV","WIN-SUARIOMU79L.Dataset 1.Total_Power","WIN-SUARIOMU79L.Dataset 1.Total_Power_Avg","WIN-SUARIOMU79L.Dataset 1.Wave_Height"],"continuation":null}
# Requesting: http://10.0.2.8:55235/api/v2/browseTags with params: {'path': 'WIN-SUARIOMU79L.{Diagnostics}'}
# {"statusCode":"Good","errors":[],"tags":["WIN-SUARIOMU79L.{Diagnostics}.AdminRequests/sec"],"continuation":null}

# exit()

# Building Visualizations

# https://www.ndbc.noaa.gov/station_realtime.php?station=51210
# First we need to download the wave data from WETS which is station 51210
# result = requests.get("https://www.ndbc.noaa.gov/data/realtime2/51210.data_spec")
# wave_data_fname = "51210_wave_data_test.txt"

# with open(wave_data_fname, "w") as f:
#     f.write(result.text)

ndbc_data_file = "wave_data.txt"
[raw_ndbc_data, meta] = wave.io.ndbc.read_file(ndbc_data_file)
ndbc_data = raw_ndbc_data.T

# Te = wave.resource.energy_period(ndbc_data)
Te = wave.resource.energy_period(mean_wave_period_te)
# Hm0 = wave.resource.significant_wave_height(ndbc_data)
Hm0 = wave.resource.significant_wave_height(wave_height_Hm0)

h = 30  # Set water depth to 30 meters

# Compute the energy flux from the NDBC spectra data and water depth
# Energy flux is the s density indexed by frequency
# J = wave.resource.energy_flux(ndbc_data, h)
J = wave.resource.energy_flux(ndbc_data, h)

Te = Te.squeeze()  # Energy period from spectra

Hm0 = Hm0["Hm0"]  # Significant wave height
J = J["J"]  # Wave energy flux from spectra

# random_seed = 10
# np.random.seed(random_seed)

for x in range(1, 3 + 1):
    # Generate random power values
    print("Building Visualization for PTO", x)
    P = pd.Series(np.random.normal(200, 40, 743), index=J.index)

    L = wave.performance.capture_length(P, J)
    Hm0_bins = np.arange(0, Hm0.values.max() + 0.5, 0.5)
    Te_bins = np.arange(0, Te.values.max() + 1, 1)

    LM_mean = wave.performance.capture_length_matrix(
        Hm0, Te, L, "mean", Hm0_bins, Te_bins
    )
    # LM_std = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, "std", Hm0_bins, Te_bins
    # )
    # LM_count = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, "count", Hm0_bins, Te_bins
    # )
    # LM_min = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, "min", Hm0_bins, Te_bins
    # )
    # LM_max = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, "max", Hm0_bins, Te_bins
    # )

    # LM_freq = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, "frequency", Hm0_bins, Te_bins
    # )

    # Demonstration of arbitrary matrix generator
    # PM_mean_not_standard = wave.performance.capture_length_matrix(
    #     Hm0, Te, P, "mean", Hm0_bins, Te_bins
    # )

    # Demonstration of passing a callable function to the matrix generator
    # LM_variance = wave.performance.capture_length_matrix(
    #     Hm0, Te, L, np.var, Hm0_bins, Te_bins
    # )

    # Create wave energy flux matrix using mean
    # JM is the wave energy flux matrix
    JM = wave.performance.wave_energy_flux_matrix(Hm0, Te, J, "mean", Hm0_bins, Te_bins)

    # Create power matrix using mean
    power_matrix_mean = wave.performance.power_matrix(LM_mean, JM)

    # Create power matrix using standard deviation
    # PM_std = wave.performance.power_matrix(LM_std, JM)

    # Show mean power matrix, round to 3 decimals
    power_matrix_mean.round(3)

    plt.figure(figsize=(8, 8))

    fig, ax = plt.subplots()

    ax = plt.gca()

    wave.graphics.plot_matrix(LM_mean, ax=ax)

    image_format = "svg"
    fig.savefig(
        f"../public/img/pto_{x}_lm_mean_latest.svg", format=image_format, dpi=1200
    )

    fig, ax = plt.subplots()

    ax = plt.gca()

    wave.graphics.plot_matrix(
        power_matrix_mean,
        xlabel="Te (s)",
        ylabel="Hm0 (m)",
        zlabel="Mean Power (kW)",
        show_values=False,
        ax=ax,
    )

    image_format = "svg"
    fig.savefig(
        f"../public/img/pto_{x}_pm_mean_latest.svg", format=image_format, dpi=1200
    )

    print("Visualization Complete for PTO", x)
