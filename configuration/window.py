from PyQt5.QtWidgets import *
from PyQt5 import uic
from .new_window import NewWindow
import os



class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Gui/select_gui.ui", self)
        self.next_btn.clicked.connect(self.on_next_btn_click)

    def on_next_btn_click(self):
        from .new_window import NewWindow
        if self.new_prj_btn.isChecked():
            self.newwindow = NewWindow()
            self.newwindow.show()
            self.close()
        elif self.exsting_prj_btn.isChecked():
            self.open_existing_project_dialog()
        else:
            QMessageBox.warning(self, "Warning", "Please select a project type")

    def open_existing_project_dialog(self):
        # Open a file dialog to select the config.txt file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Config File", "", "Text Files (*.txt);;All Files (*)", options=options)
        print(f"Selected file path: {file_path}")
        if file_path:
            # Check if the selected file is a config.txt file
            if os.path.basename(file_path) == "config.txt":
                try:
                    # Read the contents of the config.txt file
                    with open(file_path, 'r') as file:
                        config_data = file.readlines()
                        project_name = config_data[0].strip().split(':', 1)[1].strip()
                        ip_address = config_data[1].strip().split(':', 1)[1].strip()
                        print(f"Project name: {project_name}, IP address: {ip_address}")

                        # Create a NewWindow instance and set the values
                        self.newwindow = NewWindow()
                        self.newwindow.project_name.setText(project_name)
                        self.newwindow.ip_address.setText(ip_address)

                        # Set db_file_path (assuming you want to keep this in NewWindow)
                        project_folder = os.path.dirname(os.path.dirname(file_path))  # Get the folder where config.txt is located
                        self.newwindow.db_file_path = os.path.join(project_folder,project_name,"data_logger.db")
                        print(f"Database file path in NewWindow: {self.newwindow.db_file_path}")

                        self.newwindow.show()
                        self.close()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to read config file: {e}")
            else:
                QMessageBox.warning(self, "Invalid File", "Please select a config.txt file.")