import sys, os, math
import json
import time
import logging
import platform
import webbrowser
from pathlib import Path
from collections import OrderedDict
from PyQt5 import QtWidgets, QtGui

#external import
if "linux" in platform.platform().lower():
	import my_gui_ubuntu as Ui_SplitDownloader
elif "windows" in platform.platform().lower():
	import my_gui as Ui_SplitDownloader
from library.message_box import MessageBox
from library.threads import DownloadThread, MergeThread, SplitThread


class MyApp(QtWidgets.QMainWindow, Ui_SplitDownloader.Ui_SplitDownloader):
    def __init__(self, logger, parent=None):
        super(MyApp, self).__init__(parent)
        self.setupUi(self)
        self.parent = QtWidgets.QMainWindow()
        self.logger = logger
        self.onlyInt = QtGui.QIntValidator(1, 99999999)
        self.lineedit_chunk_size.setValidator(self.onlyInt)
        self.lineedit_chunk_size_split.setValidator(self.onlyInt)
        self.setFixedWidth(677)
        self.setFixedHeight(469)
        #actions
        self.chunk_size_download = 1
        self.messagebox = MessageBox()
        self.button_exit.clicked.connect(self.exit_click)
        self.button_url_check.clicked.connect(self.url_check)
        self.button_browse_download.clicked.connect(self.download_select_folder)
        self.button_download.clicked.connect(self.download)
        self.checkBox.stateChanged.connect(self.checked_download)
        #merge
        self.button_browse_merge_path_merge.clicked.connect(self.merge_folder_path)
        self.button_browse_folder_merge.clicked.connect(self.merge_contain_folder)
        self.button_browse_config_merge.clicked.connect(self.merge_config)
        self.button_cancel_merge.clicked.connect(self.merge_cancel)
        self.button_merge.clicked.connect(self.merge)
        #split
        self.button_browse_file_pt_split.clicked.connect(self.open_file_split)
        self.button_browse_out_pt_split.clicked.connect(self.out_folder_split)
        self.line_edit_file_path_split.textChanged.connect(self.check_file_split)
        self.button_split.clicked.connect(self.split)
        self.button_cancel_split.clicked.connect(self.split_cancel)

        # menu file action
        self.actionExit.triggered.connect(self.exit_click)
        self.actiongithub.triggered.connect(self.open_github)


    def open_github(self):
        self.logger.info("Opening github")
        webbrowser.open('https://github.com/AskarKani/split_downloader')

    def file_size_KB_MB_GB(self, file_size_b):
        if file_size_b:
            file_size = int(file_size_b)
            if file_size/1024/1024/1024 > 1:
                file_size = str(round(file_size/1024/1024/1024, 2)) + " GB"
            elif file_size/1024/1024 > 1:
                file_size = str(round(file_size/1024/1024, 2)) + " MB"
            elif file_size/1024 > 1:
                file_size = str(round(file_size/1024, 2)) + " KB"
            elif file_size:
                file_size = str(file_size) + " B"
            return file_size
        else:
            return "--"

    def url_check(self):
        self.logger.info("Checking url in MyApp")
        self.disable_download()
        self.url = self.url_line_edit.text()
        self.download_obj = DownloadThread(self.logger, self.url)
        if not self.download_obj.internet_check():
            return
        if not self.download_obj.url_check():
            return
        def url_update_elements(data):
            if self.download_obj.file_size != None:
                self.download_file_size_B = int(self.download_obj.file_size)
            else:
                self.download_file_size_B = 0
            self.download_content_type = self.download_obj.content_type
            self.download_accept_ranges = self.download_obj.accept_ranges
            self.logger.info(f"downlaod size,content_type,accept_range: {self.download_file_size_B},\
                             {self.download_content_type}, {self.download_accept_ranges}")
            if self.download_content_type and "html" in self.download_content_type:
                self.label_file_size_output.setText("--")
                self.checkBox.setEnabled(False)
                self.messagebox.warning_box(f"The URL: {self.url} is not downloadable")
                self.logger.warning(f"The URL: {self.url} is not downloadable")
                if self.download_obj.isRunning():
                    self.download_obj.terminate()
                return
            # get file name
            self.download_file_name = self.download_obj.file_name()
            if not self.download_file_name:
                self.logger.warning("Could not find the file name")
                self.messagebox.info_box("The file name is missing in the url." \
                                         "\nDownlaoding as \"no_file_name\"")
                self.download_file_name = "no_file_name"
            print("file_name", self.download_file_name)

            file_size = self.file_size_KB_MB_GB(self.download_file_size_B)
            if "--" not in file_size:
                self.label_file_size_output.setText(file_size)
                self.logger.info(f"File size : {file_size}")
            else:
                self.label_file_size_output.setText("--")

            if not self.download_file_size_B:
                self.messagebox.info_box("The file size not found in the URL.\nBut you can download directly")
                self.checkBox.setChecked(False)
                self.lineedit_chunk_size.setEnabled(False)
                self.combo_partselect.setEnabled(False)
                self.logger.info("The URL is not split downloadable")
                self.button_download.setEnabled(True)
                self.is_split_downloadable = False
                self.cancel_pressed_split_flag = False
                self.button_browse_download.setEnabled(True)
                self.folder_download_line_edit.setEnabled(True)
                if self.download_obj.isRunning():
                    self.download_obj.terminate()
                return
            # check for file size < 1 MB
            if int(self.download_file_size_B) < 1 * 1024 * 1024:
                self.logger.info("The file size is less than 1 MB")
                self.button_browse_download.setEnabled(True)
                self.folder_download_line_edit.setEnabled(True)
                self.checkBox.setEnabled(False)
                self.is_split_downloadable = False
                self.cancel_pressed_split_flag = False
                self.messagebox.info_box("The file size is less than 1MB.\nYou can download directly")
                if self.download_obj.isRunning():
                    self.download_obj.terminate()
                return
            if self.download_accept_ranges and "bytes" in self.download_accept_ranges:
                self.checkBox.setEnabled(True)
                self.checkBox.setChecked(True)
                self.lineedit_chunk_size.setEnabled(True)
                self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)
                self.logger.info("The URL is split downloable")
                self.is_split_downloadable = True
            elif not self.download_accept_ranges:
                self.checkBox.setChecked(False)
                self.lineedit_chunk_size.setEnabled(False)
                self.combo_partselect.setEnabled(False)
                self.messagebox.info_box("The file is not splitable you can download as full file")
                self.logger.info("The URL is not split downloadable")
                self.button_download.setEnabled(True)
                self.is_split_downloadable = False
            self.button_browse_download.setEnabled(True)
            self.folder_download_line_edit.setEnabled(True)

        def url_check_error():
            if self.download_obj.isRunning():
                self.logger.warning("error in url check")
                self.download_obj.terminate()
        self.download_obj.header_error_signal.connect(url_check_error)
        self.download_obj.header_finish_signal.connect(url_update_elements)
        self.download_obj.get_headers()
        self.download_obj.start()
        # if not self.download_obj.res:
        #     return


    def checked_download(self, checked):
        if checked:
            self.is_split_downloadable = True
            self.enable_download_full()
        else:
            self.is_split_downloadable = False
            self.disable_download_full()

    def disable_download_full(self):
        self.checkBox.setEnabled(True)
        self.lineedit_chunk_size.setEnabled(False)
        self.folder_download_line_edit.setEnabled(True)
        self.button_browse_download.setEnabled(True)
        self.combo_partselect.setEnabled(False)

    def enable_download_full(self):
        self.checkBox.setEnabled(True)
        self.lineedit_chunk_size.setEnabled(True)
        self.combo_partselect.setEnabled(True)

    def disable_download(self):
        self.label_file_size_output.setText("--")
        self.checkBox.setEnabled(False)
        self.lineedit_chunk_size.clear()
        self.combo_partselect.clear()
        self.lineedit_chunk_size.setEnabled(False)
        self.folder_download_line_edit.setEnabled(False)
        self.button_browse_download.setEnabled(False)
        self.cancel_pressed_split_flag = True

    def exit_click(self):
        self.logger.info("Exit pressed..")
        button_value = self.messagebox.question("Do you really want to exit?")
        if "yes" in button_value.lower():
            self.logger.info("Exit : Yes pressed..")
            sys.exit(1)
        else:
            self.logger.info("Exit : No pressed..")

    def chunk_splitter(self):
        self.logger.info("Entering chunk splitter")
        self.lineedit_chunk_size.editingFinished.disconnect()
        self.chunk_size_download = int(self.lineedit_chunk_size.text())
        spinbox = MessageBox()
        cnfm_chunk = spinbox.question(f"Do you want to proceed with the selected chunk size : "
                                      f"{str(self.chunk_size_download)} MB? \n "
                                      f"IMPORTANT! Chunk size should remain same till all parts download")
        if "no" in cnfm_chunk.lower():
            self.logger.info("No in chunk size dialog box")
            self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)
            self.lineedit_chunk_size.clear()
            return
        self.chunk_size_download_B = self.chunk_size_download * 1024 * 1024
        if self.chunk_size_download_B > self.download_file_size_B:
            self.logger.error("Chunk size is greater than file size")
            spinbox.warning_box("Chunk size is greater than file size")
            self.lineedit_chunk_size.clear()
            self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)
            return

        if self.chunk_size_download:
            parts = self.download_obj.split_parts(self.chunk_size_download)
        self.number_of_chunks = len(parts)
        self.logger.info(f"Number of chunks : {self.number_of_chunks}")

        #dict {file_name: [start_byte end byte]}
        self.chunk_dict = {}
        for chunk_number in range(self.number_of_chunks):
            if chunk_number:
                start = (chunk_number * self.chunk_size_download_B)
            elif not chunk_number:
                start = chunk_number * self.chunk_size_download_B
            end = ((chunk_number + 1) * self.chunk_size_download_B) - 1
            if end >= self.download_file_size_B:
                end = self.download_file_size_B
            file_name = str(chunk_number+1) + "_" + self.download_file_name
            if file_name not in self.chunk_dict:
                self.chunk_dict[file_name] = [start, end]
        self.logger.info(f"Chunk dict : {self.chunk_dict}")
        self.combo_partselect.setEnabled(True)
        self.append_parts = list(map(lambda x: str(x) + "_" + self.download_file_name, parts))
        self.combo_partselect.clear()
        self.combo_partselect.addItems(list(map(str, self.append_parts)))
        self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)


    def download_select_folder(self):
        if self.lineedit_chunk_size.isEnabled() and not self.combo_partselect.isEnabled():
            self.logger.warning("Enter chunk size")
            self.messagebox.warning_box("Enter chunk size")
            return
        self.logger.info("Select Folder to download")
        dialog = QtWidgets.QFileDialog()
        dir = dialog.getExistingDirectory(self.parent, 'Select an directory to download',
                                              os.getcwd(),
                                              QtWidgets.QFileDialog.ShowDirsOnly |
                                              QtWidgets.QFileDialog.DontResolveSymlinks)

        if dir:
            self.download_dir = dir
            self.logger.info("Folder selected for download : " + str(self.download_dir))
            self.folder_download_line_edit.setText(str(self.download_dir))
            self.button_download.setEnabled(True)

    def update_progress_bar(self, progress_dict):
        self.progressBar.setValue(progress_dict['current'][0])
        downloaded_size = round(progress_dict['current'][1]/ 1024 / 1024,1)
        if self.is_split_downloadable:
            if not (self.chunk_dict[self.file_name][1] + 1) % self.chunk_size_download_B:
                 self.label_download_status.setText(f"Downloading {self.progress_display_name} : {downloaded_size} MB / "
                                               f"{round(self.chunk_size_download_B/1024/1024,2)} MB")
            else:
                file_size = self.chunk_dict[self.file_name][1] - self.chunk_dict[self.file_name][0] + 1
                self.label_download_status.setText(f"Downloading {self.progress_display_name} : {downloaded_size} MB / "
                                               f"{round(file_size/1024/1024,1)} MB")
        else:
            self.label_download_status.setText(f"Downloading {self.progress_display_name} : {downloaded_size} MB / "
                                               f"{round(self.download_file_size_B / 1024 / 1024, 2)} MB")

    def download_cancel(self):
        self.button_cancel_download.clicked.disconnect(self.download_cancel)
        button_value = self.messagebox.question("Do you want to Cancel?")
        if "yes" in button_value.lower():
            if self.download_obj.isRunning():
                self.download_obj.terminate()
            self.label_download_status.setText("Status")
            self.button_download.setEnabled(True)
            self.progressBar.setValue(0)
            self.tab_on_off("on", [1, 2])
            self.cancel_pressed_disable_split()
        else:
            self.button_cancel_download.clicked.connect(self.download_cancel)
            return
        self.button_cancel_download.clicked.connect(self.download_cancel)
        self.button_cancel_download.setEnabled(False)
        return

    def download_pressed_disable_split(self):
        self.lineedit_chunk_size.setEnabled(False)
        self.url_line_edit.setEnabled(False)
        self.combo_partselect.setEnabled(False)
        self.button_url_check.setEnabled(False)
        self.button_browse_download.setEnabled(False)
        self.folder_download_line_edit.setEnabled(False)
        self.checkBox.setEnabled(False)
        self.button_cancel_download.setEnabled(True)

    def cancel_pressed_disable_split(self):
        self.url_line_edit.setEnabled(True)
        self.combo_partselect.setEnabled(True)
        self.button_url_check.setEnabled(True)
        self.button_browse_download.setEnabled(True)
        self.folder_download_line_edit.setEnabled(True)
        if self.download_accept_ranges and "bytes" in self.download_accept_ranges:
            self.is_split_downloadable = True
        elif not self.download_accept_ranges:
            self.is_split_downloadable = False
        if self.is_split_downloadable and self.cancel_pressed_split_flag:
            self.checkBox.setChecked(True)
            self.checkBox.setEnabled(True)
            self.lineedit_chunk_size.setEnabled(True)
        else:
            self.checkBox.setChecked(False)
            self.checkBox.setEnabled(False)
        self.button_download.setEnabled(True)
        self.button_cancel_download.setEnabled(False)
        self.progressBar.setValue(0)
        self.label_download_status.setText("Status")

    def download_finish(self, signal):
        self.download_obj.finish_signal.disconnect(self.download_finish)
        if self.is_split_downloadable:
            if self.file_name in self.chunk_dict:
                file_size = self.chunk_dict[self.file_name][1] - self.chunk_dict[self.file_name][0]
                update_dict = {
                    self.file_name: file_size + 1}
            with open(self.config_path_download, 'r+') as file:
                data = json.load(file)
                data = OrderedDict(data)
                data.update(update_dict)
                file.seek(0)
                json.dump(data, file, indent=4)
        if signal:
            download = MessageBox()
            download.info_box(f"The file: {self.progress_display_name} is downloaded in {self.download_dir}",
                              "Download Finished")
            self.cancel_pressed_disable_split()
            self.button_download.setEnabled(True)
            self.button_cancel_download.setEnabled(False)
            self.tab_on_off("on", [1, 2])

    def download_error(self, signal):
        if signal:
            self.messagebox.warning_box(f"Error occured while downloading {self.download_file_name}")
            self.cancel_pressed_disable_split()
            self.tab_on_off("on", [1, 2])

    def check_part_status(self):
        self.resume = False
        self.split_start_byte_res = 0
        # Check if 1st part and config files are already present
        self.config_path_download = Path(self.download_dir) / f"{self.download_file_name}.config"
        if f"1_{self.download_file_name}" == self.file_name:
            if self.file_name in os.listdir(self.download_dir):
                file_size = self.chunk_dict[self.file_name][1] - self.chunk_dict[self.file_name][0] + 1
                if os.path.getsize(self.download_path) == file_size:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to redownload?").lower():
                        return False
                else:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to resume?").lower():
                        return False
                    else:
                        self.split_start_byte_res = os.path.getsize(self.download_path) + self.chunk_dict[self.file_name][0]
                        self.resume = True
                        return True
            if os.path.isfile(self.config_path_download):
                return True
            self.config_dict_download = OrderedDict()
            self.config_dict_download['file_name'] = self.download_file_name
            self.config_dict_download['chunk_size'] = self.chunk_size_download_B
            self.config_dict_download['parts'] = self.number_of_chunks
            json_object = json.dumps(self.config_dict_download, indent=4)
            with open(self.config_path_download, 'w') as config:
                config.write(json_object)
            return True
        else:
            if self.file_name in os.listdir(self.download_dir):
                if not (self.chunk_dict[self.file_name][1] + 1) % self.chunk_size_download_B:
                    file_size = self.chunk_dict[self.file_name][1] - self.chunk_dict[self.file_name][0] + 1
                else:
                    file_size = self.chunk_dict[self.file_name][1] - self.chunk_dict[self.file_name][0]
                if os.path.getsize(self.download_path) == file_size:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to redownload?").lower():
                        return False
                else:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to resume?").lower():
                        return False
                    else:
                        self.split_start_byte_res = os.path.getsize(self.download_path) + self.chunk_dict[self.file_name][0]
                        self.resume = True
            if not os.path.isfile(Path(self.download_dir) / f"1_{self.download_file_name}"):
                self.logger.warning(f"1_{self.download_file_name} does not exist in {self.download_dir}")
                self.messagebox.warning_box("Download part 1 or Select the folder containing part 1 and config file")
                return False
            elif os.path.isfile(self.config_path_download):
                with open(self.config_path_download) as config:
                    self.config_dict_download = OrderedDict(json.load(config))
                if not self.config_dict_download['chunk_size'] == self.chunk_size_download_B:
                    self.logger.warning("Chunk size not matched with config file")
                    self.messagebox.info_box(f"Enter chunk size: {self.config_dict_download['chunk_size']/1024/1024} MB")
                    return False
            return True

    def start_download(self, status):
        if status:
            self.logger.info("Start Downloading...")
            self.label_download_status.setText("Downloading..")

    def download(self):
        self.folder_path_download = self.folder_download_line_edit.text()
        self.download_dir = self.folder_download_line_edit.text()
        if not os.path.isdir(self.download_dir):
            self.messagebox.warning_box(f"The folder {self.download_dir} path is incorrect")
            self.logger.warning(f"The folder {self.download_dir} path is incorrect")
            return
        if not self.is_split_downloadable:
            self.logger.info("Downloading as Full")
            if "no" in self.messagebox.question(f"Do you want to downlaod {self.download_file_name} ?").lower():
                return
            self.download_path = Path(self.download_dir) / self.download_file_name
            self.progress_display_name = self.download_file_name
            start_byte = 0
            resume = False
            if self.progress_display_name in os.listdir(self.download_dir):
                if os.path.getsize(self.download_path) == self.download_file_size_B:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to redownload?").lower():
                        return False
                else:
                    if "no" in self.messagebox.question(f"{self.download_file_name} already exists."
                                                        f"\nDo you want to resume?").lower():
                        return False
                    else:
                        start_byte = os.path.getsize(self.download_path)
                        resume = True
            end_byte = self.download_file_size_B
            self.download_obj.assign_download_variable(start_byte, end_byte, self.download_path, True, resume)
            self.download_obj.result_signal.connect(self.update_progress_bar)
            self.download_obj.finish_signal.connect(self.download_finish)
            self.download_obj.error_signal.connect(self.download_error)
            self.download_obj.start_signal.connect(self.start_download)
            self.button_cancel_download.clicked.connect(self.download_cancel)
            self.button_download.setEnabled(False)
            self.logger.info(f"Downloading file : {self.download_file_name}")
            self.download_obj.start()
            time.sleep(1)
            self.download_pressed_disable_split()
            self.tab_on_off("off", [1, 2])
        elif self.is_split_downloadable:
            self.logger.info("Downloading as Split")
            if not (self.lineedit_chunk_size.text() and self.combo_partselect.currentText()) :
                self.logger.warning("Select Chunk size and part")
                self.messagebox.warning_box("Select Chunk size and part")
                return
            self.file_name = self.combo_partselect.currentText()
            if "no" in self.messagebox.question(f"Do you want to downlaod {self.file_name} ?").lower():
                return
            self.download_path = Path(self.download_dir) / self.file_name
            self.progress_display_name = self.file_name
            #check part status
            if not self.check_part_status():
                return
            self.download_pressed_disable_split()
            if self.file_name in self.chunk_dict:
                end_byte = self.chunk_dict[self.file_name][1]
                if self.resume:
                    start_byte = self.split_start_byte_res
                    self.download_obj.assign_download_variable(start_byte, end_byte, self.download_path, False, True)
                else:
                    start_byte = self.chunk_dict[self.file_name][0]
                    self.download_obj.assign_download_variable(start_byte, end_byte, self.download_path, False)
                self.download_obj.result_signal.connect(self.update_progress_bar)
                self.download_obj.finish_signal.connect(self.download_finish)
                self.download_obj.error_signal.connect(self.download_error)
                self.download_obj.start_signal.connect(self.start_download)
                self.button_cancel_download.clicked.connect(self.download_cancel)
                self.button_download.setEnabled(False)
                self.logger.info(f"Downloading file : {self.file_name}")
                self.download_obj.start()
                self.button_cancel_download.setEnabled(True)
                self.tab_on_off("off", [1,2])


    def tab_on_off(self,tab_status, list_tab):
        if "off" in tab_status.lower():
            action = False
        elif "on" in tab_status.lower():
            action = True
        for tab in list_tab:
                self.Tab_MAIN.setTabEnabled(tab, action)

    ######################## MERGE ####################################
    def folder_select(self, header):
        dialog = QtWidgets.QFileDialog()
        dir = dialog.getExistingDirectory(self.parent, header,
                                          os.getcwd(),
                                          QtWidgets.QFileDialog.ShowDirsOnly |
                                          QtWidgets.QFileDialog.DontResolveSymlinks)
        if dir:
            return dir

    def merge_folder_path(self):
        merge_dir = self.folder_select("Select the folder to save the output")
        self.line_edit_merge_path_merge.setText(merge_dir)

    def merge_contain_folder(self):
        merge_contain_dir = self.folder_select("Select the folder containing the split files")
        self.line_edit_folder_merge.setText(merge_contain_dir)

    def merge_config(self):
        dialog = QtWidgets.QFileDialog()
        merge_config_file = dialog.getOpenFileName(self.parent, "Select the config file",
                                          os.getcwd(),
                                          "Config File (*.config)")

        if merge_config_file[0]:
            self.line_edit_folder_merge.setText(os.path.split(os.path.abspath(merge_config_file[0]))[0])
            self.line_edit_config.setText(merge_config_file[0])

    def merge_enable_disable(self, merge):
        if merge:
            self.line_edit_folder_merge.setEnabled(False)
            self.line_edit_config.setEnabled(False)
            self.line_edit_merge_path_merge.setEnabled(False)
            self.button_browse_merge_path_merge.setEnabled(False)
            self.button_browse_folder_merge.setEnabled(False)
            self.button_browse_config_merge.setEnabled(False)
            self.button_merge.setEnabled(False)
            self.button_cancel_merge.setEnabled(True)
        else:
            self.line_edit_folder_merge.setEnabled(True)
            self.line_edit_config.setEnabled(True)
            self.line_edit_merge_path_merge.setEnabled(True)
            self.button_browse_merge_path_merge.setEnabled(True)
            self.button_browse_folder_merge.setEnabled(True)
            self.button_browse_config_merge.setEnabled(True)
            self.button_merge.setEnabled(True)
            self.button_cancel_merge.setEnabled(False)
            self.progressBar.setValue(0)
            self.label_download_status.setText("Status")


    def merge(self):
        self.logger.info("################MERGER######################")
        self.merge_config_file = self.line_edit_config.text()
        self.merge_contain_dir = self.line_edit_folder_merge.text()
        self.merge_dir = self.line_edit_merge_path_merge.text()
        self.logger.info(f"config path: {self.merge_config_file}")
        self.logger.info(f"contain_dir: {self.merge_contain_dir}")
        self.logger.info(f"merge_dir: {self.merge_dir}")
        if not os.path.isfile(self.merge_config_file):
            self.logger.warning("Config file path is incorrect")
            self.messagebox.warning_box("Config file path is incorrect")
            return
        if not os.path.isdir(self.merge_contain_dir):
            self.logger.warning("Folder path is incorrect")
            self.messagebox.warning_box("Folder path is incorrect")
            return
        if not os.path.isdir(self.merge_dir):
            self.logger.warning("Merge output path is incorrect")
            self.messagebox.warning_box("Merge output path is incorrect")
            return
        with open(self.merge_config_file, 'r') as file:
            config_dict = json.load(file)

        expected_parts = int(config_dict.get('parts'))
        files ={}
        for i, value in enumerate(config_dict):
            if i > 2:
                files[value] = config_dict[value]
        config_file_name_sorted = [file for file in sorted(files)]
        check_part = expected_parts - len(config_file_name_sorted)
        if not check_part==0:
            self.logger.warning(f"{check_part} parts are missing")
            self.messagebox.warning_box(f"{check_part} parts are missing")
            return
        dir_list = os.listdir(self.merge_contain_dir)
        for file in config_file_name_sorted:
            if file not in dir_list:
                self.logger.warning(f"{file} is missing in {self.merge_contain_dir}")
                self.messagebox.warning_box(f"{file} is missing in {self.merge_contain_dir}")
                return
            check_size = config_dict[file] - os.path.getsize(Path(self.merge_contain_dir) / file)
            if not check_size < 2:
                self.logger.warning(f"{file} file size: {os.path.getsize(Path(self.merge_contain_dir) / file)} is less than chunk size"
                      f"\nRedownload or Resplit the file")
                self.messagebox.warning_box(f"{file} file size: {os.path.getsize(Path(self.merge_contain_dir) / file)} is less than chunk size"
                      f"\nRedownload or Resplit {file}")
                return
        if "no" in self.messagebox.question("Do you want to merge?").lower():
            self.logger.info("NO pressed in merge confirmation")
            return
        self.merge_enable_disable(True)
        #merge start
        def input_list_map(input):
            return Path(self.merge_contain_dir) / input

        def progress_merge(index):
            percentage = int(round(((index+1) / self.config_file_name_length)*100, 2))
            self.progressBar.setValue(percentage)
            self.logger.info(f"Merge Progress: {percentage} %")
            self.label_download_status.setText(f"Merging {index+1}/{self.config_file_name_length}")

        def error_merge(signal):
            if signal:
                self.messagebox.warning_box("Error occured while Merging")
                self.merge_enable_disable(False)
                self.tab_on_off("on", [0, 2])

        def finish_merge():
            self.logger.info(f"{config_dict['file_name']} is stored in {self.merge_dir}", "Merging Finished")
            self.messagebox.info_box(f"{config_dict['file_name']} is stored in {self.merge_dir}", "Merging Finished")
            self.merge_enable_disable(False)
            self.tab_on_off("on", [0, 2])
        input_list_path = list(map(input_list_map, config_file_name_sorted))
        self.config_file_name_length = len(input_list_path)
        self.merge_thread = MergeThread(self.logger, Path(self.merge_dir) / config_dict['file_name'],
                                        input_list_path)
        self.merge_thread.result_signal.connect(progress_merge)
        self.merge_thread.error_signal.connect(error_merge)
        self.merge_thread.finish_signal.connect(finish_merge)
        self.logger.info("merging thread started")
        self.tab_on_off("off",[0,2])
        self.merge_thread.start()

    def merge_cancel(self):
        if "no" in self.messagebox.question("Do you want to Cancel?").lower():
            return
        if self.merge_thread.isRunning():
            self.merge_thread.terminate()
        self.merge_enable_disable(False)
        self.tab_on_off("on", [0, 2])

    ############################ SPLIT ############################
    def open_file_split(self):
        dialog = QtWidgets.QFileDialog()
        split_file = dialog.getOpenFileName(self.parent, "Select the config file",
                                                   os.getcwd())
        if split_file[0]:
            self.lineedit_chunk_size_split.clear()
            self.label_file_size_output_split.setText("--")
            self.line_edit_file_path_split.setText(split_file[0])

    def out_folder_split(self):
        dir = self.folder_select("Select the folder to save the split files")
        if dir:
            if os.path.isdir(dir):
                self.line_edit_out_path_split.setText(dir)

    def check_file_split(self):
        self.logger.info("Checking the split file")
        self.split_file_path = self.line_edit_file_path_split.text()
        if not os.path.isfile(self.split_file_path):
            self.logger.warning("The split file path is not valid")
            self.messagebox.warning_box("Select or Enter a Valid Path")
            return
        self.split_file_size_B = os.path.getsize(self.split_file_path)
        file_size = self.file_size_KB_MB_GB(self.split_file_size_B)
        if "--" not in file_size:
            self.logger.info(f"Split file size {file_size}")
            self.label_file_size_output_split.setText(file_size)
        else:
            self.label_file_size_output_split.setText(file_size)
            self.messagebox.warning_box("file size not found")
            return
        if self.split_file_size_B < 1048577:
            self.logger.warning("Split file size is less than 1 MB")
            self.messagebox.warning_box("Split file size is less than 1 MB")
            return
        self.lineedit_chunk_size_split.setEnabled(True)
        self.lineedit_chunk_size_split.editingFinished.connect(self.chunk_splitter_split)

    def chunk_splitter_split(self):
        self.logger.info("Entering chunk splitter SPLIT")
        self.lineedit_chunk_size_split.editingFinished.disconnect()
        self.chunk_size_split = int(self.lineedit_chunk_size_split.text())
        spinbox = MessageBox()
        cnfm_chunk = spinbox.question(f"Do you want to proceed with the selected chunk size :"
                                      f" {str(self.chunk_size_split)} MB?")
        if "no" in cnfm_chunk.lower():
            self.logger.info("No in chunk size dialog box")
            self.lineedit_chunk_size_split.editingFinished.connect(self.chunk_splitter_split)
            self.lineedit_chunk_size_split.clear()
            return
        self.chunk_size_split_B = self.chunk_size_split * 1024 * 1024
        if self.chunk_size_split_B > self.split_file_size_B:
            self.logger.error("Chunk size is greater than file size")
            spinbox.warning_box("Chunk size is greater than file size")
            self.lineedit_chunk_size_split.clear()
            self.lineedit_chunk_size_split.editingFinished.connect(self.chunk_splitter_split)
            return
        self.logger.info("splitting parts in split")
        self.number_of_chunks_split = math.ceil(self.split_file_size_B / self.chunk_size_split_B)
        self.split_file_name = os.path.basename(self.split_file_path)
        self.logger.info(f"Number of chunks : {self.number_of_chunks_split}")

        # dict {file_name: [size]}
        self.chunk_dict_split = OrderedDict()
        for chunk_number in range(self.number_of_chunks_split):
            file_name = str(chunk_number + 1) + "_" + self.split_file_name
            if chunk_number+1 == self.number_of_chunks_split:
                if file_name not in self.chunk_dict_split:
                    self.chunk_dict_split[file_name] = self.split_file_size_B - (chunk_number*self.chunk_size_split_B)
            if file_name not in self.chunk_dict_split:
                self.chunk_dict_split[file_name] = self.chunk_size_split_B
        self.logger.info(f"Chunk dict : {self.chunk_dict_split}")
        self.lineedit_chunk_size_split.editingFinished.connect(self.chunk_splitter_split)

    def split(self):
        if not self.lineedit_chunk_size_split.text():
            self.logger.warning("Enter Chunk size")
            self.messagebox.warning_box("Enter Chunk size")
            return
        out_folder = self.line_edit_out_path_split.text()
        if not os.path.isdir(out_folder):
            self.messagebox.warning_box(f"Out Path {out_folder} is invalid")
            self.logger.warning(f"Out Path {out_folder} is invalid")
            return
        self.split_file_path = self.line_edit_file_path_split.text()
        if not os.path.isfile(self.split_file_path):
            self.logger.warning("The split file path is not valid")
            self.messagebox.warning_box("Select or Enter a Valid Path")
            return
        if "no" in self.messagebox.question("Do you want to split?").lower():
            self.logger.info("no pressed in split confirm message box")
            return
        #write to config file
        self.config_split_file = Path(out_folder) / f"{self.split_file_name}.config"
        self.config_dict_split = OrderedDict()
        self.config_dict_split['file_name'] = self.split_file_name
        self.config_dict_split['chunk_size'] = self.chunk_size_split_B
        self.config_dict_split['parts'] = self.number_of_chunks_split
        self.config_dict_split.update(self.chunk_dict_split)
        json_object = json.dumps(self.config_dict_split, indent=4)
        with open(self.config_split_file, 'w') as config:
            config.write(json_object)
        self.split_out_list = [Path(out_folder) / file for file in self.chunk_dict_split]
        def finish_split(signal):
            if signal:
                self.logger.info(f"Splitted files are stored in {out_folder}")
                self.messagebox.info_box(f"Splitted files are stored in {out_folder}","Spliting Finished")
                self.split_enable(False)
                self.tab_on_off("on", [0, 1])

        def start_split(signal):
            if signal:
                self.label_download_status.setText("Splitting...")

        def progress_split(index):
            percentage = round(((index + 1) / self.number_of_chunks_split) * 100, 2)
            self.progressBar.setValue(percentage)
            self.logger.info(f"Split Progress: {percentage} %")
            self.label_download_status.setText(f"Splitting {index + 1}/{self.number_of_chunks_split}")

        def error_split(signal):
            if signal:
                self.messagebox.warning_box("Error occured while Splitting")
                self.tab_on_off("on", [0, 1])
                self.split_enable(False)

        self.split_thread = SplitThread(self.logger, self.split_file_path, self.split_out_list, self.chunk_size_split_B,
                                        self.chunk_dict_split)
        self.tab_on_off("off", [0,1])
        self.split_thread.finish_signal.connect(finish_split)
        self.split_thread.error_signal.connect(error_split)
        self.split_thread.result_signal.connect(progress_split)
        self.split_thread.start_signal.connect(start_split)
        self.split_enable(True)
        self.split_thread.start()
        self.logger.info("split threading start")

    def split_enable(self, check):
        if check:
            self.line_edit_file_path_split.setEnabled(False)
            self.line_edit_out_path_split.setEnabled(False)
            self.button_browse_out_pt_split.setEnabled(False)
            self.button_browse_file_pt_split.setEnabled(False)
            self.lineedit_chunk_size_split.setEnabled(False)
            self.button_split.setEnabled(False)
            self.button_cancel_split.setEnabled(True)
        else:
            self.line_edit_file_path_split.setEnabled(True)
            self.line_edit_out_path_split.setEnabled(True)
            self.button_browse_out_pt_split.setEnabled(True)
            self.button_browse_file_pt_split.setEnabled(True)
            self.lineedit_chunk_size_split.setEnabled(True)
            self.button_split.setEnabled(True)
            self.button_cancel_split.setEnabled(False)
            self.progressBar.setValue(0)
            self.label_download_status.setText("Status")

    def split_cancel(self):
        if "no" in self.messagebox.question("Do you want to cancel?").lower():
            self.logger.info("NO pressed in Cancel")
            return
        self.logger.info("Split Cancel pressed ")
        if self.split_thread.isRunning():
            self.split_thread.terminate()
        self.split_enable(False)
        self.tab_on_off("on", [0, 1])


def main():
    app = QtWidgets.QApplication(sys.argv)
    logging.basicConfig(filename="log.txt",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger()
    downlaoder = MyApp(logger)
    downlaoder.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
