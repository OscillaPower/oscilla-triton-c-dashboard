import traceback

from DirectoryManager import DirectoryManager
from Logger import Logger
from SQLite import SQLite
from TritonCHandler import TritonC
from FileManager import FileManager
from SpectraHandler import SpectraHandler
from PowerMatrixDataHandler import PowerMatrixDataHandler
from PowerMatrixImageGenerator import PowerMatrixImageGenerator


class Runner:
    def __init__(self):
        self.triton_c = TritonC()
        self.spectra = SpectraHandler()
        self.logger = Logger()

        self.db = SQLite()

        self.dirs = DirectoryManager()
        self.files = FileManager()

    # Run once to create all files necessary for running the application
    def create_files(self):
        self.db.create_tables()

    # Updates > 10 Hz? when WEC is online
    # Should run every 5 minutes
    # 5 minutes * 10 hz = 60 * 10 * 10 = 3000
    # If we are not collecting all data increase the value of CanaryRequester.default_max_size
    def collect_WEC_data(self):
        self.logger.info(__name__, "Starting collect_WEC_data...")
        try:
            last_10_min = "Now-10Min"
            # last_hour = "Now-1Hour"
            # last_day = "Now-1Hour"
            # last_month = "Now-1Month"

            self.triton_c.init_canary_request()

            self.triton_c.update_triton_c(last_10_min)

            # These are being run for legacy purposes. If the triton_c table works
            # nominally these commands (and db tables) should be deprecated
            self.triton_c.update_gps_coords(last_10_min)
            self.triton_c.update_deployment_state(last_10_min)
            self.triton_c.update_power_performance(last_10_min)
        except Exception as e:
            self.logger.error("collect_WEC_data", e)

        self.logger.info(__name__, "Finished collect_WEC_data!")

    # Set up the database from saved files
    # Should run once to initialize the database
    def populate_WEC_data(self):
        print("\tPopulating 'triton_c' table")
        self.triton_c.populate_triton_c()
        print("\tPopulating 'power_performance' table")
        self.triton_c.populate_power_performance()
        print("\tPopulating 'deployment_state' table")
        self.triton_c.populate_deployment_state()
        print("\tPopulating 'gps_coords' table")
        self.triton_c.populate_gps_coords()

    # Updates every hour
    # Should run every half hour
    def collect_spectra_data(self):
        self.logger.info(__name__, "Starting collect_spectra_data...")
        try:
            self.spectra.update_spectra()
        except Exception as e:
            self.logger.error("collect_spectra_data", e)
        self.logger.info(__name__, "Finished collect_spectra_data!")

    # Run every half hour
    def build_visualizations(self):
        self.logger.info(__name__, "Starting build_visualizations...")
        try:
            pto_col_names = [
                "PTO_Bow_Power_kW",
                "PTO_Port_Power_kW",
                "PTO_Starboard_Power_kW",
                "Total_Power_kW",
            ]

            spectra_df = self.spectra.read_spectra()

            power_df = self.triton_c.db.select_all_triton_c()

            viz_generator = PowerMatrixImageGenerator()

            for pto in pto_col_names:
                print(f"\tBuilding {pto} vizualization...")
                power_matrix_result = (
                    PowerMatrixDataHandler().calculate_power_matrix_mean(
                        power_df, spectra_df, pto
                    )
                )

                if power_matrix_result is not None:
                    power_matrix_data = power_matrix_result[0]
                    utc_timestamps = power_matrix_result[1]

                    earliest_timestamp = utc_timestamps.iloc[0]
                    latest_timestamp = utc_timestamps.iloc[-1]

                    if power_matrix_data is not None:
                        viz_generator.build_power_matrix_mean_visualization(
                            power_matrix_data,
                            pto,
                            f"Triton-C {pto}",
                            f"{earliest_timestamp} {latest_timestamp}",
                        )
        except Exception as e:
            self.logger.error("build_visualizations", e)

        self.logger.info(__name__, "Finished build_visualizations!")


if __name__ == "__main__":
    runner = Runner()
    print("Creating files...")

    runner.create_files()

    print("Populating WEC data...")
    runner.populate_WEC_data()

    print("Collecting spectra...")
    runner.collect_spectra_data()

    print("Building visualizations...")
    runner.build_visualizations()
