import pandas as pd
import requests

from Logger import Logger

# Download and parse NDBC real time raw spectral wave data into pandas
# DataFrame
class NDBCRealTimeRawSpectralParser:
    def __init__(self, station_id):
        self.station_id = station_id
        self.realtime_raw_spectral_wave_data_url = (
            f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.data_spec"
        )
        self.logger = Logger()

    def request_latest(self):
        try:
            result = requests.get(self.realtime_raw_spectral_wave_data_url)
        except requests.RequestException as e:
            result = None
            self.logger.error(
                __name__,
                f"Request {self.realtime_raw_spectral_wave_data_url} failed with error {e}",
            )

        if result != None:
            return result.text

    def parse_latest_spec_file(self):
        raw_spec_file = self.request_latest()
        rows = []
        raw_timestamps = []
        columns = []

        if raw_spec_file is not None:
            spec = raw_spec_file.split("\n")

            for i in range(1, len(spec)):
                this_spec = spec[i].split(" ")

                if len(this_spec) > 1:
                    metadata = this_spec[0:6]
                    spectra = [float(x) for x in this_spec[6:-2:2]]
                    spectra_freq = this_spec[7::2]
                    spectra_freq = [
                        x.replace("(", "").replace(")", "") for x in spectra_freq
                    ]
                    spectra_freq = [float(x) for x in spectra_freq]
                    this_raw_timestamp = f"{metadata[0]}-{metadata[1]}-{metadata[2]}-{metadata[3]}:{metadata[4]}:00"
                    raw_timestamps.append(this_raw_timestamp)
                    columns = spectra_freq
                    rows.append(spectra)

        df = pd.DataFrame(
            data=rows,
            columns=columns,
        )
        df.index = pd.to_numeric(pd.to_datetime(raw_timestamps))
        df.index.name = "Timestamp"

        return (df, raw_timestamps)


if __name__ == "__main__":
    parser = NDBCRealTimeRawSpectralParser("51210")
    df, _ = parser.parse_latest_spec_file()
    print(df.info())
