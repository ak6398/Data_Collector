import os
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import serial.tools.list_ports
from .port_form import Form
from configuration.utils import resource_path



class NewWindow(QMainWindow):
    Default_Braud_rate = 19200

    def __init__(self):
        super().__init__()
        ui_file=resource_path("Gui/serial_port_new_prj.ui")
        uic.loadUi(ui_file, self)
        # choose file dialog
        self.choose_file_btn.clicked.connect(self.open_file_dialog)
        # back button
        self.Back_btn.clicked.connect(self.previous_page)
        # next button
        self.Next_btn.clicked.connect(self.get_details)

        self.port_combo_box=self.findChild(QComboBox,'port_select')

        self.populate_com_ports()


        # layout=QVBoxLayout()
        # layout.addWidget(self.combo_box)
        # self.setLayout(layout)

        self.project_name.setPlaceholderText("Enter Project Name")
        
        # port entry
        self.Braud_rate.setText(str(self.Default_Braud_rate))
        self.Braud_rate.setReadOnly(True)

    def populate_com_ports(self):
        com_ports=self.get_com_ports()

        self.port_combo_box.addItems(com_ports)

    def get_com_ports(self):
        # Use pyserial to list available COM ports
        ports = serial.tools.list_ports.comports()
        com_ports = [port.device for port in ports]  # Extract port names
        return com_ports


    def open_file_dialog(self):
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
                port_address=self.port_select.currentText().strip()
                if project_name:
                    os.makedirs(config_folder_path, exist_ok=True)
                    self.db_file_path = os.path.join(config_folder_path, "data_logger.db")
                    print(f"Database file path: {self.db_file_path}")

                    # Create a config file
                    config_file_path = os.path.join(config_folder_path, "config.txt")
                    with open(config_file_path, 'w') as config_file:
                        config_file.write(f'project name:{project_name}\n')
                        config_file.write(f'select port:{port_address}\n')
                    QMessageBox.information(self, "Information", f'New project folder saved to {config_folder_path}')
                    
                else:
                    QMessageBox.warning(self, "Warning", "Please enter a project name.")
        else:
            QMessageBox.warning(self,"Warning","Please select the path to save your project")
    

    def load_existing_project(self, config_folder_path):
        # Load existing project settings from config.txt
        config_file_path = os.path.join(config_folder_path, "config.txt")
        print(f"Config file path: {config_file_path}")
        
        if os.path.isfile(config_file_path):
            with open(config_file_path, 'r') as config_file:
                config_data = config_file.readlines()
                project_name = config_data[0].strip().split(':', 1)[1].strip()
                port_address = config_data[1].strip().split(':', 1)[1].strip()
                print(f"Project name: {project_name}, Port: {port_address}")
                
                # Load the database file path
                self.db_file_path = os.path.join(config_folder_path, "data_logger.db")
                print(f"Database file path: {self.db_file_path}")
                
                # Set the project name and IP address in the UI
                self.project_name.setText(project_name)
                self.port_select.setText(port_address)

                QMessageBox.information(self, "Information", f'Loaded existing project: {project_name}')
        else:
            QMessageBox.warning(self, "Warning", "No configuration file found in the selected folder.")
    
    

    def previous_page(self):
        from .PortWindow import Portwindow
        self.close()
        self.previous_window = Portwindow()
        self.previous_window.show()

    def get_details(self):
        # Get project name and IP address entered by the user
        project_name = self.project_name.text().strip()
        port_address = self.port_select.currentText().strip()
        
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please enter a project name")
        elif not port_address:
            QMessageBox.warning(self, "Warning", "Please enter the IP address")
        elif not hasattr(self,'db_file_path'):
            QMessageBox.warning(self,"Warning","please select the folder for database file")
        else:
            # Pass IP address and port to Form window
            self.data_log_window = Form(port_address, self.Default_Braud_rate, self.db_file_path)
            self.data_log_window.show()
            self.close()