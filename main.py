import sys, os, math
import requests
import validators
import logging

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal

from my_gui import Ui_SplitDownloader

class dialog_box():
    def __init__(self):
        self.dialog = QtWidgets.QMessageBox()

    def warning_box(self, body ,title = "Warning"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Warning)
        self.dialog.setText(body)
        # msg.setInformativeText("This is additional information")
        self.dialog.setWindowTitle(title)
        # msg.setDetailedText("The details are as follows:")
        # msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.dialog.exec_()

    def question(self, body, title="Split Downloader"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Question)
        self.dialog.setText(body)
        self.dialog.setWindowTitle(title)
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        self.dialog.exec_()
        return self.dialog.clickedButton().text()

    def info_box(self, body ,title = "Info"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Information)
        self.dialog.setText(body)
        # msg.setInformativeText("This is additional information")
        self.dialog.setWindowTitle(title)
        # msg.setDetailedText("The details are as follows:")
        # msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        self.dialog.exec_()


class download_thread(QtCore.QThread):
    signal = QtCore.pyqtSignal(int)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.git_url = ""
        self.control = False
    # run method gets called when we start the thread
    def run(self):
        # tmpdir = tempfile.mkdtemp()
        # cmd = "git clone {0} {1}".format(self.git_url, tmpdir)
        # subprocess.check_output(cmd.split())
        # # git clone done, now inform the main thread with the output
        if self.control:
            for i in range(5):
                print("askar")
                self.sleep(3)
                self.signal.emit(i)
        else:
            for i in range(5):
                print("kani")
                self.sleep(3)
                self.signal.emit(i)

class download():
    def __init__(self, logger, url):
        self.logger = logger
        self.url = url
        self.dialogbox = dialog_box()

    def url_check(self):
        self.logger.info("Checking URL :" + str(self.url))
        if not validators.url(self.url):
            print("Enter a Valid URL")
            self.logger.error("The URL is invalid.")
            self.dialogbox.warning_box("Enter a Valid URL")
            return False
        else:
            self.logger.info("URL is Valid")
            return True

    def internet_check(self):
        self.logger.info("Checking Internet connectivity..")
        try:
            r = requests.head("https://www.google.com/", timeout=3)
            self.logger.info("Internet is connected..")
            return True
        except requests.ConnectionError as ex:
            print(ex)
            self.logger.error("Internet is not connected..")
            self.dialogbox.warning_box("Check your Internet Connection!")
            return False

    def get_headers(self):
        self.logger.info(f"Getting headers from {self.url}")
        self.file_size = self.content_type = self.accept_ranges = None
        try:
            res = requests.head(self.url)
            print(res)
            if res.ok:
                headers_items = res.headers
                print(headers_items)
                self.res = True
            else:
                self.logger.error("NO response" + str(res))
                self.res = False
                print("NO response" + str(res))
                self.dialogbox.warning_box("Invalid Response from URL: " + self.url)
                return
        except:
            print("HEADER NOT FOUND")
            self.logger.warning(f"Error in getting headers")
            self.res = False
            self.dialogbox.warning_box("Header not found")
            return
        self.file_size = headers_items.get('Content-Length')
        self.content_type = headers_items.get('Content-Type')
        self.accept_ranges = headers_items.get('Accept-Ranges')


    def file_name(self):
        self.logger.info(f"Getting file_name from {self.url}")
        return str(os.path.basename(self.url))

    def split_parts(self, chunk_size):
        chunk_size_b = chunk_size * 1024 * 1024
        number_of_chunks = math.ceil(int(self.file_size) / chunk_size_b)
        return [ _ for _ in range(1,number_of_chunks+1)]

    def test(self, data):
        print("data", data)

    def download(self, start_byte, end_byte, file_path):
        self.download_thread = download_thread()
        self.download_thread.signal.connect(self.test)
        self.download_thread.start()
        # range_headers = {'Range': f'bytes={start_byte}-{end_byte}'}
        # req = requests.get(self.url, stream=True, headers=range_headers)
        # with open(file_path, 'wb') as f:
        #     for chunk in req.iter_content(chunk_size=10 * 1048576):
        #         f.write(chunk)
        #         print("downloading..")
        # try:
        #
        #
        # except:
        #     print("Interupted")
        #     return False

        return True





