import sqlite3

import pandas as pd

from FileManager import FileManager


class SQLite:
    def __init__(self):
        self.fm = FileManager()
        self.db_fname = self.fm.get_db_filepath()

        (self.con, self.cursor) = self.init_db_connection()

    # Initialize the sqlite database connection, gracefully handle any errors
    def init_db_connection(self):
        con = sqlite3.connect(self.db_fname)
        cursor = con.cursor()
        return (con, cursor)

    def finish(self):
        self.con.close()

    # Execute SQL, gracefully handle any errors
    # Return the execution result
    def execute_sql(self, command):
        try:
            result = self.cursor.execute(command)
            self.con.commit()
            return result.fetchall()
        except sqlite3.OperationalError:
            return None

    def create_tables(self):
        self.init_gps_table()
        self.init_deployment_state_table()
        self.init_power_performance_table()
        self.init_triton_c_table()
        self.init_spectra_table()

    # Get timestamps from table that are in `timestamp_list` Getting the both
    # the input `timestamp_list` and the output df['Timestamp'] should be unix
    # epoch ns integers. pd.to_numeric(datetime_list) handles this conversion
    # Returns a df with one "Timestamp" column and no index
    def select_matching_timestamps(self, table, timestamp_list):
        timestamp_list = pd.to_numeric(timestamp_list)
        df = pd.read_sql(
            f"""
SELECT Timestamp
    FROM {table}
    WHERE Timestamp in ({", ".join([f"'{str(x)}'" for x in timestamp_list])})
    ORDER BY Timestamp;
""",
            self.con,
        )
        df["Timestamp"] = pd.to_numeric(df["Timestamp"])
        return df

    def set_df_timestamp_to_index(self, df):
        if "Timestamp" in df.columns:
            df = df.set_index("Timestamp")
            df.drop(["Timestamp"], axis=1, inplace=True)

        df.index.name = "Timestamp"
        # Ensure that timestamps are unix epoch ns integers
        df.index = pd.to_numeric(df.index)

        return df

    # `triton_c` Table
    # Timestamp: Unix Time in nanoseconds as integer, UNIQUE allows one row per timestamp
    #     * Converted from pandas using pd.numeric(df.index) and converted to timestamp using pd.to_datetime(df.index)
    # Raw_Timestamp: Original timestamp as string
    # GPS_Lat: WEC latitude as float, WIN-SUARIOMU79L.Dataset 1.Pos_Lat
    # GPS_Lng: WEC longitude as float, WIN-SUARIOMU79L.Dataset 1.Pos_Long
    # Is_Deployed: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Deployed
    # Is_Maint: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Maint
    # PTO_Bow_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI1607.PV
    # PTO_Starboard_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI2607.PV
    # PTO_Port_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI3607.PV
    # Total_Power_kW: real, Summation of pto_bow_kw, pto_stbd_kw, and pto_port_kw
    # Mean_Wave_Period: real, WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period
    # Wave_Height: real, WIN-SUARIOMU79L.Dataset 1.Wave_Height
    def init_triton_c_table(self):
        command = """
CREATE TABLE triton_c(
    Timestamp INT UNIQUE,
    Raw_Timestamp TEXT DEFAULT NULL,
    GPS_Lat REAL DEFAULT NULL,
    GPS_Lng REAL DEFAULT NULL,
    Is_Deployed INT DEFAULT NULL,
    Is_Maint INT DEFAULT NULL,
    PTO_Bow_Power_kW REAL DEFAULT NULL,
    PTO_Starboard_Power_kW REAL DEFAULT NULL,
    PTO_Port_Power_kW REAL DEFAULT NULL,
    Total_Power_kW REAL DEFAULT NULL,
    Mean_Wave_Period REAL DEFAULT NULL,
    Mean_Wave_Height REAL DEFAULT NULL
)
        """
        self.execute_sql(command)

    def insert_triton_c(self, df):
        df.to_sql("triton_c", self.con, if_exists="append", index_label="Timestamp")
        self.con.commit()

    def select_all_triton_c(self):
        df = pd.read_sql(
            f"""
SELECT Timestamp, GPS_Lat, GPS_Lng, Is_Deployed, Is_Maint, PTO_Bow_Power_kW, PTO_Starboard_Power_kW, PTO_Port_Power_kW, Total_Power_kW, Mean_Wave_Period, Mean_Wave_Height
    FROM triton_c
    ORDER BY Timestamp DESC;
""",
            self.con,
            index_col="Timestamp",
        )

        return self.set_df_timestamp_to_index(df)

    def select_all_triton_c_with_power(self):
        df = pd.read_sql(
            f"""
SELECT Timestamp, GPS_Lat, GPS_Lng, Is_Deployed, Is_Maint, PTO_Bow_Power_kW, PTO_Starboard_Power_kW, PTO_Port_Power_kW, Total_Power_kW, Mean_Wave_Period, Mean_Wave_Height
    FROM triton_c
    WHERE Total_Power_kW is not NULL
    ORDER BY Timestamp DESC;
""",
            self.con,
            index_col="Timestamp",
        )

        return self.set_df_timestamp_to_index(df)

    def select_all_triton_c_average_power(self):
        df = pd.read_sql(
            f"""
SELECT
    strftime('%Y-%m-%d %H:', Raw_Timestamp) ||
    CASE
        WHEN CAST(strftime('%M', Raw_Timestamp) AS INTEGER) < 30 THEN '00'
        ELSE '30'
    END AS HalfHourInterval,
    AVG(Total_Power_kW) AS Avg_Total_Power_kW
    AVG(PTO_Bow_Power_kW) AS Avg_PTO_Bow_Power_kW
    AVG(PTO_Port_Power_kW) AS Avg_PTO_Port_Power_kW
    AVG(PTO_Starboard_Power_kW) AS Avg_PTO_Starboard_Power_kW
FROM triton_c
WHERE Total_Power_kW IS NOT NULL
GROUP BY HalfHourInterval
ORDER BY HalfHourInterval DESC;
""",
            self.con,
            index_col="Timestamp",
        )

        return self.set_df_timestamp_to_index(df)

    def select_is_deployed_triton_c(self):
        df = pd.read_sql(
            f"""
SELECT Timestamp, GPS_Lat, GPS_Lng, Is_Deployed, Is_Maint, PTO_Bow_Power_kW, PTO_Starboard_Power_kW, PTO_Port_Power_kW, Total_Power_kW, Mean_Wave_Period, Mean_Wave_Height
    FROM triton_c
    WHERE Is_Deployed = 1,
    ORDER BY Timestamp DESC;
""",
            self.con,
            index_col="Timestamp",
        )

        return self.set_df_timestamp_to_index(df)

    def select_is_maint_triton_c(self):
        df = pd.read_sql(
            f"""
SELECT Timestamp, GPS_Lat, GPS_Lng, Is_Deployed, Is_Maint, PTO_Bow_Power_kW, PTO_Starboard_Power_kW, PTO_Port_Power_kW, Total_Power_kW, Mean_Wave_Period, Mean_Wave_Height
    FROM triton_c
    WHERE Is_Maint = 1,
    ORDER BY Timestamp DESC;
""",
            self.con,
            index_col="Timestamp",
        )
        return self.set_df_timestamp_to_index(df)

    def select_matching_triton_c_timestamps(self, timestamp_list):
        return self.select_matching_timestamps("triton_c", timestamp_list)

    # TODO: Do we use this?
    def select_most_recent_triton_c_timestamp(self, timestamp_list):
        df = pd.read_sql(
            f"""
SELECT Timestamp
    FROM triton_c
    WHERE Timestamp in ({", ".join([f"'{str(x)}'" for x in timestamp_list])})
    ORDER BY Timestamp DESC
    LIMIT 20000;
""",
            self.con,
            index_col="Timestamp",
        )
        return df

    # `gps` Table
    # Timestamp: Unix Time as integer, UNIQUE allows one row per timestamp
    # Raw_Timestamp: Original timestamp as string
    # GPS_Lat: WEC latitude as float, WIN-SUARIOMU79L.Dataset 1.Pos_Lat
    # GPS_Lng: WEC longitude as float, WIN-SUARIOMU79L.Dataset 1.Pos_Long
    def init_gps_table(self):
        command = """
CREATE TABLE gps_coords(
    Timestamp INT UNIQUE,
    Raw_Timestamp TEXT DEFAULT NULL,
    GPS_Lat REAL DEFAULT NULL,
    GPS_Lng REAL DEFAULT NULL
)
        """
        self.execute_sql(command)

    def insert_gps_coords(self, gps_coords_df):
        gps_coords_df.to_sql(
            "gps_coords",
            self.con,
            if_exists="append",
            index_label="Timestamp",
        )
        self.con.commit()

    def select_gps_coords(self, num_entries):
        df = pd.read_sql(
            f"""
SELECT Timestamp, GPS_Lat, GPS_Lng
    FROM gps_coords
    ORDER BY Timestamp
    LIMIT {num_entries};
        """,
            self.con,
            index_col="Timestamp",
        )
        return self.set_df_timestamp_to_index(df)

    def select_matching_gps_timestamps(self, timestamp_list):
        return self.select_matching_timestamps("gps_coords", timestamp_list)

    # `deployment_state` Table
    # Timestamp: Unix Time as integer, UNIQUE allows one row per timestamp
    # Raw_Timestamp: Original timestamp as string
    # Is_Deployed: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Deployed
    # Is_Maint: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Maint
    def init_deployment_state_table(self):
        command = """
CREATE TABLE deployment_state(
    Timestamp INT UNIQUE,
    Raw_Timestamp TEXT DEFAULT NULL,
    Is_Deployed INT DEFAULT NULL,
    Is_Maint INT DEFAULT NULL
)"
        """
        self.execute_sql(command)

    def insert_deployment_state(self, df):
        df.to_sql(
            "deployment_state",
            self.con,
            if_exists="append",
            index="Timestamp",
        )
        self.con.commit()

    def select_deployment_state(self, num_entries):
        df = pd.read_sql(
            f"""
SELECT Timestamp, Is_Deployed, Is_Maint
    FROM deployment_state
    ORDER BY Timestamp
    LIMIT {num_entries};
        """,
            self.con,
            index_col="Timestamp",
        )
        return self.set_df_timestamp_to_index(df)

    def select_matching_deployment_state_timestamps(self, timestamp_list):
        return self.select_matching_timestamps("deployment_state", timestamp_list)

    # `power_performance` Table
    # Timestamp: Unix Time as integer, UNIQUE allows one row per timestamp
    # Raw_Timestamp: Original timestamp as string
    # Is_Deployed: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Deployed
    # Is_Maint: bool 0 or 1 as integer, WIN-SUARIOMU79L.Dataset 1.Is_Maint
    # PTO_Bow_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI1607.PV
    # PTO_Starboard_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI2607.PV
    # PTO_Port_Power_kW: real, WIN-SUARIOMU79L.Dataset 1.JI3607.PV
    # Total_Power_kW: real, Summation of pto_bow_kw, pto_stbd_kw, and pto_port_kw
    # Mean_Wave_Period: real, WIN-SUARIOMU79L.Dataset 1.Mean_Wave_Period
    # Wave_Height: real, WIN-SUARIOMU79L.Dataset 1.Wave_Height
    def init_power_performance_table(self):
        command = """
CREATE TABLE power_performance(
    Timestamp INT UNIQUE,
    Raw_Timestamp TEXT DEFAULT NULL,
    Is_Deployed INT DEFAULT NULL,
    Is_Maint INT DEFAULT NULL,
    PTO_Bow_Power_kW REAL DEFAULT NULL,
    PTO_Starboard_Power_kW REAL DEFAULT NULL,
    PTO_Port_Power_kW REAL DEFAULT NULL,
    Total_Power_kW REAL DEFAULT NULL,
    Mean_Wave_Period REAL DEFAULT NULL,
    Mean_Wave_Height REAL DEFAULT NULL
)
        """
        self.execute_sql(command)

    def insert_power_performance(self, df):
        df.to_sql(
            "power_performance",
            self.con,
            if_exists="append",
            index="Timestamp",
        )
        self.con.commit()

    def select_power_performance(
        self, is_maint=False, is_deployed=False, num_entries=None
    ):
        where_args = []
        limit_args = ""

        if is_maint is True:
            where_args.append("WHERE Is_Maint = 1")

        if is_deployed is True:
            where_args.append("WHERE Is_Deployed = 1")

        if num_entries is not None:
            limit_args = f"LIMIT {num_entries}"

        df = pd.read_sql(
            f"""
SELECT Timestamp, Is_Deployed, Is_Maint, PTO_Bow_Power_kW, PTO_Starboard_Power_kW, PTO_Port_Power_kW, Total_Power_kW, Mean_Wave_Period, Mean_Wave_Height
    FROM power_performance
    {' '.join(where_args)}
    ORDER BY Timestamp {limit_args};
        """,
            self.con,
            index_col="Timestamp",
        )

        return self.set_df_timestamp_to_index(df)

    def select_all_power_performance(self):
        return self.select_power_performance()

    def select_is_deployed_power_performance(self):
        return self.select_power_performance(is_deployed=True)

    def select_is_maint_power_performance(self):
        return self.select_power_performance(is_maint=True)

    def select_matching_power_performance_timestamps(self, timestamp_list):
        return self.select_matching_timestamps("power_performance", timestamp_list)

    # `spectra` Table
    # Timestamp: Unix Time as integer, UNIQUE allows one row per timestamp
    # Raw_Timestamp: Original timestamp as string
    # Te: Real
    # Hm0: Real
    # J: Real
    def init_spectra_table(self):
        command = """
CREATE TABLE spectra(
    Timestamp INT UNIQUE,
    Raw_Timestamp TEXT DEFAULT NULL,
    Spectral_Hm0 REAL DEFAULT NULL,
    Spectral_Te REAL DEFAULT NULL,
    Spectral_J REAL DEFAULT NULL,
    Spectral_Tavg REAL DEFAULT NULL,
    Spectral_Tm REAL DEFAULT NULL,
    Spectral_Tp REAL DEFAULT NULL,
    Spectral_Tz REAL DEFAULT NULL,
    WMI_waveHs REAL DEFAULT NULL,
    WMI_waveTp REAL DEFAULT NULL,
    WMI_waveTa REAL DEFAULT NULL,
    WMI_waveDp REAL DEFAULT NULL,
    WMI_wavePeakPSD REAL DEFAULT NULL,
    WMI_waveTz REAL DEFAULT NULL
)
        """
        self.execute_sql(command)

    def insert_spectra(self, df):
        # df.to_sql("spectra", self.con, if_exists="append", index_label="Timestamp")
        df.to_sql("spectra", self.con, if_exists="append", index=False)
        self.con.commit()

    def select_spectra(self):
        df = pd.read_sql(
            f"""
SELECT Timestamp, Raw_Timestamp, Spectral_Te, Spectral_Hm0, Spectral_J
    FROM spectra
    ORDER BY Timestamp;
""",
            self.con,
            index_col="Timestamp",
        )

        df = df.rename(columns=lambda x: x.strip("Spectral_"))

        return self.set_df_timestamp_to_index(df)

    def select_matching_spectra_timestamps(self, timestamp_list):
        return self.select_matching_timestamps("spectra", timestamp_list)
