import serial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import time
from .logging_utility import logger

class DataFetchThread(QThread):
    data_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal()
    show_error_message=pyqtSignal(str)

    def __init__(self, port_address, braud_rate,db_file_path,sleep_duration=5,timeout=0.5):
        super().__init__()
        self.port_address = port_address
        self.braud_rate = braud_rate
        self.db_file_path=db_file_path
        self.sleep_duration=sleep_duration
        self.timeout=timeout
        # self.sleep_interval=0
        self.max_tries=1 # Maximum number of reconnection attempts
        self.stop_thread = False

    def run(self):
        retry_count=0
        while not self.stop_thread and retry_count<=self.max_tries:
            try:
                # Establishing the serial connection
                with serial.Serial(self.port_address, self.braud_rate, timeout=self.timeout) as ser:
                    try:
                        self.connection_successful.emit()
                        logger.info("connection successful")
                        retry_count=0

                        next_fetch_time=time.time()
                        
                        # First, fetch parameters using the '?' command
                        try:
                            ser.write(b'?')
                            params_data = ser.readline().decode('utf-8').strip()  # Reading the response
                            if params_data:
                                logger.info(f"fetched data {params_data}")
                                self.data_fetched.emit(f'?{params_data}')
                            else:
                                logger.error("no data recieved for ? command")
                                raise serial.error("No data received for '?' command")
                            
                        except (serial.error, Exception) as e:
                        
                            raise serial.error(f"Error fetching parameters: {str(e)}")
                            
                        try:
                            # Then, continuously fetch values using the '!' command
                            while not self.stop_thread:
                                current_time=time.time()
                                if current_time>=next_fetch_time:
                                    ser.write(b'!')
                                    values_data = ser.readline().decode('utf-8').strip()  # Reading the response
                                    if values_data:
                                        self.data_fetched.emit(values_data)
                                        print(f"fetched at {time.strftime('%H:%M:%S', time.localtime())}: {values_data}")
                                        # calculate the next_fetch_time
                                        next_fetch_time+=self.sleep_duration
                                    else:
                                        logger.error("error in fetching data")
                                    time.sleep(0.5)
                                    
                                    # QThread.sleep(self.sleep_duration)
                        except (serial.error,Exception) as e:
                            logger.error("error in fetching values")
                            raise serial.error(f"Error fetching values: {str(e)}")
                        

                    except serial.SerialException as e:
                        error_message=f"Serial error:{e}"
                        self.error_occurred.emit(error_message)
                        self.connection_failed.emit()
                        print(f"SerialException occurred: {e}")
                        self.show_error_message.emit(error_message)
                        # Show an error message box  
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Critical)
                        msg_box.setWindowTitle("Connection Error")
                        msg_box.setText(f"Serial error occurred: {e}")
                        msg_box.exec_()

            except Exception as e:
                self.error_occurred.emit(f"Error: {e}")
                self.connection_failed.emit()
                # Show an error message box
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"An error occurred: {e}")
                msg_box.exec_()

            finally:
                if retry_count<=self.max_tries and not self.stop_thread:
                    logger.error("Attempting to reconnect")
                    self.error_occurred.emit("Attempting to reconnect")
                    time.sleep(5) 
        if retry_count>self.max_tries:
            logger.error("Maximum reconnection attempts reached.")
            self.error_occurred.emit("Maximum reconnection attempts reached.")

    def update_interval(self,sleep_duration):
        self.sleep_duration=sleep_duration

    def stop(self):
        self.stop_thread=True 
        self.wait()


        
