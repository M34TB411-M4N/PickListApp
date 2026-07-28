from PyQt6.QtWidgets import QApplication, QMainWindow
import sys

winX = 500
winY = 500

winWid = 800
winHei = 600

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(winX, winY, winWid, winHei)

#window.statusBar().showMessage("[Initializing]")
#window.menuBar().addMenu("file")

app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())