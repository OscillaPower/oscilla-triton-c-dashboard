import matplotlib.pyplot as plt
from mhkit import wave

from FileManager import FileManager


class PowerMatrixImageGenerator:
    def __init__(self):
        self.file_manager = FileManager()

        self.fig_width = 8
        self.fig_height = 8
        self.img_format = "svg"
        self.dpi = 1200

    def build_power_matrix_mean_visualization(
        self, power_matrix_mean, pto_name, title, date_range, all_ns_timestamps
    ):
        plt.figure(figsize=(8, 8))
        plt.suptitle(title)
        plt.title(date_range)

        ax = plt.gca()

        wave.graphics.plot_matrix(
            power_matrix_mean,
            xlabel="Te (s)",
            ylabel="Hm0 (m)",
            zlabel="Mean Power (kW)",
            show_values=False,
            ax=ax,
        )

        plt.tight_layout()

        self.file_manager.archive_last_power_matrix(
            pto_name,
            self.img_format,
            start=all_ns_timestamps[0],
            end=all_ns_timestamps[-1],
        )

        plt.savefig(
            self.file_manager.get_power_matrix_latest_filename(
                pto_name, self.img_format
            ),
            format=self.img_format,
            dpi=self.dpi,
        )
