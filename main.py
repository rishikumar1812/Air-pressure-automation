import sys
from PyQt5.QtWidgets import QApplication
from ui import Dashboard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Dashboard()
    win.show()
    sys.exit(app.exec_())