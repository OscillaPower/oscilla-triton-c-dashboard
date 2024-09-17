# This script packages this application for unpacking on the server
# To accomplish this we perform the following steps:
# 1. Create the `package/build` directory
#       * If there is a zip file in the package directory, change the name to the current date/time and save it to the `archive` directory
#       * Hash the file and do not archive if already in `archive` directory
# 2. Move all files and folders into this directory, keeping the same structure
#       * Ignore the files in the `ignore_files` list
#       * Ignore the folders in the `ignore_folders` list
# 3. Zip the `package/build` directory
# 4. Archive the built zip file
#       * Hash the file and do not archive if already in `archive` directory

from datetime import datetime
import os
import shutil
from distutils.dir_util import copy_tree

# import errno


class OscillaPackager:
    def __init__(self):
        self.frontend_dir = "frontend"
        self.backend_dir = "backend"

        self.package_dir = "package"
        self.build_dir = "build"
        self.archive_dir = "archive"

        self.ignore_files = [".gitignore", ".DS_Store"]
        self.ignore_folders = [
            ".git",
            ".next",
            "node_modules",
            ".ipynb_checkpoints",
            "package",
            "archive",
            "__pycache__",
        ]

        self.source_directory = os.path.dirname(os.path.realpath(__file__))
        self.destination_directory = os.path.join(
            self.source_directory, self.package_dir, self.build_dir
        )
        self.package_directory = os.path.join(self.source_directory, self.package_dir)
        self.archive_directory = os.path.join(self.source_directory, self.archive_dir)

        self.frontend_full_path = os.path.join(self.source_directory, self.frontend_dir)
        self.backend_full_path = os.path.join(self.source_directory, self.backend_dir)

    def cleanly_create_directory(self, full_path):
        try:
            os.makedirs(full_path)
        except FileExistsError:
            pass

    def init_output_directories(self):
        self.cleanly_create_directory(self.build_dir)
        self.cleanly_create_directory(self.archive_dir)

    def get_dir_contents(self, directory):
        working_dir = os.path.join(self.source_directory, directory)
        dir_contents = os.listdir(working_dir)
        return dir_contents

    def get_dir_files(self, directory):
        working_dir = os.path.join(self.source_directory, directory)
        dir_contents = self.get_dir_contents(directory)

        return [f for f in dir_contents if os.path.isfile(os.path.join(working_dir, f))]

    def get_dir_folders(self, directory):
        working_dir = os.path.join(self.source_directory, directory)
        dir_contents = self.get_dir_contents(directory)

        return [f for f in dir_contents if os.path.isdir(os.path.join(working_dir, f))]

    def remove_matches_from_list(self, input_list: list, ignore_list: list):
        result = []
        for input_element in input_list:
            has_match = False
            for ignore_element in ignore_list:
                if input_element == ignore_element:
                    has_match = True
                    break
            if has_match == False:
                result.append(input_element)

        return result

    def get_sanitized_file_list(self, directory):
        files = self.get_dir_files(directory)
        return self.remove_matches_from_list(files, self.ignore_files)

    def get_sanitized_folder_list(self, directory):
        folders = self.get_dir_folders(directory)
        return self.remove_matches_from_list(folders, self.ignore_folders)

    def get_sanitized_files_and_folders(self, directory):
        files = self.get_sanitized_file_list(directory)
        # return files
        folders = self.get_sanitized_folder_list(directory)
        return (files, folders)

    def package(self, name):
        this_base_dir = os.path.join(self.source_directory, name)
        this_destination = os.path.join(self.destination_directory, name)

        self.cleanly_create_directory(this_destination)

        # Remove existing files in destination directory
        for f in os.listdir(this_destination):
            os.remove(os.path.join(this_destination, f))

        this_zip_destination = os.path.join(self.package_directory, name)

        files, folders = self.get_sanitized_files_and_folders(this_base_dir)

        print(files)
        print(folders)

        for file in files:
            source_filename = os.path.join(this_base_dir, file)
            print(f"Copying file: {source_filename} to {this_destination}")
            shutil.copy(source_filename, this_destination)

        for folder in folders:
            print(
                f"Copying folder: {os.path.join(this_base_dir, folder)} to {os.path.join(this_destination, folder)}"
            )
            copy_tree(
                os.path.join(this_base_dir, folder),
                os.path.join(this_destination, folder),
            )

        now = datetime.now()
        date_string = now.strftime("%Y_%m%_%d_%H_%M_%S")
        build_fname = f"build_{date_string}"

        # if os.path.isfile(os.path.join(destination_directory, f"{self.build_dir}.zip")):
        #     print("build_file_exists")
        #     exit()

        print(f"Writing {this_zip_destination} from {this_destination}")

        shutil.make_archive(
            this_zip_destination,
            "zip",
            root_dir=this_destination,
            # base_dir=build_dir,
        )

        # shutil.rmtree(destination_directory)

    def package_frontend(self):
        self.package(
            # self.frontend_full_path,
            # os.path.join(self.package_directory, "frontend"),
            "frontend",
        )

    def package_backend(self):
        self.package(
            # self.backend_full_path,
            # os.path.join(self.destination_directory, "backend"),
            "backend",
        )

        # def get_files_and_folders(self, source_directory):
        #     dir_contents = os.listdir(source_directory)
        #     files = [
        #         f for f in dir_contents if os.path.isfile(os.path.join(source_directory, f))
        #     ]
        #     folders = [f for f in dir_contents if f not in files]

        #     # This is tedious, but we want to eliminate exact matches between the files and the ignored files
        #     relevant_files = []
        #     for file in files:
        #         has_match = False
        #         for ignore_file in ignore_files:
        #             if ignore_file == file:
        #                 has_match = True
        #                 break
        #         if has_match == False:
        #             relevant_files.append(file)

        #     relevant_folders = []
        #     for folder in folders:
        #         has_match = False
        #         for ignore_folder in ignore_folders:
        #             if ignore_folder == folder:
        #                 has_match = True
        #                 break
        #         if has_match == False:
        #             relevant_folders.append(folder)

        #     return (relevant_files, relevant_folders)


# relevant_files, relevant_folders = get_files_and_folders(source_directory)


# try:
#     os.makedirs(destination_directory)
# except FileExistsError:
#     pass
# try:
#     os.makedirs(archive_directory)
# except FileExistsError:
#     pass

# for file in relevant_files:
#     src = os.path.join(source_directory, file)
#     shutil.copy(src, destination_directory)

# for folder in relevant_folders:
#     copy_tree(
#         os.path.join(source_directory, folder),
#         os.path.join(destination_directory, folder),
#     )

# now = datetime.now()
# date_string = now.strftime("%Y_%m%_%d_%H_%M_%S")
# build_fname = f"build_{date_string}"

# Check for last build_file
# if os.path.isfile(os.path.join(destination_directory, f"{build_dir}.zip")):
#     print("build_file_exists")
#     exit()
# exit()

# print(destination_directory)

# shutil.make_archive(
#     os.path.join(package_directory, build_fname),
#     "zip",
#     root_dir=package_directory,
#     base_dir=build_dir,
# )

# shutil.rmtree(destination_directory)


# print("Oscilla App Packaged Successfully!")

if __name__ == "__main__":
    packager = OscillaPackager()

    # packager.package_frontend()
    packager.package_backend()
