import pandas as pd

from Logger import Logger


class DataHandler:
    def __init__(self):
        self.log = Logger()

    # Avoid database row duplication by uniquely insert timestamps into the
    # database. This works by first selecting timestamps in the database that match
    # the insertion dataframe timestamps then subtracting these timestamps from the
    # insertion timestamps. The Timestamp column in the database is UNIQUE and
    # will error out if there are multiple rows with the same timestamp
    def unique_insert(self, df, insert_function, extract_timestamp_function):
        try:
            # Unix epoch ns timestamps in a DataFrame
            # These are the timestamps in common between the insertion df and the database
            # Basically, these timestamps already exist
            existing_timestamps = extract_timestamp_function(pd.to_numeric(df.index))

            if existing_timestamps.empty is False:
                # Conversion of above into workable format (list of ints)
                existing_timestamps = list(
                    pd.to_numeric(existing_timestamps["Timestamp"])
                )

                # Unix ns timestamps of data ready for insertion
                insertion_timestamps = list(pd.to_numeric(df.index))

                # Calculation to get list of unix ns timestamps that are NOT in the database
                new_timestamps = list(
                    set(insertion_timestamps) - set(existing_timestamps)
                )
                # Conversion to workable format
                new_timestamps = pd.to_numeric(new_timestamps)

                # Filter the insertion dataframe to contain only new timestamps
                df = df[df.index.isin(new_timestamps)]

        # This function can error out if the existing timestamp function fails.
        # In this case we assume that the database has no data and we can
        # safely insert the entire incoming dataframe
        except pd.errors.DatabaseError as e:
            self.log.error(__name__, e)

        if len(df) > 0:
            insert_function(df)

        # Placeholder code if the above does not work
        # This is a suboptimal approach, but is reliable
        # for _, row in df.iterrows():
        # Convert the timestamp into nanoseconds since unix epoch
        # if convert_timestamp is True:
        # row["Timestamp"] = pd.to_datetime(row["Timestamp"]).value

        # try:
        #     this_df = pd.DataFrame([row])
        #     insert_function(this_df)
        # except sqlite3.IntegrityError:
        #     continue
