from PyQt5 import QtWidgets
from gui import Ui_SplitDownloader
import logging

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SplitDownloader = QtWidgets.QMainWindow()
    logging.basicConfig(filename="log.txt",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logger = logging.getLogger()
    ui = Ui_SplitDownloader(logger)
    ui.setupUi(SplitDownloader)
    SplitDownloader.show()
    sys.exit(app.exec_())