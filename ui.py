import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from log_processing import processlog

LOG_DIR = "C:/DGS/log"


class Canvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(10, 6))
        self.axs = self.fig.subplots(2, 2)
        super().__init__(self.fig)


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Temperature Monitor")
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout()

        # TOP BAR
        top = QHBoxLayout()

        self.com = QComboBox()
        self.com.addItems(["COM1", "COM2", "COM3"])

        admin = QPushButton("Admin")

        top.addWidget(QLabel("COM Port:"))
        top.addWidget(self.com)
        top.addStretch()
        top.addWidget(admin)

        layout.addLayout(top)

        # GRAPH
        self.canvas = Canvas()
        layout.addWidget(self.canvas)

        # BOTTOM
        bottom = QGridLayout()

        self.f_avg = QLabel("Front Avg: --")
        self.r_avg = QLabel("Rear Avg: --")
        self.status = QLabel("● RUNNING")

        bottom.addWidget(self.f_avg, 0, 0)
        bottom.addWidget(self.r_avg, 0, 1)
        bottom.addWidget(self.status, 1, 0, 1, 2)

        layout.addLayout(bottom)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(240000)

        self.update_ui()

    def update_ui(self):
        fs, fe, rs, re = processlog(LOG_DIR)

        axs = self.canvas.axs

        for ax in axs.flat:
            ax.clear()

        for arr in fs:
            if arr:
                axs[0][0].plot(arr)
        axs[0][0].set_title("Front Start")

        for arr in rs:
            if arr:
                axs[0][1].plot(arr)
        axs[0][1].set_title("Rear Start")

        for arr in fe:
            if arr:
                axs[1][0].plot(arr)
        axs[1][0].set_title("Front End")

        for arr in re:
            if arr:
                axs[1][1].plot(arr)
        axs[1][1].set_title("Rear End")

        self.canvas.draw()

        # AVG do changes here 
        f_vals = [arr[-1] for arr in fe if arr]
        r_vals = [arr[-1] for arr in re if arr]

        f_avg = sum(f_vals) / max(1, len(f_vals))
        r_avg = sum(r_vals) / max(1, len(r_vals))

        self.f_avg.setText(f"Front Avg: {round(f_avg,2)} °C")
        self.r_avg.setText(f"Rear Avg: {round(r_avg,2)} °C")

        if f_avg > 50 or r_avg > 50:
            self.status.setText("● HIGH TEMP")
            self.status.setStyleSheet("color:red")
        else:
            self.status.setText("● RUNNING")
            self.status.setStyleSheet("color:green")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())