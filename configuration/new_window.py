import os
from PyQt5.QtWidgets import QMainWindow,QFileDialog,QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
from configuration.utils import resource_path
from .form import Form


"""
This module contains the `NewWindow` class which handles the creation of a new project window.
"""

class NewWindow(QMainWindow):
    Default_port = 10001

    def __init__(self):
        """
        A class used to represent the New Project Window.
        """
        super().__init__()
        self.previous_window=None
        self.data_log_window=None
        ui_file=resource_path("Gui/new_prj.ui")
        uic.loadUi(ui_file, self)
        # choose file dialog
        self.choose_file_btn.clicked.connect(self.open_file_dialog)
        # back button
        self.Back_btn.clicked.connect(self.previous_page)
        # next button
        self.Next_btn.clicked.connect(self.get_details)
        # ip address edit box
        self.ip_address.setPlaceholderText("Enter IP Address")

        ip_regex = QRegExp(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$"
            )
        ip_validator = QRegExpValidator(ip_regex, self.ip_address)
        self.ip_address.setValidator(ip_validator)
        # project name edit box
        self.project_name.setPlaceholderText("Enter Project Name")
        
        # port entry
        self.portNo.setText(str(self.Default_port))
        self.portNo.setReadOnly(True)

    def open_file_dialog(self):
        """Open a file dialog for selecting the project folder."""
        self.db_file_path=""
        while not self.db_file_path:

            directory = QFileDialog.getExistingDirectory(self, "Select Project Folder", "")
            if directory:
                # Check if the folder contains a config folder
                project_name = self.project_name.text().strip()
                config_folder_path = os.path.join(directory, "config", project_name)
                if os.path.exists(config_folder_path):
                    # If it exists, load the existing project
                    print("Loading existing project...")
                    self.load_existing_project(config_folder_path)
                else:
                    ip_address=self.ip_address.text().strip()
                    if project_name:
                        os.makedirs(config_folder_path, exist_ok=True)
                        self.db_file_path = os.path.join(config_folder_path, "data_logger.db")
                        print(f"Database file path: {self.db_file_path}")

                        # Create a config file
                        config_file_path = os.path.join(config_folder_path, "config.txt")
                        with open(config_file_path, 'w',encoding='utf-8') as config_file:
                            config_file.write(f'project name:{project_name}\n')
                            config_file.write(f'Ip Address:{ip_address}\n')
                        QMessageBox.information(self, "Information", f'New project folder saved to {config_folder_path}')    
                    else:
                        QMessageBox.warning(self, "Warning", "Please enter a project name.")
            else:
                QMessageBox.warning(self,"Warning","Please select the path to save your project")
                continue  # Keep prompting until a valid path is selected
    def load_existing_project(self, config_folder_path):
        """Load an existing project configuration from the selected folder."""
        config_file_path = os.path.join(config_folder_path, "config.txt")
        print(f"Config file path: {config_file_path}")
        
        if os.path.isfile(config_file_path):
            with open(config_file_path, 'r') as config_file:
                config_data = config_file.readlines()
                project_name = config_data[0].strip().split(':', 1)[1].strip()
                ip_address = config_data[1].strip().split(':', 1)[1].strip()
                print(f"Project name: {project_name}, IP address: {ip_address}")
                # Load the database file path
                self.db_file_path = os.path.join(config_folder_path, "data_logger.db")
                print(f"Database file path: {self.db_file_path}")
                # Set the project name and IP address in the UI
                self.project_name.setText(project_name)
                self.ip_address.setText(ip_address)
                QMessageBox.information(self, "Information", f'Loaded existing project: {project_name}')
        else:
            QMessageBox.warning(self, "Warning", "No configuration file found in the selected folder.")
    def previous_page(self):
        """Go back to the previous window."""
        from .window import Window # Local import to avoid circular dependency
        self.close()
        self.previous_window = Window()
        self.previous_window.show()
    def get_details(self):
        """Get the project details and proceed to the form window."""
        project_name = self.project_name.text().strip()
        ip_address = self.ip_address.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please enter a project name")
        elif not ip_address:
            QMessageBox.warning(self, "Warning", "Please enter the IP address")
        elif not hasattr(self,'db_file_path'):
            QMessageBox.warning(self,"Warning","please select the folder for database file")
        else:
            # Pass IP address and port to Form window
            self.data_log_window = Form(ip_address, self.Default_port, self.db_file_path)
            self.data_log_window.show()
            self.close()
