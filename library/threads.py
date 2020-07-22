import validators
import requests
import math, os
from PyQt5 import QtCore
import urllib.parse

from library.message_box import MessageBox


class Download():
    def __init__(self, logger, url):
        super().__init__()
        self.logger = logger
        self.url = url
        self.messagebox = MessageBox()

    def url_check(self):
        self.logger.info("Checking URL :" + str(self.url))
        if not validators.url(self.url):
            self.logger.error("The URL is invalid.")
            self.messagebox.warning_box("Enter a Valid URL")
            return False
        else:
            self.logger.info("URL is Valid")
            self.url = urllib.parse.unquote(self.url)
            return True

    def internet_check(self):
        self.logger.info("Checking Internet connectivity..")
        try:
            r = requests.head("https://www.google.com/", timeout=3)
            self.logger.info("Internet is connected..")
            return True
        except requests.ConnectionError as ex:
            self.logger.error("Internet is not connected..")
            self.messagebox.warning_box("Check your Internet Connection!")
            return False

    def get_headers(self):
        self.logger.info(f"Getting headers from {self.url}")
        self.file_size = self.content_type = self.accept_ranges = None
        try:
            res = requests.head(self.url)
            if res.status_code == 302:
                self.url = res.headers['Location']
                self.logger.info(f"URL redirected to {self.url}")
                res = requests.head(self.url)
            if res.ok:
                headers_items = res.headers
                self.logger.info(headers_items)
                self.res = True
            else:
                self.logger.error("NO response" + str(res))
                self.res = False
                self.messagebox.warning_box("Invalid Response from URL: " + self.url)
                return
        except:
            self.logger.warning(f"Error in getting headers")
            self.res = False
            self.messagebox.warning_box("Header not found")
            return
        content_length = headers_items.get('Content-Length')
        if content_length != None:
            self.file_size = int(headers_items.get('Content-Length'))
        self.content_type = headers_items.get('Content-Type')
        self.accept_ranges = headers_items.get('Accept-Ranges')
        if 'none' in str(self.accept_ranges).lower():
            self.accept_ranges=None

    def file_name(self):
        self.logger.info(f"Getting file_name from {self.url}")
        return str(os.path.basename(self.url))

    def split_parts(self, chunk_size):
        self.logger.info("splitting parts")
        self.chunk_size_b = chunk_size * 1024 * 1024
        number_of_chunks = math.ceil(self.file_size / self.chunk_size_b)
        return [_ for _ in range(1, number_of_chunks + 1)]

    def assign_download_variable(self, start_byte, end_byte, file_path, full):
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.file_path = file_path
        if full:
            self.full = True
        else:
            self.full = False


class DownloadThread(Download, QtCore.QThread):
    result_signal = QtCore.pyqtSignal(dict)
    error_signal = QtCore.pyqtSignal(bool)
    finish_signal = QtCore.pyqtSignal(bool)
    start_signal = QtCore.pyqtSignal(bool)

    def __init__(self, logger, url):
        QtCore.QThread.__init__(self)
        Download.__init__(self, logger, url)

    # run method gets called when we start the thread
    def run(self):
        try:
            range_headers = {'Range': f'bytes={self.start_byte}-{self.end_byte}'}
            req = requests.get(self.url, stream=True, headers=range_headers, timeout=30, allow_redirects=True)
            self.logger.info(f"Response: {req}")
            with open(self.file_path, 'wb') as f:
                chunk_size = 1048576
                progress_dict = {}
                self.start_signal.emit(True)
                for i, chunk in enumerate(req.iter_content(chunk_size=chunk_size)):
                    f.write(chunk)
                    current_file_size = os.path.getsize(self.file_path)
                    if self.full:
                        if not self.file_size:
                            self.file_size = 1
                        percentage = (current_file_size / self.file_size) * 100
                    else:
                        percentage = (current_file_size / self.chunk_size_b) * 100
                    progress_dict['current'] = [percentage, current_file_size]
                    self.result_signal.emit(progress_dict)
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection Error occured while downloading {str(os.path.basename(self.url))}")
            self.error_signal.emit(True)
        except:
            self.logger.warning(f"Error occured while downloading {str(os.path.basename(self.url))}")
            self.error_signal.emit(True)
        else:
            self.finish_signal.emit(True)


class MergeThread(QtCore.QThread):
    result_signal = QtCore.pyqtSignal(int)
    error_signal = QtCore.pyqtSignal(bool)
    finish_signal = QtCore.pyqtSignal(bool)
    start_signal = QtCore.pyqtSignal(bool)

    def __init__(self, logger, out_file_path, input_list):
        QtCore.QThread.__init__(self)
        self.logger = logger
        self.out_file_path = out_file_path
        self.input_list = input_list

    # run method gets called when we start the thread
    def run(self):
        try:
            self.start_signal.emit(True)
            self.logger.info("merging the files....")
            with open(self.out_file_path, 'wb') as f:
                for i, file in enumerate(self.input_list):
                    with open(file, 'rb') as inp:
                        f.write(inp.read())
                    self.result_signal.emit(i)
        except:
            self.logger.warning("Error while merging")
            self.error_signal.emit(True)
        self.finish_signal.emit(True)


class SplitThread(QtCore.QThread):
    result_signal = QtCore.pyqtSignal(int)
    error_signal = QtCore.pyqtSignal(bool)
    finish_signal = QtCore.pyqtSignal(bool)
    start_signal = QtCore.pyqtSignal(bool)
    def __init__(self, logger, split_input, split_list, chunk_size):
        QtCore.QThread.__init__(self)
        self.logger = logger
        self.split_file_path = split_input
        self.split_out_list = split_list
        self.chunk_size_split_B = chunk_size
        self.messagebox = MessageBox()

    # run method gets called when we start the thread
    def run(self):
        try:
            self.logger.info("Split thread run() starting")
            with open(self.split_file_path, 'rb') as file_in:
                for i, file in enumerate(self.split_out_list):
                    with open(file, 'wb') as file_out:
                        file_out.write(file_in.read(self.chunk_size_split_B))
                    self.result_signal.emit(i)
        except:
            self.logger.warning("error while splitting")
            self.error_signal.emit(True)
        else:
            self.logger.info("Splitting Finished")
            self.finish_signal.emit(True)

