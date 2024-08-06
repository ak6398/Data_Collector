import socket
from PyQt5.QtCore import *

class DataFetchThread(QThread):
    data_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal()

    def __init__(self, ip_address, port):
        super().__init__()
        self.ip_address = ip_address
        self.port = port
        self.stop_thread = False

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip_address, self.port))
                self.connection_successful.emit()

                # First, fetch parameters using the '?' command
                s.sendall(b'?')
                params_data = s.recv(1024).decode('utf-8')
                self.data_fetched.emit(f'?{params_data}')

                # Then, continuously fetch values using the '!' command
                while not self.stop_thread:
                    s.sendall(b'!')
                    values_data = s.recv(1024).decode('utf-8')
                    if values_data:
                        self.data_fetched.emit(values_data)
                    QThread.sleep(1)  
        except socket.gaierror:
            self.error_occurred.emit("Invalid IP address or host not found.")
            self.connection_failed.emit()
        except socket.timeout:
            self.error_occurred.emit("Connection timed out.")
            self.connection_failed.emit()
        except socket.error as e:
            self.error_occurred.emit(f"Socket error: {e}")
            self.connection_failed.emit()