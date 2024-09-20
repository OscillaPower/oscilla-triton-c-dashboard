import math

from mhkit import wave
import numpy as np
import pandas as pd

from Logger import Logger

# Steps to generate the power performance Visualization
# Following: https://mhkit-software.github.io/MHKiT/wave_example.html
# 1. Load NDBC Buoy Data:
#     * https://www.ndbc.noaa.gov/station_realtime.php?station=51210
#     * Starting with "Realtime raw spectial wave data"
# 2.Compute Wave Metrics
#     1. Te (energy period)from NDBC spectra data
#     2. Hm0 (significant wave height )from NDBC data
#     3. J (energy flux)from NDBC data and site depth
# 3. Convert DataFrames to series
#     * We precalc these and pull them from the db
# 4. Gather power data
#     * Get all power data from the db `triton_c` table
#     * We precalc these and pull them from the db
# 5. Capture Power Matricies
#     * Calculate JM (wave energy flux)
#     * Create Power Matrix using np.mean
# 6. Create Graphics
#     * Plot power matrix

# We need to do this for each spectra so how do we save the data between iterations
# 1. Get all relevant power performance data from the wec `Is_Deployed` == True
# 2. Split the data into hours
#     * Filter out all data that is not 2hz or faster for the whole hour. Probably skip
#     * We don't actually do this, but the code to do this is commented out
#         * Per 62600-100 8.3.1
# 3. Calculate PM_Mean for each hour that exists from the NDBC spectra for that hour
#     * Remove any spectra that do not meet 62600-199 9.2.1. This is in the matrix
#         * Significant wave height (Hm0) >= 0.5m
#         * Energy period (Te) >= 1.0s
#     * The spectra is by the hour, so we need to reduce the data to an hourly average?
#     * The restriction is in the capture length calculation:  `L = wave.performance.capture_length(P, J)`
#         * The length of the power data needs to be the same as the length of the number of spectra entries


# Validate spectra, energy period (Te), significant wave height (Hm0), and WEC power
# Inputs are all spectra and all wec power
# Ensure inputs are consistent for each measurement period
# Ensure inputs meet IEC 62600-100
# Perform calculations on all data to get to PM_Mean calculation
class PowerMatrixDataHandler:
    # Aggregrate power data into hourly averaged chunks
    # Return a df of "UTC_Timestamps" and average power data in watts by

    def __init__(self):
        self.logger = Logger()

    def average_power_data(self, power_df, column):
        # Per 62600-100 8.3.1:
        # Filter out all data that is not 2hz or faster for the whole hour
        # Not used, but code is kept if necessary
        min_samples_per_hour = 2 * 60 * 60
        max_time_delta_ns = 1_000_000_000 / 2  # 2Hz

        averaging_frequency = "30min"

        # NDBC Buoy Times are in UTC, to match formats we convert our unix epoch ns timestamp to UTC
        power_df.sort_index(inplace=True)
        df = power_df

        df["UTC_Timestamp"] = pd.to_datetime(df.index)

        first_timestamp = df["UTC_Timestamp"].iloc[0]
        last_timestamp = df["UTC_Timestamp"].iloc[-1]

        # Move the first timestamp back to its hour
        first_timestamp = first_timestamp.floor(freq=averaging_frequency)

        # Move the last timestamp forward to its hour
        last_timestamp = last_timestamp.ceil(freq=averaging_frequency)

        # Get all data between the first and last timestamp by hour
        hours_power_data_is_available = pd.date_range(
            start=first_timestamp, end=last_timestamp, freq=averaging_frequency
        )

        valid_timestamps = []
        valid_power_kw = []

        for i in range(1, len(hours_power_data_is_available)):
            hour_start = hours_power_data_is_available[i - 1]
            hour_end = hours_power_data_is_available[i]

            # Get all power data between these hour_start and hour_end
            this_hour_power_data = df[
                (df["UTC_Timestamp"] >= hour_start) & (df["UTC_Timestamp"] < hour_end)
            ]

            if this_hour_power_data.empty:
                continue

            # The commented code below skips hours where the data rate is less that 2hz
            # if len(this_hour_power_data) < min_samples_per_hour:
            # continue

            # this_hour_power_data["Timestamp"] = this_hour_power_data.index
            # time_delta_ns = this_hour_power_data["Timestamp"].diff(periods=1)

            # if time_delta_ns.max() > max_time_delta_ns:
            #     continue

            # hour_power_data = this_hour_power_data[column]

            average_power_kw = this_hour_power_data[column].mean()

            if average_power_kw != 0 and math.isnan(average_power_kw) is False:
                valid_power_kw.append(average_power_kw)
                valid_timestamps.append(hour_start)

        return pd.DataFrame(
            [valid_timestamps, valid_power_kw], ["UTC_Timestamp", f"{column}"]
        ).T

    # Follow
    # https://github.com/MHKiT-Software/MHKiT-Python/blob/master/examples/wave_example.ipynb
    # to calculate the power matrix data
    def calculate_power_matrix_mean(self, power_df, spectra_df, column):
        valid_average_power_df = self.average_power_data(power_df, column)

        if valid_average_power_df.empty:
            self.logger.info(
                __name__, "Not enough power data to calculate power matrix. Returning.."
            )
            return

        combined_df = pd.concat([valid_average_power_df, spectra_df], axis="index")
        # Drop anything with nan
        combined_df = combined_df.dropna(how="any")

        if combined_df.empty:
            self.logger.info(
                __name__,
                "Not enough combined data to calculate power matrix. Returning..",
            )
            return

        P = np.array(
            np.abs(combined_df[column].to_numpy()),
            dtype="float64",
        )

        # These are pre calculated in SpectraHandler.update_spectra
        # Energy Period
        Te = combined_df["Te"].to_numpy()

        # Significant Wave Height
        Hm0 = combined_df["Hm0"].to_numpy()

        # Energy Flux
        J = combined_df["J"].to_numpy()

        # Capture Length
        L = wave.performance.capture_length(P, J)

        Hm0_bins = np.arange(0, Hm0.max() + 0.5, 0.5)
        Te_bins = np.arange(0, Te.max() + 1, 1)

        LM_mean = wave.performance.capture_length_matrix(
            Hm0, Te, L, "mean", Hm0_bins, Te_bins
        )

        # Wave Energy Flux Matrix using mean
        JM = wave.performance.wave_energy_flux_matrix(
            Hm0, Te, J, "mean", Hm0_bins, Te_bins
        )

        PM_mean = wave.performance.power_matrix(LM_mean, JM)

        # Timestamps are used for filenames?
        return (PM_mean, combined_df.index.astype("int64"))
