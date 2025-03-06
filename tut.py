from PyQt5.QtWidgets import QMainWindow, QMenu, QComboBox, QWidgetAction, QDialog, QVBoxLayout, QLabel, QPushButton, QApplication

class TimeIntervalDialog(QDialog):
    def __init__(self, parent=None):
        super(TimeIntervalDialog, self).__init__(parent)
        
        self.setWindowTitle("Set Data Fetch Interval")

        layout = QVBoxLayout()

        # Labels
        layout.addWidget(QLabel("Select Hours:"))
        self.hours_combo = QComboBox()
        self.hours_combo.addItems([str(i) for i in range(0, 25)])
        layout.addWidget(self.hours_combo)

        layout.addWidget(QLabel("Select Minutes:"))
        self.minutes_combo = QComboBox()
        self.minutes_combo.addItems([str(i) for i in range(0, 60)])
        layout.addWidget(self.minutes_combo)

        layout.addWidget(QLabel("Select Seconds:"))
        self.seconds_combo = QComboBox()
        self.seconds_combo.addItems([str(i) for i in range(0, 60)])
        layout.addWidget(self.seconds_combo)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def get_time_interval(self):
        # Calculate total time interval in seconds
        hours = int(self.hours_combo.currentText())
        minutes = int(self.minutes_combo.currentText())
        seconds = int(self.seconds_combo.currentText())
        return hours * 3600 + minutes * 60 + seconds


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        menu_bar = self.menuBar()
        setting_menu = QMenu("Set Data Fetched Time", self)
        menu_bar.addMenu(setting_menu)

        # Action to open the custom dialog
        open_dialog_action = QWidgetAction(self)
        open_dialog_action.setText("Select Interval")
        open_dialog_action.triggered.connect(self.open_time_interval_dialog)
        setting_menu.addAction(open_dialog_action)

    def open_time_interval_dialog(self):
        dialog = TimeIntervalDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            interval = dialog.get_time_interval()
            self.update_fetch_interval(interval)

    def update_fetch_interval(self, interval):
        # Your code to update the fetch interval, e.g., update a timer or a data fetcher
        print(f"Data fetch interval set to {interval} seconds")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
