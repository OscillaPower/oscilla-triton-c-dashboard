from pathlib import Path


class DataFrameArchiver:
    @staticmethod
    def save_df(df, path, filename):
        # Ensure we do not modify the original dataframe
        df = df.copy()

        # json_path = Path(path, "json")
        # json_path.mkdir(exist_ok=True, parents=True)
        #
        # df.to_json(
        #     Path(json_path, f"{filename}.json"),
        #     orient="split",
        #     index="Timestamp",
        # )

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

        # Here we convert the column types to strings and convert them back
        # Parquet requires column types to be strings
        # Some mkhit functions require numbers
        # * wave.resource.energy_period
        # * wave.resource.significant_wave_height
        # * wave.resource.energy_flux

        column_save = df.columns

        df.columns = df.columns.astype(str)

        parquet_path = Path(path, "parquet")
        parquet_path.mkdir(exist_ok=True, parents=True)
        df.to_parquet(Path(parquet_path, f"{filename}.parquet"), index="Timestamp")

        df.columns = column_save
