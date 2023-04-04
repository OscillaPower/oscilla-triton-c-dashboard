import os
from pathlib import Path

# DirectoryManager abstracts directory names. This provides multiple benefits:
#   1. Co-locates directory names for all other classes
#   2. Allows the server and developer to use common functions and only hard codes the server directory in one place
#   3. Creates directories that don't exist
class DirectoryManager:
    def __init__(self):
        if os.getenv("TRITON_C_SERVER") != None:
            self.base_dir = Path("/home/nrel@oscillapower.local/dashboard")
        else:
            # We should be in the "backend" directory
            self.this_dir = Path.cwd()
            self.base_dir = self.this_dir.parents[0]

        # Base locations
        self.log_dir = self.build_base_path("logs")
        self.backend_dir = self.build_base_path("backend")
        self.frontend_dir = self.build_base_path("frontend")
        self.package_dir = self.build_base_path("package")
        self.package_archive_dir = self.build_base_path("package_archive")
        self.data_dir = self.build_base_path("data")

        # Path can safely handle slashes in the filename
        self.triton_c = self.build_path(f"{self.data_dir}/triton_c")
        self.raw_spectra = self.build_path(f"{self.data_dir}/raw_spectra")
        self.spectra_calc = self.build_path(f"{self.data_dir}/spectra_calc")

        # These are old directories that are used to populate data
        self.power_performance = self.build_path(f"{self.data_dir}/power_performance")
        self.gps_coords = self.build_path(f"{self.data_dir}/gps_coords")
        self.deployment_state = self.build_path(f"{self.data_dir}/deployment_state")

        self.visualization_dir = self.build_path(
            f"{self.frontend_dir}/public/img/viz_latest"
        )
        self.visualization_archive_dir = self.build_path(
            f"{self.frontend_dir}/public/img/viz_archive"
        )

    def build_base_path(self, dir_string):
        this_path = self.base_dir.joinpath(dir_string)
        return self.create_dir(this_path)

    def build_path(self, dir_string):
        this_path = Path(dir_string)
        return self.create_dir(this_path)

    def create_dir(self, path):
        if path.exists() is False:
            path.mkdir()
        return path


if __name__ == "__main__":
    dirs = DirectoryManager()
    print(dirs.log_dir)
    print(dirs.power_performance)
