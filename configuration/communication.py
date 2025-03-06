from PyQt5.QtWidgets import QMainWindow,QMessageBox
from PyQt5 import uic
from configuration.utils import resource_path
from .window import Window
from .PortWindow import Portwindow

class CommWindow(QMainWindow):
    """Main window for communication settings."""

    def __init__(self):
        """Initialize the CommWindow."""
        super().__init__()
        ui_file=resource_path("Gui/communication_method.ui")
        uic.loadUi(ui_file,self)
        self.comm_btn.clicked.connect(self.on_next_button_clicked)

        self.project_window=None
        self.portwindow=None

    def on_next_button_clicked(self):
        """Handle the next button click event."""
        if self.ethernet_btn.isChecked():
            self.project_window=Window()
            self.project_window.setWindowTitle("Connected through Ethernet")
            self.project_window.show()
            self.close()
        elif self.serial_port_btn.isChecked():
            self.portwindow=Portwindow()
            self.portwindow.setWindowTitle("Connected through serial port")
            self.portwindow.show()
            self.close()
        else:
            QMessageBox.warning(self,"Warning","Please Select a Communication method")
