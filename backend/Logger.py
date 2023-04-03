import logging

from FileManager import FileManager


class Logger:
    def __init__(self):
        self.file_manager = FileManager()

        logging.basicConfig(
            filename=self.file_manager.get_log_filepath(),
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%Y_%m_%d-%H:%M:%S",
            level=logging.INFO,
        )

    def info(self, module, message):
        logging.info(f"{module}: {message}")

    def warning(self, module, message):
        logging.warning(f"{module}: {message}")

    def error(self, module, message):
        logging.error(f"{module}: {message}")
