from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
import sys

WIN_X = 500
WIN_Y = 500
WIN_WID = 800
WIN_HEI = 600

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(WIN_X, WIN_Y, WIN_WID, WIN_HEI)
        self.setWindowTitle("Canny's Little Helper")
        #self.setWindowIcon(QIcon('findimagelater'))
        self.statusBar().showMessage("[Initializing]")
        #self.menuBar().addMenu("file")

app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())