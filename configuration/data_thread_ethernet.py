import socket
import time
from PyQt5.QtCore import QThread,pyqtSignal
from .logging_utility import logger


class DataFetchThread(QThread):
    data_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal()

    def __init__(self, ip_address, port, sleep_duration=5, timeout=5):
        super().__init__()
        self.ip_address = ip_address
        self.port = port
        self.sleep_duration = sleep_duration
        self.timeout = timeout
        self.stop_thread = False
        self.max_tries=1    # Maximum number of reconnection attempts

    def run(self):
        retry_count=0
        while not self.stop_thread and retry_count<=self.max_tries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.settimeout(self.timeout)
                        s.connect((self.ip_address, self.port))
                        self.connection_successful.emit()
                        logger.info(f"connected to {self.ip_address}:{self.port}")

                        # Reset retry count after successful connection
                        retry_count=0

                        # First, fetch parameters using the '?' command
                        try:
                            s.sendall(b'?')
                            params_data = s.recv(1024).decode('utf-8')
                            if params_data:
                                self.data_fetched.emit(f'?{params_data}')
                            else:
                                raise socket.error("No data received for '?' command")
                        except (socket.error, Exception) as e:
                            raise socket.error(f"Error fetching parameters: {str(e)}")

                        # Then, continuously fetch values using the '!' command
                        try:
                            while not self.stop_thread:
                                s.sendall(b'!')
                                values_data = s.recv(1024).decode('utf-8')
                                if values_data:
                                    self.data_fetched.emit(values_data)
                                QThread.sleep(self.sleep_duration)
                        except (socket.error, Exception) as e:
                            raise socket.error(f"Error fetching values: {str(e)}")

                    except (socket.gaierror, socket.timeout, socket.error) as e:
                        error_message = f"Connection error: {str(e)}"
                        self.error_occurred.emit(error_message)
                        self.connection_failed.emit()
                        retry_count+=1 # Increment retry count
                        raise

            except Exception as e:
                # Catch any other unexpected exceptions
                self.error_occurred.emit(f"Unexpected error: {str(e)}")
                self.connection_failed.emit()

            finally:
                if retry_count<=self.max_tries and not self.stop_thread:
                    # Reattempt connection in case of failure
                    self.error_occurred.emit("Reconnecting...")
                    time.sleep(5)  # Sleep before reattempting connection
        if retry_count>self.max_tries:
            self.error_occurred.emit("Maximum reconnection attempts reached.")

    def update_interval(self,sleep_duration):
        self.sleep_duration=sleep_duration

    def stop(self):
        self.stop_thread = True
        self.wait()
