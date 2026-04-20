import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from log_cleaning import process_data


class Canvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(10, 6))
        self.axs = self.fig.subplots(2, 2)
        super().__init__(self.fig)


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Machine Temperature Monitor")
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout()

        # TOP BAR
        top = QHBoxLayout()

        self.com = QComboBox()
        self.com.addItems(["COM1", "COM2", "COM3"])

        admin = QPushButton("Admin")

        top.addWidget(QLabel("COM:"))
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

        self.status.setStyleSheet("color: green; font-size:18px")

        bottom.addWidget(self.f_avg, 0, 0)
        bottom.addWidget(self.r_avg, 0, 1)
        bottom.addWidget(self.status, 1, 0, 1, 2)

        layout.addLayout(bottom)

        self.setLayout(layout)

        # TIMER
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(240000)

        self.update_ui()

    def update_ui(self):
        try:
            fs, fe, rs, re, favg, ravg = process_data()

            axs = self.canvas.axs
            for ax in axs.flat:
                ax.clear()

            colors = ['b','g','r','c','m','k']

            for i in range(6):
                if fs[i]: axs[0][0].plot(fs[i], color=colors[i])
                if rs[i]: axs[0][1].plot(rs[i], color=colors[i])
                if fe[i]: axs[1][0].plot(fe[i], color=colors[i])
                if re[i]: axs[1][1].plot(re[i], color=colors[i])

            axs[0][0].set_title("Front Start")
            axs[0][1].set_title("Rear Start")
            axs[1][0].set_title("Front End")
            axs[1][1].set_title("Rear End")

            self.canvas.draw()

            f = sum(favg)/6
            r = sum(ravg)/6

            self.f_avg.setText(f"Front Avg: {round(f,2)}°C")
            self.r_avg.setText(f"Rear Avg: {round(r,2)}°C")

            if f > 50 or r > 50:
                self.status.setText("● HIGH TEMP")
                self.status.setStyleSheet("color:red; font-size:18px")
            else:
                self.status.setText("● RUNNING")
                self.status.setStyleSheet("color:green; font-size:18px")

        except Exception as e:
            print(e)
            self.status.setText("● ERROR")
            self.status.setStyleSheet("color:red;")