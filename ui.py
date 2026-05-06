import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout,
    QDialog, QLineEdit, QMessageBox,
    QFileDialog, QSlider
)

from PyQt5.QtCore import (
    Qt,
    QTimer,
    QFileSystemWatcher
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from log_cleaning import processlog


# ─────────────────────────────
# DEFAULT LOG DIRECTORY
# ─────────────────────────────
LOG_DIR = r"C:\DGS\Logs"

# ─────────────────────────────
# GRAPH SETTINGS
# ─────────────────────────────
WINDOW = 50


# ─────────────────────────────
# GRAPH FUNCTION
# ─────────────────────────────
def temp_graph(ax, arrays, title, colors, bg_color):

    for i, arr in enumerate(arrays):

        if arr:
            data = arr[-WINDOW:]

            ax.plot(
                data,
                color=colors[i % len(colors)],
                linewidth=2
            )

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
# LOGIN DIALOG
# ─────────────────────────────
class LoginDialog(QDialog):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Admin Authentication")
        self.setFixedSize(350, 220)

        self.setStyleSheet("""
            QWidget{
                background-color:#0F172A;
                color:white;
                font-size:14px;
            }

            QLineEdit{
                background:#1E293B;
                border:1px solid #334155;
                padding:8px;
                border-radius:6px;
                color:white;
            }

            QPushButton{
                background:#22C55E;
                padding:10px;
                border-radius:6px;
                color:white;
                font-weight:bold;
            }
        """)

        layout = QVBoxLayout()

        title = QLabel("Admin Login")
        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#38BDF8;
        """)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("User ID")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.check_login)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addSpacing(10)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    # ─────────────────────────────
    # CHECK LOGIN
    # ─────────────────────────────
    def check_login(self):

        username = self.user_input.text()
        password = self.pass_input.text()

        # CHANGE USERNAME/PASSWORD HERE
        if username == "admin" and password == "1234":

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Access Denied",
                "Invalid Username or Password"
            )

            self.reject()


# ─────────────────────────────
# ADMIN PANEL
# ─────────────────────────────
class AdminPanel(QDialog):

    def __init__(self, dashboard):

        super().__init__()

        self.dashboard = dashboard

        self.setWindowTitle("Admin Settings")
        self.setFixedSize(550, 350)

        self.setStyleSheet("""
            QWidget{
                background-color:#0F172A;
                color:white;
                font-size:14px;
            }

            QPushButton{
                background:#2563EB;
                padding:10px;
                border-radius:6px;
                color:white;
                font-weight:bold;
            }

            QLabel{
                color:white;
            }
        """)

        layout = QVBoxLayout()

        # ───────── LOG DIRECTORY ─────────
        title = QLabel("Admin Control Panel")

        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#38BDF8;
        """)

        layout.addWidget(title)

        layout.addSpacing(20)

        current = QLabel("Current Log Directory:")

        self.path_label = QLabel(self.dashboard.log_dir)

        self.path_label.setStyleSheet("""
            background:#1E293B;
            padding:10px;
            border-radius:6px;
            color:#4ADE80;
        """)

        browse_btn = QPushButton("Change Log Directory")
        browse_btn.clicked.connect(self.change_directory)

        layout.addWidget(current)
        layout.addWidget(self.path_label)
        layout.addSpacing(10)
        layout.addWidget(browse_btn)

        # ───────── VOLTAGE SLIDER ─────────
        layout.addSpacing(30)

        voltage_title = QLabel("Voltage Slider (Future Use)")

        voltage_title.setStyleSheet("""
            font-size:16px;
            font-weight:bold;
        """)

        layout.addWidget(voltage_title)

        self.slider = QSlider(Qt.Horizontal)

        self.slider.setMinimum(0)
        self.slider.setMaximum(500)

        self.slider.setValue(self.dashboard.voltage)

        self.slider.valueChanged.connect(self.update_voltage)

        self.voltage_label = QLabel(
            f"Voltage : {self.slider.value()} V"
        )

        self.voltage_label.setStyleSheet("""
            font-size:18px;
            color:#FACC15;
            font-weight:bold;
        """)

        layout.addWidget(self.slider)
        layout.addWidget(self.voltage_label)

        self.setLayout(layout)

    # ─────────────────────────────
    # CHANGE DIRECTORY
    # ─────────────────────────────
    def change_directory(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Log Directory"
        )

        if folder:

            self.dashboard.log_dir = folder

            self.path_label.setText(folder)

            self.dashboard.reset_watcher()

            QMessageBox.information(
                self,
                "Success",
                "Log Directory Updated Successfully"
            )

    # ─────────────────────────────
    # UPDATE VOLTAGE
    # ─────────────────────────────
    def update_voltage(self, value):

        self.dashboard.voltage = value

        self.voltage_label.setText(
            f"Voltage : {value} V"
        )


