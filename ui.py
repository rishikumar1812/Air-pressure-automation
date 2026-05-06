import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout,
    QDialog, QLineEdit, QMessageBox,
    QSlider, QFileDialog
)

from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

import config
from log_cleaning import process_data


# =========================================================
# GRAPH FUNCTION
# =========================================================

def temp_graph(ax, arrays, title):

    colors = plt.cm.tab10.colors

    if not arrays or (len(arrays) == 1 and not arrays[0]):

        ax.text(
            0.5,
            0.5,
            "No Data Available",
            ha='center',
            va='center',
            fontsize=14,
            color="white"
        )

        ax.set_title(title, color="white")
        ax.set_xticks([])
        ax.set_yticks([])

        return

    all_x = [np.arange(len(arr)) for arr in arrays if len(arr) > 0]

    min_x = min([x.min() for x in all_x] if all_x else [0])
    max_x = max([x.max() for x in all_x] if all_x else [0])

    aligned_arrays = []

    for arr in arrays:

        if len(arr) > 0:

            x = np.arange(len(arr))

            y = np.full(max_x - min_x + 1, np.nan)

            y[x - min_x] = arr

            aligned_arrays.append(y)

        else:

            aligned_arrays.append(
                np.full(max_x - min_x + 1, np.nan)
            )

    for i, arr in enumerate(aligned_arrays):

        if np.isfinite(arr).any():

            x = np.arange(min_x, max_x + 1)

            ax.plot(
                x,
                arr,
                linewidth=2,
                color=colors[i % len(colors)],
                label=f"DL{i+1}"
            )

    ax.set_title(title, color="white", fontsize=13)

    ax.set_xlabel("Time Index", color="white")
    ax.set_ylabel("Temperature °C", color="white")

    ax.tick_params(colors='white')

    ax.grid(True, alpha=0.3)

    ax.legend()

    ax.set_facecolor("#111827")


# =========================================================
# MATPLOTLIB CANVAS
# =========================================================

class Canvas(FigureCanvas):

    def __init__(self):

        self.fig = Figure(figsize=(12, 7))
        self.fig.patch.set_facecolor("#0F172A")

        self.axs = self.fig.subplots(2, 2)

        super().__init__(self.fig)

        self.fig.subplots_adjust(
            hspace=0.35,
            wspace=0.25,
            top=0.92,
            bottom=0.08
        )


# =========================================================
# LOGIN WINDOW
# =========================================================

