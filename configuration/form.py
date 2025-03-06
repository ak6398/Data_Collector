import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QDialog,QVBoxLayout,QComboBox,QLabel,QPushButton,QMainWindow,QAction,QMenu,QWidgetAction,QTableWidgetItem,QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QFont,QColor
from PyQt5.QtCore import Qt,QMetaObject,Q_ARG,pyqtSlot
from configuration.utils import resource_path
from .line_graph import MainWindow
from .data_thread_ethernet import DataFetchThread
from .logging_utility import logger
"""Handle the class TimeIntervalDialog of the window."""
class TimeIntervalDialog(QDialog):

    def __init__(self,parent=None):
        """define function ."""
        super(TimeIntervalDialog,self).__init__(parent)
        logger.info("Initializing TimeIntervalDialog")
        self.setWindowTitle("set Data fetch interval")
        self.setGeometry(600,300,300,200)

        layout=QVBoxLayout()

        # hour labels
        layout.addWidget(QLabel("Select hours:"))
        self.hour_combo=QComboBox()
        self.hour_combo.addItems([str(i) for i in range(0,25)])
        layout.addWidget(self.hour_combo)

        # Minute label
        layout.addWidget(QLabel("Select Minutes:"))
        self.minutes_combo=QComboBox()
        self.minutes_combo.addItems([str(i) for i in range(0,60)])
        layout.addWidget(self.minutes_combo)

        # second label
        layout.addWidget(QLabel("Select Seconds:"))
        self.seconds_combo=QComboBox()
        self.seconds_combo.addItems([str(i) for i in range(1,60)])
        layout.addWidget(self.seconds_combo)

        # ok button
        ok_button=QPushButton("Ok")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        self.setLayout(layout)

    def get_time_interval(self):
        # # calculate total time interval in seconds
        hours = int(self.hour_combo.currentText())
        minutes = int(self.minutes_combo.currentText())
        seconds = int(self.seconds_combo.currentText())
        interval= hours * 3600 + minutes * 60 + seconds
        logger.info(f"Time interval set to {interval} seconds")
        return interval

        
