import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from log_processing import processlog   # your function

LOG_DIR = "C:/DGS/log"


# ─────────────────────────────
# GRAPH FUNCTION
# ─────────────────────────────
def temp_graph(ax, arrays, title, color_set):
    for i, arr in enumerate(arrays):
        if arr:
            ax.plot(arr, color=color_set[i % len(color_set)], linewidth=2)

    ax.set_title(title, color='white')
    ax.set_facecolor('#1E293B')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')


# ─────────────────────────────
# CANVAS
# ─────────────────────────────
class Canvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(10, 6))
        self.axs = self.fig.subplots(2, 2)
        super().__init__(self.fig)


# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Temperature Monitor Dashboard")
        self.setGeometry(100, 100, 1300, 850)

        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A;
                color: #E2E8F0;
                font-family: Arial;
            }
        """)

        main_layout = QVBoxLayout()

        # ───────── TOP BAR ─────────
        top = QHBoxLayout()

        self.com = QComboBox()
        self.com.addItems(["COM1", "COM2", "COM3"])
        self.com.setStyleSheet("""
            background-color:#1E293B;
            padding:6px;
            border-radius:6px;
        """)

        admin = QPushButton("Admin Login")
        admin.setStyleSheet("""
            background-color:#22C55E;
            padding:8px;
            border-radius:6px;
            color:white;
        """)

        top.addWidget(QLabel("COM Port:"))
        top.addWidget(self.com)
        top.addStretch()
        top.addWidget(admin)

        main_layout.addLayout(top)

        # ───────── GRAPH AREA ─────────
        self.canvas = Canvas()
        main_layout.addWidget(self.canvas)

        # ───────── BOTTOM PANEL ─────────
        bottom = QGridLayout()

        self.f_avg = QLabel("42.35 °C")
        self.r_avg = QLabel("39.80 °C")
        self.status = QLabel("● RUNNING")

        self.f_avg.setStyleSheet("font-size:28px; font-weight:bold; color:#38BDF8;")
        self.r_avg.setStyleSheet("font-size:28px; font-weight:bold; color:#4ADE80;")
        self.status.setStyleSheet("font-size:30px; font-weight:bold; color:#22C55E;")

        bottom.addWidget(QLabel("FRONT AVG"), 0, 0)
        bottom.addWidget(QLabel("REAR AVG"), 0, 1)
        bottom.addWidget(QLabel("STATUS"), 0, 2)

        bottom.addWidget(self.f_avg, 1, 0)
        bottom.addWidget(self.r_avg, 1, 1)
        bottom.addWidget(self.status, 1, 2)

        main_layout.addLayout(bottom)

        self.setLayout(main_layout)

        # ───────── TIMER ─────────
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(240000)

        self.update_ui()

    # ─────────────────────────────
    # UPDATE UI
    # ─────────────────────────────
    def update_ui(self):

        fs, fe, rs, re = processlog(LOG_DIR)

        axs = self.canvas.axs

        for ax in axs.flat:
            ax.clear()

        # COLORS
        colors = ['#22D3EE', '#4ADE80', '#FACC15', '#F87171', '#A78BFA', '#FB7185']

        temp_graph(axs[0][0], fs, "Front Start", colors)
        temp_graph(axs[0][1], rs, "Rear Start", colors)
        temp_graph(axs[1][0], fe, "Front End", colors)
        temp_graph(axs[1][1], re, "Rear End", colors)

        self.canvas.draw()

        # ───────── AVG CALCULATION ─────────
        f_vals = []
        r_vals = []

        for i in range(len(fs)):
            if fs[i] and fe[i]:
                avg = (fs[i][-1] + fe[i][-1]) / 2
                f_vals.append(avg)

        for i in range(len(rs)):
            if rs[i] and re[i]:
                avg = (rs[i][-1] + re[i][-1]) / 2
                r_vals.append(avg)

        f_avg = sum(f_vals) / max(1, len(f_vals))
        r_avg = sum(r_vals) / max(1, len(r_vals))

        self.f_avg.setText(f"{round(f_avg,2)} °C")
        self.r_avg.setText(f"{round(r_avg,2)} °C")

        # ───────── STATUS ─────────
        if f_avg > 50 or r_avg > 50:
            self.status.setText("● HIGH TEMP")
            self.status.setStyleSheet("color:#EF4444; font-size:30px; font-weight:bold;")
        else:
            self.status.setText("● RUNNING")
            self.status.setStyleSheet("color:#22C55E; font-size:30px; font-weight:bold;")


# ─────────────────────────────
# MAIN
# ─────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())