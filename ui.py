import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from log_cleaning import processlog   # your file

import os
LOG_DIR = os.path.join(os.getcwd(), "log")


# ─────────────────────────────
# GRAPH FUNCTION
# ─────────────────────────────
def temp_graph(ax, arrays, title, colors, bg_color):

    for i, arr in enumerate(arrays):
        if arr:
            ax.plot(arr, color=colors[i % len(colors)], linewidth=2)

    ax.set_title(title, color='white')
    ax.set_facecolor(bg_color)

    ax.tick_params(colors='white')

    for spine in ax.spines.values():
        spine.set_edgecolor('#334155')
        spine.set_linewidth(1.5)


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

        # LEFT
        self.com = QComboBox()
        self.com.addItems(["COM1", "COM2", "COM3"])
        self.com.setStyleSheet("""
            background-color:#1E293B;
            padding:6px;
            border-radius:6px;
        """)

        left_part = QHBoxLayout()
        left_part.addWidget(QLabel("COM Port:"))
        left_part.addWidget(self.com)

        # RIGHT
        right_part = QVBoxLayout()

        admin = QPushButton("Admin")
        admin.setStyleSheet("""
            background-color:#22C55E;
            padding:8px;
            border-radius:6px;
            color:white;
        """)

        self.update_label = QLabel("Last Update: --")
        self.update_label.setStyleSheet("""
            font-size:12px;
            color:#94A3B8;
        """)

        right_part.addWidget(admin)
        right_part.addWidget(self.update_label)

        top.addLayout(left_part)
        top.addStretch()
        top.addLayout(right_part)

        main_layout.addLayout(top)

        # ───────── GRAPH AREA ─────────
        self.canvas = Canvas()
        main_layout.addWidget(self.canvas)

        # ───────── BOTTOM PANEL ─────────
        bottom = QGridLayout()

        self.f_avg = QLabel("-- °C")
        self.r_avg = QLabel("-- °C")
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
        self.timer.start(240000)  # 4 min

        self.update_ui()

    # ─────────────────────────────
    # UPDATE UI
    # ─────────────────────────────
    def update_ui(self):

        # 🔹 update time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.update_label.setText(f"Last Update: {current_time}")

        fs, fe, rs, re = processlog(LOG_DIR)

        axs = self.canvas.axs

        for ax in axs.flat:
            ax.clear()

        colors = ['#22D3EE', '#4ADE80', '#FACC15', '#F87171', '#A78BFA', '#FB7185']

        # 🔥 PANEL SPLIT COLORS
        temp_graph(axs[0][0], fs, "Front Start", colors, "#1E293B")
        temp_graph(axs[0][1], rs, "Rear Start", colors, "#172554")
        temp_graph(axs[1][0], fe, "Front End", colors, "#1E293B")
        temp_graph(axs[1][1], re, "Rear End", colors, "#172554")

        self.canvas.draw()

        # ───────── AVG ─────────
        f_vals = []
        r_vals = []

        for i in range(len(fs)):
            if fs[i] and fe[i]:
                f_vals.append((fs[i][-1] + fe[i][-1]) / 2)

        for i in range(len(rs)):
            if rs[i] and re[i]:
                r_vals.append((rs[i][-1] + re[i][-1]) / 2)

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
# MAIN (ONLY IF RUN DIRECTLY)
# ─────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())