"""Handle the form class  of the window."""
class Form(QMainWindow):
    def __init__(self, ip_address, port, db_file_path):
        super().__init__()
        logger.info(f"Form initialized with IP: {ip_address}, Port: {port}")
        self.test_progress = None
        self.line_graph = None
        self.parameters_fetched = False
        self.stop_thread = None
        ui_file=resource_path("Gui/main.ui")
        uic.loadUi(ui_file, self)
        self.ip_address = ip_address
        self.port = port
        self.db_file_path = db_file_path
        self.data_fetch_thread=None
        self.sleep_duration=5
        self.start_data_fetch_thread(self.sleep_duration)
        self.font_size=15 # default font size

        

        # Initialize fields for sensor names, values, and units
        self.sensor_names = []
        self.sensor_values = []
        self.sensor_units = []


        # Load existing data from the database
        self.update_saved_data_table()
        

        ip_menubar = self.menuBar()
        # export menu for filemenu
        export_menu_bar=self.menuBar()
        export_menu=export_menu_bar.findChild(QMenu,'menuFile')

        export_action=QAction('export to excel',self)
        export_action.triggered.connect(self.export_manage)
        export_menu.addAction(export_action)

        # Find the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.findChild(QMenu, 'menuFile')     

        # # create a menu
        setting_menu=QMenu("Set Data Fetched Time",self)
        menu_bar.addMenu(setting_menu)

        # action to open custom dialog
        open_dialog_action=QWidgetAction(self)
        open_dialog_action.setText("Select Interval")
        open_dialog_action.triggered.connect(self.open_time_interval_dialog)
        setting_menu.addAction(open_dialog_action)

        # setting_menu.addAction(combo_action)
        # # Connect QComboBox selection change to the timeout update method
        # combo_box.currentTextChanged.connect(self.update_fetch_interval)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("ctrl+Q")
        file_menu.addAction(exit_action)

        exit_action.triggered.connect(self.exit_window)
        # show graph menu
        menu_bar=self.menuBar()
        graph_menu=QMenu("Graphs",self)
        menu_bar.addMenu(graph_menu)

        show_graph_action=graph_menu.addAction("Show Graph")
        show_graph_action.triggered.connect(self.show_graph)


        # add a menu for font-size selection
        font_menu=ip_menubar.addMenu("Font-Size")
        for size in range(10,31,2):
            font_action=QAction(f'{size} pt',self)
            font_action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
            font_menu.addAction(font_action)

    def start_data_fetch_thread(self,sleep_duration):
        logger.info(f"Starting data fetch thread with sleep duration: {sleep_duration}")
        if self.data_fetch_thread is not None:
            logger.info("Stopping existing data fetch thread")
            self.data_fetch_thread.stop_thread=True
            self.data_fetch_thread.wait()

    #     # Start the data fetching thread
        
        self.data_fetch_thread = DataFetchThread(self.ip_address, self.port,sleep_duration=sleep_duration)
        self.data_fetch_thread.data_fetched.connect(self.handle_data_fetched)
        self.data_fetch_thread.error_occurred.connect(self.show_error_message)
        self.data_fetch_thread.connection_successful.connect(self.update_window_title_connected)
        self.data_fetch_thread.connection_failed.connect(self.update_window_title_disconnected)
        self.data_fetch_thread.start()
        logger.info("Data fetch thread started")


    def open_time_interval_dialog(self):
        logger.info("Opening time interval dialog")
        dialog=TimeIntervalDialog(self)
        if dialog.exec_()==QDialog.Accepted:
            interval=dialog.get_time_interval()
            self.update_fetch_interval(interval)

    def update_fetch_interval(self,interval):
        logger.info(f"Updating fetch interval to {interval} seconds")
        if self.data_fetch_thread:
            self.data_fetch_thread.update_interval(interval)

    def set_font_size(self,size):
        logger.info(f"Setting font size to {size}")
        self.font_size=size
        self.update_saved_data_table() # Update table to apply the new font size

            # export detial page

    def export_manage(self):
        logger.info("Exporting data to excel")
        from configuration.display_data import MyWidget
        # from configuration.with_time_display import MyWidget
        self.test_progress=MyWidget(self.db_file_path,self.ip_address,self.port)
        self.test_progress.show()
        self.data_fetch_thread.stop_thread = True
        self.close()


    def show_graph(self):
        logger.info("Showing graph")
        self.line_graph=MainWindow(self.db_file_path,self.ip_address,self.port)
        self.line_graph.show()
        self.close()

    def update_saved_data_table(self):
        try:
            conn=sqlite3.connect(self.db_file_path)
            cursor=conn.cursor()
        
            # fetch all data from the sensor data table
            cursor.execute("PRAGMA table_info(SensorData)")
            columns_info = cursor.fetchall()
            column_names = [info[1] for info in columns_info]
            # Fetch data ordered by timestamp in descending order
            cursor.execute("SELECT * FROM SensorData ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            if not rows:
                print("No data found in the database.")
                logger.warning("No data found in the database.")

            font_size = 10  # You can change this to your preferred size
            font = QFont()
            font.setPointSize(font_size)
            # clear the table before displaying new data
            self.Data_table.setRowCount(0)
            self.Data_table.setColumnCount(len(column_names))
            self.Data_table.setHorizontalHeaderLabels(column_names)
            # Populate the table with data
            for row in rows:
                row_position = self.Data_table.rowCount()
                self.Data_table.insertRow(row_position)
                for col, data in enumerate(row):
                    item = QTableWidgetItem(str(data))
                    item.setFont(font)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setForeground(QColor('white'))
                    self.Data_table.setItem(row_position, col, item)
            print("Data loaded successfully.")
            logger.info("Data loaded successfully into table.")
        except sqlite3.Error as e:
            print(f"An error occurred while fetching data: {e}")
        finally:
            conn.close()
        
    # # Set initial window title
    #     self.setWindowTitle(f"Disconnected from {self.ip_address}:{self.port}")

    def handle_data_fetched(self, data):
        try:

            # Initialize a flag to check if parameters have already been fetched
            if not hasattr(self,'parameters_fetched'):
                self.parameters_fetched=False
            # Log the raw data received
            # print(f"Raw data received: {data}")
            

            if data.startswith('?') and not self.parameters_fetched:
                # Fetch and log raw parameters from the data logger
                params_data = data[1:]
                logger.debug(f"Raw data received: {data}")
                logger.info(f"Parsing parameters: {params_data}")
                # print(f"Raw parameters from data logger: {params_data}")
                self.parse_parameters(params_data)
                self.create_table(self.sensor_names)
                self.update_value_fields(params_data)
                print("Parameters:", self.sensor_names)

                # Set the flag to True so parameters are not fetched again
                self.parameters_fetched=True
            else:
                # Fetch and log the raw sensor values
                values_data = data
                logger.debug(f"Parsing sensor values: {values_data}")
                # print(f"Raw sensor values: {values_data}")
                # Parse the sensor values
                self.parse_values(values_data)

                # Log the parsed sensor values before saving
                print(f"Parsed sensor values: {self.sensor_values}")

                # Save the parsed data to the database
                self.save_to_database()
                self.update_value_fields(values_data)

                ## Print the final sensor values to the console
                print("Final sensor values:", self.sensor_values)
        except Exception as e:
            # Log the exception details
            # print(f"An error occurred while handling fetched data: {str(e)}")
            logger.error(f"An error occurred while handling fetched data: {str(e)}")

    def create_table(self, param_names):
        logger.info("Creating database table")
        conn = sqlite3.connect(self.db_file_path)
        cursor = conn.cursor()
        try:
            columns = ', '.join([f'"{name.replace(" ", "_")}" REAL' for name in param_names])
            query = f'''
                CREATE TABLE IF NOT EXISTS SensorData (
                    timestamp TEXT,
                    {columns}
                )
            '''
            cursor.execute(query)
            conn.commit()
            logger.info("Database table created successfully")
        except sqlite3.Error as e:
            # print(f"An error occurred: {e}")
            logger.error(f"An error occurred while creating table: {e}")
        finally:
            conn.close()

    def save_to_database(self):
        logger.info("Saving data to database")
        conn = sqlite3.connect(self.db_file_path)
        cursor = conn.cursor()
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            placeholders = ', '.join(['?'] * (len(self.sensor_names) + 1))  # +1 for timestamp
            columns = ', '.join([f'"{name.replace(" ", "_")}"' for name in self.sensor_names])
            query = f'''
                INSERT INTO SensorData (
                    timestamp,
                    {columns}
                )
                VALUES ({placeholders})
            '''
            for i,value in enumerate(self.sensor_values):
                sensor_name = self.sensor_names[i].lower()
                if sensor_name=='Temprature' and (value<0.5 or value>50):
                    logger.error(f"Invalid temperature value: {value}. Expected range: 0.5 to 50.")
                    return False
                elif sensor_name=='Temprature' and 0<value<1:
                    logger.warning(f"Temperature value is too low: {value}. Check for sensor issues.")
                    self.sensor_values[i] = None
            cursor.execute(query, (timestamp, *self.sensor_values))
            conn.commit()
            # Update the saved data table after saving to the database
            self.update_saved_data_table()
        except sqlite3.Error as e:
            # print(f"An error occurred while saving data: {e}")
            logger.error(f"An error occurred while saving data: {e}")
        finally:
            conn.close()

    def show_error_message(self, message):
        logger.error(f"Error occurred: {message}")
        QMetaObject.invokeMethod(self, "_show_error_message", Qt.QueuedConnection, Q_ARG(str, message))

    @pyqtSlot(str)
    def _show_error_message(self, message):
        
        QMessageBox.critical(self, "Error", message)

    def update_window_title_connected(self):
        logger.info(f"Connected to {self.ip_address}:{self.port}")
        self.setWindowTitle(f"Connected to {self.ip_address}:{self.port}")

    def update_window_title_disconnected(self):
        logger.info(f"Disconnected from {self.ip_address}:{self.port}")
        self.setWindowTitle(f"Disconnected from {self.ip_address}:{self.port}")

    def parse_parameters(self, params_data):
        logger.info(f"Parsing parameters: {params_data}")
        params = params_data.split(',')
        trans_table = str.maketrans('', '', '();')
        self.sensor_units = [param.split('(')[-1].translate(trans_table) for param in params]
        self.sensor_names = [param.split('(')[0].strip() for param in params]
        logger.info(f"Parsed sensor names: {self.sensor_names}")

    def parse_values(self, values_data):
        logger.info(f"Parsing values: {values_data}")
        values = values_data.split(',')
        try:
            self.sensor_values = [float(value.strip().rstrip(';')) for value in values if value.strip().rstrip(';').replace('.', '', 1).isdigit()]
            logger.info(f"Parsed sensor values: {self.sensor_values}")
        except ValueError as e:
            # print(f"ValueError while parsing values: {e}")
            logger.error(f"ValueError while parsing values: {e}")

    def resize_event(self,event):
        logger.debug("Resize event triggered")
        self.adjust_coloumn_widths()
        super().resizeEvent(event)

    def adjust_coloumn_widths(self):
        logger.debug("Adjusting column widths")
        if self.tableWidget.columnCount()>0:
            self.tableWidget.resizeColumnsToContents() # Adjust columns to fit content
            self.tableWidget.resizeRowsToContents() # Adjust rows to fit content

            table_width=self.tableWidget.viewport().width()
            total_content_width=sum(self.tableWidget.columnWidth(i) for i in range(self.tableWidget.columnCount()))
            
            if total_content_width<table_width:

                column_width = table_width // self.tableWidget.columnCount()
                for i in range(self.tableWidget.columnCount()):
                    self.tableWidget.setColumnWidth(i,column_width)
            else:
                pass

    def update_sensor_fields(self):
        pass

    def update_value_fields(self, values_data):
        logger.debug(f"Updating value fields with data: {values_data}")
        self.display_data(values_data, ','.join([f"{name}({unit})" for name, unit in zip(self.sensor_names, self.sensor_units)]))

    def display_data(self, data, params):
        logger.info("Displaying data in table")
        try:

            param_list = params.split(',')
            trans_table = str.maketrans('', '', '();')
            units = [param.split('(')[-1].translate(trans_table) for param in param_list]
            param_names = [param.split('(')[0].strip() for param in param_list]

            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderLabels(["Sensor Name", "Value", "Units"])

            # column_width = 200  # Adjust width as needed
            # for i in range(3):
            #     self.tableWidget.setColumnWidth(i, column_width)

            values = data.split(',')
            for i, value in enumerate(values):
                row_position = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row_position)

                # set the desired font size
                font=QFont()
                font.setPointSize(self.font_size)
                
                param_name_item = QTableWidgetItem(param_names[i])
                param_name_item.setForeground(QColor('white'))
                param_name_item.setTextAlignment(Qt.AlignCenter)
                param_name_item.setFont(font)
                self.tableWidget.setItem(row_position, 0, param_name_item)


                cleaned_value = value.strip().rstrip(';')
                value_item = QTableWidgetItem(cleaned_value)
                value_item.setFont(font)
                value_item.setForeground(QColor('white'))
                value_item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row_position, 1, value_item)

                unit_item = QTableWidgetItem(units[i])
                unit_item.setFont(font)
                unit_item.setTextAlignment(Qt.AlignCenter)
                unit_item.setForeground(QColor('white'))
                self.tableWidget.setItem(row_position, 2, unit_item)

            self.adjust_coloumn_widths()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


    def closeEvent(self, event):
        logger.info("Close event triggered")
        # Stop the data fetch thread
        if self.data_fetch_thread is not None:
            logger.info("Stopping data fetch thread")
            self.data_fetch_thread.stop_thread=True
            self.data_fetch_thread.wait()
            logger.info("Data fetch thread stopped")
        # Close any open database connections
        try:
            logger.info("Closing database connection")
            sqlite3.connect(self.db_file_path).close()
            logger.info("Database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")
            # pass
        logger.info("Accepting close event")
        event.accept()
        logger.info("Application closed")

    def exit_window(self):
        logger.info("Exit window method called")
        self.close()
        