# ─────────────────────────────
# DASHBOARD
# ─────────────────────────────
class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        self.log_dir = LOG_DIR
        self.voltage = 220

        self.setWindowTitle("Temperature Monitor Dashboard")

        self.setGeometry(100, 100, 1350, 850)

        self.setStyleSheet("""
            QWidget{
                background-color:#0F172A;
                color:#E2E8F0;
                font-family:Arial;
            }
        """)

        main_layout = QVBoxLayout()

        # ─────────────────────────────
        # TOP BAR
        # ─────────────────────────────
        top = QHBoxLayout()

        self.com = QComboBox()

        self.com.addItems([
            "COM1",
            "COM2",
            "COM3"
        ])

        self.com.setStyleSheet("""
            background:#1E293B;
            padding:6px;
            border-radius:6px;
        """)

        left_part = QHBoxLayout()

        left_part.addWidget(QLabel("COM Port :"))
        left_part.addWidget(self.com)

        right_part = QVBoxLayout()

        # ───────── ADMIN BUTTON ─────────
        admin = QPushButton("Admin")

        admin.setStyleSheet("""
            background:#22C55E;
            padding:10px;
            border-radius:6px;
            color:white;
            font-weight:bold;
        """)

        admin.clicked.connect(self.open_admin)

        self.update_label = QLabel("Last Update : --")
        self.date_label = QLabel("Date : --")

        self.update_label.setStyleSheet("""
            font-size:12px;
            color:#94A3B8;
        """)

        self.date_label.setStyleSheet("""
            font-size:12px;
            color:#94A3B8;
        """)

        right_part.addWidget(admin)
        right_part.addWidget(self.update_label)
        right_part.addWidget(self.date_label)

        top.addLayout(left_part)

        top.addStretch()

        top.addLayout(right_part)

        main_layout.addLayout(top)

        # ─────────────────────────────
        # GRAPH SECTION
        # ─────────────────────────────
        self.canvas = Canvas()

        main_layout.addWidget(self.canvas)

        # ─────────────────────────────
        # BOTTOM PANEL
        # ─────────────────────────────
        bottom = QGridLayout()

        self.fs_avg = QLabel("-- °C")
        self.fe_avg = QLabel("-- °C")
        self.rs_avg = QLabel("-- °C")
        self.re_avg = QLabel("-- °C")

        self.status = QLabel("● RUNNING")

        for lbl in [
            self.fs_avg,
            self.fe_avg,
            self.rs_avg,
            self.re_avg
        ]:

            lbl.setStyleSheet("""
                font-size:24px;
                font-weight:bold;
                color:#38BDF8;
            """)

        self.status.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
            color:#22C55E;
        """)

        bottom.addWidget(QLabel("FRONT START DL AVG"), 0, 0)
        bottom.addWidget(QLabel("FRONT END DL AVG"), 0, 1)
        bottom.addWidget(QLabel("REAR START DL AVG"), 0, 2)
        bottom.addWidget(QLabel("REAR END DL AVG"), 0, 3)
        bottom.addWidget(QLabel("STATUS"), 0, 4)

        bottom.addWidget(self.fs_avg, 1, 0)
        bottom.addWidget(self.fe_avg, 1, 1)
        bottom.addWidget(self.rs_avg, 1, 2)
        bottom.addWidget(self.re_avg, 1, 3)
        bottom.addWidget(self.status, 1, 4)

        main_layout.addLayout(bottom)

        self.setLayout(main_layout)

        # ─────────────────────────────
        # BLINK TIMER
        # ─────────────────────────────
        self.blink = False

        self.blink_timer = QTimer()

        self.blink_timer.timeout.connect(
            self.blink_status
        )

        # ─────────────────────────────
        # FILE WATCHER
        # ─────────────────────────────
        self.watcher = QFileSystemWatcher()

        self.reset_watcher()

        self.watcher.directoryChanged.connect(
            self.update_ui
        )

        self.watcher.fileChanged.connect(
            self.update_ui
        )

        self.update_ui()

    # ─────────────────────────────
    # RESET WATCHER
    # ─────────────────────────────
    def reset_watcher(self):

        try:

            self.watcher.removePaths(
                self.watcher.files()
            )

            self.watcher.removePaths(
                self.watcher.directories()
            )

        except:
            pass

        if os.path.exists(self.log_dir):

            self.watcher.addPath(self.log_dir)

            files = [
                os.path.join(self.log_dir, f)
                for f in os.listdir(self.log_dir)
            ]

            if files:
                self.watcher.addPaths(files)

    # ─────────────────────────────
    # ADMIN ACCESS
    # ─────────────────────────────
    def open_admin(self):

        login = LoginDialog()

        result = login.exec_()

        if result == QDialog.Accepted:

            admin_panel = AdminPanel(self)

            admin_panel.exec_()

    # ─────────────────────────────
    # BLINKING STATUS
    # ─────────────────────────────
    def blink_status(self):

        if self.blink:

            self.status.setStyleSheet("""
                color:#EF4444;
                font-size:30px;
                font-weight:bold;
            """)

        else:

            self.status.setStyleSheet("""
                color:white;
                font-size:30px;
                font-weight:bold;
            """)

        self.blink = not self.blink

    # ─────────────────────────────
    # UPDATE UI
    # ─────────────────────────────
    def update_ui(self):

        now = datetime.now()

        self.update_label.setText(
            f"Last Update : {now.strftime('%H:%M:%S')}"
        )

        self.date_label.setText(
            f"Date : {now.strftime('%d-%m-%Y')}"
        )

        try:

            fs, fe, rs, re = processlog(
                self.log_dir
            )

        except Exception as e:

            print("LOG ERROR :", e)

            return

        axs = self.canvas.axs

        for ax in axs.flat:
            ax.clear()

        colors = [
            '#22D3EE',
            '#4ADE80',
            '#FACC15',
            '#F87171'
        ]

        temp_graph(
            axs[0][0],
            fs,
            "Front Start",
            colors,
            "#1E293B"
        )

        temp_graph(
            axs[0][1],
            rs,
            "Rear Start",
            colors,
            "#172554"
        )

        temp_graph(
            axs[1][0],
            fe,
            "Front End",
            colors,
            "#1E293B"
        )

        temp_graph(
            axs[1][1],
            re,
            "Rear End",
            colors,
            "#172554"
        )

        self.canvas.draw()

        # ─────────────────────────────
        # AVERAGES
        # ─────────────────────────────
        fs_avg = sum(
            [arr[-1] for arr in fs if arr]
        ) / max(1, len(fs))

        fe_avg = sum(
            [arr[-1] for arr in fe if arr]
        ) / max(1, len(fe))

        rs_avg = sum(
            [arr[-1] for arr in rs if arr]
        ) / max(1, len(rs))

        re_avg = sum(
            [arr[-1] for arr in re if arr]
        ) / max(1, len(re))

        self.fs_avg.setText(
            f"{round(fs_avg, 2)} °C"
        )

        self.fe_avg.setText(
            f"{round(fe_avg, 2)} °C"
        )

        self.rs_avg.setText(
            f"{round(rs_avg, 2)} °C"
        )

        self.re_avg.setText(
            f"{round(re_avg, 2)} °C"
        )

        # ─────────────────────────────
        # STATUS
        # ─────────────────────────────
        if max(
            fs_avg,
            fe_avg,
            rs_avg,
            re_avg
        ) > 50:

            self.status.setText("● HIGH TEMP")

            if not self.blink_timer.isActive():

                self.blink_timer.start(500)

        else:

            self.status.setText("● RUNNING")

            self.status.setStyleSheet("""
                color:#22C55E;
                font-size:30px;
                font-weight:bold;
            """)

            self.blink_timer.stop()


# ─────────────────────────────
# MAIN
# ─────────────────────────────
if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = Dashboard()

    window.show()

    sys.exit(app.exec_())