class LoginWindow(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Admin Authentication")

        self.setFixedSize(380, 280)

        self.setStyleSheet("""

            QWidget{
                background-color:#0F172A;
                color:white;
                font-family:Arial;
            }

            QLineEdit{
                background:#1E293B;
                border:2px solid #334155;
                border-radius:10px;
                padding:12px;
                font-size:14px;
                color:white;
            }

            QPushButton{
                background:#2563EB;
                border:none;
                border-radius:10px;
                padding:12px;
                font-size:15px;
                font-weight:bold;
                color:white;
            }

            QPushButton:hover{
                background:#1D4ED8;
            }

        """)

        layout = QVBoxLayout()

        title = QLabel("ADMIN LOGIN")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            color:#38BDF8;
        """)

        self.user = QLineEdit()
        self.user.setPlaceholderText("User ID")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("LOGIN")

        login_btn.clicked.connect(self.check_login)

        layout.addStretch()

        layout.addWidget(title)

        layout.addSpacing(20)

        layout.addWidget(self.user)
        layout.addWidget(self.password)

        layout.addSpacing(15)

        layout.addWidget(login_btn)

        layout.addStretch()

        self.setLayout(layout)

    def check_login(self):

        user_id = self.user.text()
        password = self.password.text()

        # CHANGE THIS
        if user_id == "admin" and password == "1234":

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Access Denied",
                "Wrong User ID or Password"
            )

            self.reject()


# =========================================================
# ADMIN PANEL
# =========================================================

class AdminPanel(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Admin Control Panel")

        self.setGeometry(300, 150, 550, 400)

        self.setStyleSheet("""

            QWidget{
                background-color:#0F172A;
                color:white;
                font-family:Arial;
            }

            QLabel{
                font-size:15px;
            }

            QPushButton{
                background:#2563EB;
                border:none;
                border-radius:10px;
                padding:12px;
                font-size:14px;
                font-weight:bold;
                color:white;
            }

            QPushButton:hover{
                background:#1D4ED8;
            }

            QSlider::groove:horizontal{
                height:8px;
                background:#334155;
                border-radius:4px;
            }

            QSlider::handle:horizontal{
                background:#38BDF8;
                width:18px;
                margin:-5px 0;
                border-radius:9px;
            }

        """)

        layout = QVBoxLayout()

        title = QLabel("ADMIN SETTINGS")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:24px;
            color:#38BDF8;
            font-weight:bold;
        """)

        layout.addWidget(title)

        layout.addSpacing(30)

        # =================================================
        # LOG DIRECTORY
        # =================================================

        self.log_label = QLabel(
            f"Current Log Directory:\n\n{config.log_dir}"
        )

        self.log_label.setStyleSheet("""
            background:#111827;
            padding:15px;
            border-radius:10px;
            color:#E2E8F0;
        """)

        change_btn = QPushButton("Change Log Directory")

        change_btn.clicked.connect(self.change_dir)

        layout.addWidget(self.log_label)

        layout.addSpacing(10)

        layout.addWidget(change_btn)

        layout.addSpacing(40)

        # =================================================
        # VOLTAGE
        # =================================================

        self.voltage_label = QLabel("Voltage: 220V")

        self.voltage_label.setStyleSheet("""
            font-size:18px;
            color:#38BDF8;
            font-weight:bold;
        """)

        self.slider = QSlider(Qt.Horizontal)

        self.slider.setMinimum(150)
        self.slider.setMaximum(300)

        self.slider.setValue(220)

        self.slider.valueChanged.connect(self.update_voltage)

        layout.addWidget(self.voltage_label)

        layout.addWidget(self.slider)

        layout.addStretch()

        self.setLayout(layout)

    def change_dir(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Log Folder"
        )

        if folder:

            # Update runtime value
            config.log_dir = folder

            # SAVE PERMANENTLY
            with open("config.py", "w") as f:

                f.write(f'log_dir = r"{folder}"\n')

            self.log_label.setText(
                f"Current Log Directory:\n\n{folder}"
            )

            QMessageBox.information(
                self,
                "Saved",
                "Log Directory Saved Permanently"
            )

    def update_voltage(self):

        value = self.slider.value()

        self.voltage_label.setText(
            f"Voltage: {value}V"
        )


# =========================================================
# MAIN DASHBOARD
# =========================================================