class MyApp(QtWidgets.QMainWindow, Ui_SplitDownloader):

    def __init__(self, logger, parent=None):
        super(MyApp, self).__init__(parent)
        self.setupUi(self)
        self.parent = QtWidgets.QMainWindow()
        self.logger = logger
        self.onlyInt = QtGui.QIntValidator(1, 99999999)
        self.lineedit_chunk_size.setValidator(self.onlyInt)
        #actions
        self.chunk_size_download = 1
        self.dialogbox = dialog_box()
        self.button_exit.clicked.connect(self.exit_click)
        self.button_url_check.clicked.connect(self.url_check)
        self.button_browse_download.clicked.connect(self.download_select_folder)
        self.button_download.clicked.connect(self.download)

    def disable_download(self):
        self.label_file_size_output.setText("--")
        self.label_yes_no.setText("NO")
        self.lineedit_chunk_size.clear()
        self.combo_partselect.clear()
        self.lineedit_chunk_size.setEnabled(False)
        self.folder_download_line_edit.setEnabled(False)
        self.button_browse_download.setEnabled(False)

    def exit_click(self):
        self.logger.info("Exit pressed..")
        print("exit")
        button_value = self.dialogbox.question("Do you really want to exit?")
        if "yes" in button_value.lower():
            self.logger.info("Exit : Yes pressed..")
            sys.exit(1)
        else:
            self.logger.info("Exit : No pressed..")

    def url_check(self):
        self.disable_download()
        url = self.url_line_edit.text()
        self.download_obj = download(self.logger, url)
        if not self.download_obj.internet_check():
            return
        if not self.download_obj.url_check():
            return
        self.download_obj.get_headers()
        if not self.download_obj.res:
            return
        self.download_file_size_B = int(self.download_obj.file_size)
        self.download_content_type = self.download_obj.content_type
        self.download_accept_ranges = self.download_obj.accept_ranges
        print(self.download_file_size_B, self.download_content_type, self.download_accept_ranges)
        if self.download_content_type and "html" in self.download_content_type:
            print("The content is not downloadable")
            self.label_file_size_output.setText("--")
            self.label_yes_no.setText("NO")
            self.dialogbox.warning_box(f"The URL: {url} is not downloadable")
            self.logger.warning(f"The URL: {url} is not downloadable")
            return
        self.download_file_name = self.download_obj.file_name()
        if self.download_file_size_B:
            file_size = int(self.download_file_size_B)
            print(file_size)
            if file_size/1024/1024/1024 > 1:
                file_size = str(round(file_size/1024/1024/1024, 2)) + " GB"
            elif file_size/1024/1024 > 1:
                file_size = str(round(file_size/1024/1024, 2)) + " MB"
            elif file_size/1024 > 1:
                file_size = str(round(file_size/1024, 2)) + " KB"
            elif file_size:
                file_size = str(file_size) + " B"
            self.label_file_size_output.setText(file_size)
            self.logger.info(f"File size : {file_size}")
        else:
            self.label_file_size_output.setText("--")
        # check for file size < chunk size
        if int(self.download_file_size_B) < 1 *1024 *1024:
            self.logger.info("The file size is less than 1 MB")
            self.button_browse_download.setEnabled(True)
            self.folder_download_line_edit.setEnabled(True)
            self.is_split_downloadable = False
            self.dialogbox.info_box("The file size is less than 1MB.\nYou can download directly")
            return


        if self.download_accept_ranges and "bytes" in self.download_accept_ranges:
            self.label_yes_no.setText("YES")
            self.lineedit_chunk_size.setEnabled(True)
            self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)
            self.logger.info("The URL is split downloable")
            self.is_split_downloadable = True

        elif not self.download_accept_ranges:
            self.label_yes_no.setText("NO")
            self.lineedit_chunk_size.setEnabled(False)
            self.combo_partselect.setEnabled(False)
            # self.button_ok_part_select.setEnabled(False)
            self.dialogbox.info_box("The file is not splitable you can download as full")
            self.button_download.setEnabled(True)
            self.is_split_downloadable = False

        self.button_browse_download.setEnabled(True)
        self.folder_download_line_edit.setEnabled(True)

    def chunk_splitter(self):
        self.lineedit_chunk_size.editingFinished.disconnect()
        self.chunk_size_download = int(self.lineedit_chunk_size.text())
        spinbox = dialog_box()
        cnfm_chunk = spinbox.question("Do you want to proceed with the selected chunk size : " + str(self.chunk_size_download) + " MB?")
        if "no" in cnfm_chunk.lower():
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
            print(self.chunk_size_download)
        print(self.download_file_name)
        number_of_chunks = len(parts)
        print(number_of_chunks)

        #dict {file_name: [start_byte end byte]}
        self.chunk_dict = {}
        for chunk_number in range(number_of_chunks):
            if chunk_number:
                start = (chunk_number * self.chunk_size_download_B) + 1
            elif not chunk_number:
                start = chunk_number * self.chunk_size_download_B
            end = ((chunk_number + 1) * self.chunk_size_download_B)
            if end > self.download_file_size_B:
                end = self.download_file_size_B
            file_name = str(chunk_number+1) + "_" + self.download_file_name
            if file_name not in self.chunk_dict:
                self.chunk_dict[file_name] = [start, end]

        print(self.chunk_dict)


        self.combo_partselect.setEnabled(True)
        self.append_parts = list(map(lambda x: str(x) + "_" + self.download_file_name, parts))
        self.combo_partselect.clear()
        self.combo_partselect.addItems(list(map(str, self.append_parts)))
        self.lineedit_chunk_size.editingFinished.connect(self.chunk_splitter)


    def download_select_folder(self):
        print(self.chunk_size_download)
        if self.lineedit_chunk_size.isEnabled() and not self.combo_partselect.isEnabled():
            self.dialogbox.warning_box("Enter chunk size")
            return
        print(self.combo_partselect.isEnabled())
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

    def test(self, data):
        print("test", data)
        if data == 3:
            self.download_thread.terminate()

    def download(self):
        self.download_obj.download(1, 2, "askar")
        # self.download_thread = download_thread()
        # self.download_thread.signal.connect(self.test)
        # self.download_thread.start()

        # if not self.is_split_downloadable:
        #     self.download_path = Path(self.download_dir) / self.download_file_name
        #     print(self.download_path)
        # elif self.is_split_downloadable:
        #     file_name = self.combo_partselect.currentText()
        #     print(file_name)
        #     self.download_path = Path(self.download_dir) / file_name
        #     print(self.download_path)
        #     if file_name in self.chunk_dict:
        #         print(self.chunk_dict[file_name])
        #         start_byte = self.chunk_dict[file_name][0]
        #         end_byte = self.chunk_dict[file_name][1]
        #         self.download_obj.download(start_byte, end_byte, self.download_path )





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