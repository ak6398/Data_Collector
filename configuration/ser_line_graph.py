import sys
import sqlite3
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
import mplcursors
from datetime import datetime,timedelta
import calendar

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self.handle_item_pressed)

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)  
        if item.checkState() == Qt.Unchecked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def checkedItems(self):
        checked_items = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                checked_items.append(self.model().item(i).text())
        return checked_items
      
class DateDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setGeometry(100,100,300,300)
        self.setWindowTitle("Select Date")

        # create a calendar widget
        self.calendar=QCalendarWidget(self)
        # create ok button
        self.ok_button=QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        layout=QVBoxLayout()
        layout.addWidget(self.calendar)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
    
    def getDate(self):
        selected_date=self.calendar.selectedDate().toString("yyyy-MM-dd")
        return selected_date

class MainWindow(QMainWindow):
    def __init__(self, db_file_path,port_address,braud_rate):
        super(MainWindow, self).__init__()
        self.db_file_path = db_file_path
        self.port_address=port_address
        self.braud_rate=braud_rate

        self.initUI()

    def initUI(self):
        # Set up the main window layout
        self.setWindowTitle("Show Graph Window")
        self.setGeometry(100, 100, 800, 600)

        central_widget=QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout=QVBoxLayout(central_widget)

        top_layout=QVBoxLayout()

        main_layout.addLayout(top_layout)

        # create a date widget
        self.from_Date_lbl=QLabel("From date:",self)
        self.from_line_edit=QLineEdit(self)
        self.from_line_edit.setReadOnly(True)
        self.from_line_edit.mousePressEvent=self.show_from_date_dialog

        self.to_date_lbl=QLabel("To data",self)
        self.to_line_edit=QLineEdit(self)
        self.to_line_edit.setReadOnly(True)
        self.to_line_edit.mousePressEvent=self.show_to_date_dialog

        # Add the label and date to the horizontal layout
        top_layout.addWidget(self.from_Date_lbl)
        top_layout.addWidget(self.from_line_edit)
        top_layout.addWidget(self.to_date_lbl)
        top_layout.addWidget(self.to_line_edit)

        # # Create the checkable combo box
        self.graph_combo_box_label=QLabel("Select the Graph Parameters",self)
        self.graph_combo_box = CheckableComboBox(self)
        self.graph_combo_box.activated.connect(self.on_graph_type_selected)
        
        self.populate_columns()

        # # Create the Matplotlib canvas and toolbar
        self.canvas = FigureCanvas(plt.Figure())
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add the label and combo box to the horizontal layout
        top_layout.addWidget(self.graph_combo_box_label)
        top_layout.addWidget(self.graph_combo_box)

        # Create the label and combobox for graph type
        self.graph_label = QLabel("Select Graph Type:", self)
        self.graph_type_combo_box = QComboBox(self)
        self.graph_type_combo_box.addItems(["Line Graph", "Bar Graph","Wind Rose graph"])
        self.graph_type_combo_box.currentIndexChanged.connect(self.handle_graph_type_selection)

        # Add the label and combo box to the horizontal layout
        top_layout.addWidget(self.graph_label)
        top_layout.addWidget(self.graph_type_combo_box)

        # Create a back button to go to the previous page
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back_window)
        # self.back_btn.clicked.connect(self.back_window)
        top_layout.addWidget(self.back_btn)
        top_layout.addWidget(self.toolbar)
        top_layout.addWidget(self.canvas)


        

        # Connect combo box selection changes to the plot update
        self.graph_combo_box.activated.connect(self.update_plot)

    def back_window(self):
        from .port_form import Form
        self.close()
        self.bk_window=Form(self.port_address,self.braud_rate,self.db_file_path)
        self.bk_window.show()

    

    def populate_columns(self):
        try:
            # connect to database
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()

            # Fetch column names from the sensorData table
            cursor.execute("PRAGMA table_info(sensorData)")
            columns_info = cursor.fetchall() 
            columns = [column[1] for column in columns_info if column[1] != "timestamp"]

            # Add columns to the checkable combo box
            self.graph_combo_box.addItems(columns)

            cursor.close()
            conn.close()
        except sqlite3.Error as e:
            print(f"An error occurred while fetching columns: {e}")


    def load_data(self,from_date,to_date,selected_columns):
        try:
            if not from_date:
                # self.show_alert("The 'from_date' cannot be empty")
                QMessageBox.warning(self,"Warning","the from date cannot be empty")
                return pd.DataFrame()  # Return an empty DataFrame if from_date is missing
            if not to_date:
                QMessageBox.warning(self,"Warning","the to date cannot be empty")
                return pd.DataFrame()
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()
             # Ensure that from_date and to_date are strings in the correct format
            if isinstance(from_date, list) or isinstance(to_date, list):
                raise ValueError("from_date and to_date must be strings or datetime objects, not lists.")

            # Debugging: Print the from_date and to_date
            print(f"From Date: {from_date}")
            print(f"To Date: {to_date}")

            # Convert from_date and to_date to datetime objects if they are not already
            if isinstance(from_date, str):
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
            if isinstance(to_date, str):
                to_date = datetime.strptime(to_date, '%Y-%m-%d')

            to_date=to_date+timedelta(days=1)
            # Convert back to string for SQL query
            from_date = from_date.strftime('%Y-%m-%d')
            to_date = to_date.strftime('%Y-%m-%d')

            # Debugging: Print the from_date and to_date
            print(f"Adjusted From Date: {from_date}")
            print(f"Adjusted To Date: {to_date}")

            # Check if selected_columns is not empty
            if selected_columns:
                query=f"SELECT timestamp, {', '.join([f'\"{col}\"' for col in selected_columns])} FROM sensorData WHERE timestamp>= ? AND timestamp< ?"
                # Debugging: Print the SQL query
                print(f"SQL Query: {query}")
                cursor.execute(query, (from_date, to_date))
            else:
                return pd.DataFrame(cursor.fetchall(), columns=['timestamp'] + selected_columns)
            
            # fetch all result into a dataframe
            data=cursor.fetchall()
            # Debugging: Print the fetched data
            print(f"Fetched Data: {data}")
            df=pd.DataFrame(data,columns=['timestamp']+selected_columns)
            cursor.close()
            conn.close()
            return df
        except sqlite3.Error as e:
            print(f"An error occurred while loading data: {e}")
            return pd.DataFrame()
    


        
    def on_graph_type_selected(self):
       
        # Get selected columns
        selected_columns = self.graph_combo_box.checkedItems()

        if not selected_columns:
           QMessageBox.warning(self, "Warning", "Please select at least one column.")
           return
        # Fetch data from the database based on selected date range
        from_date=self.from_line_edit.text()
        to_date=self.to_line_edit.text()

        # Check if both dates are selected
        if from_date and to_date:

            # Fetch data from the database
            data = self.load_data(from_date,to_date,selected_columns)
            if data.empty:
                self.canvas.figure.clear()
                self.canvas.draw()
                QMessageBox.warning(self, "Warning", "No data found for the selected date range.")
                return
        else:
            QMessageBox.warning(self, "Warning", "Please select both from and to dates.")

    def handle_graph_type_selection(self, graph_type=None):
            graph_type = self.graph_type_combo_box.currentText()
            if graph_type == "Wind Rose graph":
                self.plot_windrose_graph()
            else:
                # Optionally handle other graph types or clear the canvas
                self.update_plot()
    def update_plot(self):
        selected_columns = self.graph_combo_box.checkedItems()
        graph_type = self.graph_type_combo_box.currentText()

        # Check if any columns are selected
        if not selected_columns:
            # Clear the canvas if no columns are selected
            self.canvas.figure.clear()
            self.canvas.draw()
            return

        
        from_date = self.from_line_edit.text()
        to_date = self.to_line_edit.text()
        df = self.load_data(from_date, to_date, selected_columns)
        if graph_type=="Bar Graph":
            self.plot_bar_graph(df)
        elif graph_type=="Line Graph":
            self.plot_line_graph(df)
        


    def plot_windrose_graph(self):
        from configuration.serial_windrose import MainWindow
        self.close()
        # Open a new dialog window for the wind rose graph
        self.windrose_dialog = MainWindow(self.db_file_path,self.port_address,self.braud_rate)
        self.windrose_dialog.show()




            
            

    def plot_line_graph(self, df):
        
        
        if df.empty or 'timestamp' not in df.columns:
            print("No data available to plot or timestamp column missing.")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)
        df.set_index('timestamp', inplace=True)

        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors='coerce')

        df.dropna(axis=1, how='all', inplace=True)
        num_columns = len(df.columns)

        if num_columns == 0:
            print("No numeric data columns to plot.")
            return

        self.canvas.figure.clear()
        num_cols = 2
        num_rows = (num_columns + num_cols - 1) // num_cols

        for i, column in enumerate(df.columns):
            ax = self.canvas.figure.add_subplot(num_rows, num_cols, i + 1)
            line,=ax.plot(df.index, df[column], label=column)
            ax.set_title(f"Line Graph of {column}")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel(column)
            ax.legend()

            # ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            # Add hover functionality
            cursor = mplcursors.cursor(line, hover=True)
            cursor.connect("add", lambda sel, df=df, column=column: sel.annotation.set_text(
                f"{df.index[int(sel.index)].strftime('%m-%d %H:%M:%S')}\n{column}: {df[column].iloc[int(sel.index)]:.2f}" # type: ignore
                if 0 <= int(sel.index) < len(df.index) else 'Index out of range' # type: ignore
            ))
            cursor.connect("remove", lambda sel: sel.annotation.set_text(''))

            


        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def plot_bar_graph(self, df):
        if df.empty:
            print("No data available to plot.")
            return

        if 'timestamp' not in df.columns:
            print("Timestamp column missing.")
            return

        # Convert the timestamp column to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.set_index('timestamp', inplace=True)

        # Convert all columns except 'timestamp' to numeric, forcing errors to NaN
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors='coerce')

        num_columns = len(df.columns)
        if num_columns == 0:
            print("No numeric data columns to plot.")
            return

        self.canvas.figure.clear()  # Clear the existing figure on the canvas

        num_cols = 2
        num_rows = (num_columns + num_cols - 1) // num_cols

        # Create a subplot for each type of data
        for i, column in enumerate(df.columns):
            ax = self.canvas.figure.add_subplot(num_rows, num_cols, i + 1)
            
            # Create a bar graph
            ax.bar(df.index, df[column], label=column)
            ax.set_title(f"Bar Graph of {column}")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel(column)
            ax.legend()

            # Format the x-axis date labels to MM-DD
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

            # Rotate date labels for better readability
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        self.canvas.draw()  # Refresh the canvas to display the new plot


    def show_from_date_dialog(self,event):
        date_dialog=DateDialog()
        if date_dialog.exec_()==QDialog.Accepted:
            from_date=date_dialog.getDate()
            self.from_line_edit.setText(from_date)

    def show_to_date_dialog(self,event):
        date_dialog=DateDialog()
        if date_dialog.exec_()==QDialog.Accepted:
            to_date=date_dialog.getDate()
            self.to_line_edit.setText(to_date)



if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())