class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Machine Temperature Monitor")

        self.setGeometry(100, 50, 1400, 900)

        self.setStyleSheet("""

            QWidget{
                background-color:#0F172A;
                color:#E2E8F0;
                font-family:Arial;
            }

            QPushButton{
                background:#2563EB;
                border:none;
                border-radius:10px;
                padding:10px 18px;
                font-size:14px;
                font-weight:bold;
                color:white;
            }

            QPushButton:hover{
                background:#1D4ED8;
            }

            QComboBox{
                background:#1E293B;
                border:1px solid #334155;
                padding:8px;
                border-radius:8px;
                color:white;
            }

        """)

        main_layout = QVBoxLayout()

        # =================================================
        # TOP BAR
        # =================================================

        top_layout = QHBoxLayout()

        left_layout = QHBoxLayout()

        com_label = QLabel("COM:")

        com_label.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
        """)

        self.com = QComboBox()

        self.com.addItems([
            "COM1",
            "COM2",
            "COM3"
        ])

        left_layout.addWidget(com_label)
        left_layout.addWidget(self.com)

        top_layout.addLayout(left_layout)

        top_layout.addStretch()

        # RIGHT PANEL

        right_layout = QVBoxLayout()

        self.admin_btn = QPushButton("Admin")

        self.admin_btn.clicked.connect(self.open_admin)

        self.ut = QLabel("Update Time: --")
        self.dt = QLabel("Data Time: --")

        self.ut.setStyleSheet("""
            color:#94A3B8;
            font-size:13px;
        """)

        self.dt.setStyleSheet("""
            color:#94A3B8;
            font-size:13px;
        """)

        right_layout.addWidget(self.admin_btn)
        right_layout.addWidget(self.ut)
        right_layout.addWidget(self.dt)

        top_layout.addLayout(right_layout)

        main_layout.addLayout(top_layout)

        # =================================================
        # GRAPH SECTION
        # =================================================

        self.canvas = Canvas()

        main_layout.addWidget(self.canvas)

        # =================================================
        # BOTTOM SECTION
        # =================================================

        bottom = QGridLayout()

        self.fs_avg = QLabel("Front Start Avg: --")
        self.fe_avg = QLabel("Front End Avg: --")
        self.rs_avg = QLabel("Rear Start Avg: --")
        self.re_avg = QLabel("Rear End Avg: --")

        labels = [
            self.fs_avg,
            self.fe_avg,
            self.rs_avg,
            self.re_avg
        ]

        for lbl in labels:

            lbl.setStyleSheet("""
                font-size:24px;
                color:#38BDF8;
                font-weight:bold;
            """)

        self.status = QLabel("● RUNNING")

        self.status.setStyleSheet("""
            color:#22C55E;
            font-size:28px;
            font-weight:bold;
        """)

        bottom.addWidget(self.fs_avg, 0, 0)
        bottom.addWidget(self.rs_avg, 0, 1)

        bottom.addWidget(self.fe_avg, 1, 0)
        bottom.addWidget(self.re_avg, 1, 1)

        bottom.addWidget(self.status, 2, 1)

        main_layout.addLayout(bottom)

        self.setLayout(main_layout)

        # =================================================
        # TIMER
        # =================================================

        self.timer = QTimer()

        self.timer.timeout.connect(self.update_ui)

        self.timer.start(30000)

        self.update_ui()

    # =====================================================
    # OPEN ADMIN PANEL
    # =====================================================

    def open_admin(self):

        login = LoginWindow(self)

        if login.exec_() == QDialog.Accepted:

            self.admin_panel = AdminPanel()

            self.admin_panel.show()

    # =====================================================
    # UPDATE UI
    # =====================================================

    def update_ui(self):

        try:

            result = process_data(config.log_dir)

            fs, fe, rs, re, fs_avg, fe_avg, rs_avg, re_avg, ut, dt = result

            axs = self.canvas.axs

            for ax in axs.flat:

                ax.clear()

            temp_graph(axs[0][0], fs, "Front DL Start")
            temp_graph(axs[0][1], rs, "Rear Start")

            temp_graph(axs[1][0], fe, "Front End")
            temp_graph(axs[1][1], re, "Rear End")

            self.canvas.draw()

            self.fs_avg.setText(
                f"Front Start Avg: {round(fs_avg,2)}°C"
            )

            self.fe_avg.setText(
                f"Front End Avg: {round(fe_avg,2)}°C"
            )

            self.rs_avg.setText(
                f"Rear Start Avg: {round(rs_avg,2)}°C"
            )

            self.re_avg.setText(
                f"Rear End Avg: {round(re_avg,2)}°C"
            )

            self.ut.setText(f"Update Time: {ut}")
            self.dt.setText(f"Data Time: {dt}")

            # FIXED STATUS ISSUE
            self.status.setText("● RUNNING")

            self.status.setStyleSheet("""
                color:#22C55E;
                font-size:28px;
                font-weight:bold;
            """)

        except Exception as e:

            print("ERROR:", e)

            self.status.setText("● ERROR")

            self.status.setStyleSheet("""
                color:red;
                font-size:28px;
                font-weight:bold;
            """)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = Dashboard()

    window.show()

    sys.exit(app.exec_())
