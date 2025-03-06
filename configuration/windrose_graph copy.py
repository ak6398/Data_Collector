from builtins import int
import sys
import sqlite3
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from datetime import datetime,timedelta
from windrose import WindroseAxes
import numpy as np



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
    def __init__(self, db_file_path,ip_address,port):
        super(MainWindow, self).__init__()
        self.db_file_path = db_file_path
        self.ip_address=ip_address
        self.port=port

        self.initUI()
    def initUI(self):
        # Set up the main window layout
        self.setWindowTitle("WindRose Graph")
        self.setGeometry(100, 100, 800, 600)

        # create a calendar widget
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

        # selectable range value of legend
        self.select_range_label=QLabel("Select Range",self)
        self.select_range=QComboBox(self)
        self.select_range.addItems(['0-5','0-10','0-20','custom'])
        self.select_range.currentIndexChanged.connect(self.on_graph_type_selected)
        
        

        # # Create the checkable combo box
        self.graph_combo_box_label=QLabel("Select the Graph Parameters",self)
        self.graph_combo_box = CheckableComboBox(self)
        self.graph_combo_box.activated.connect(self.on_graph_type_selected)
        self.populate_columns()


        # Add the label and combo box to the horizontal layout
        top_layout.addWidget(self.graph_combo_box_label)
        top_layout.addWidget(self.graph_combo_box)

        top_layout.addWidget(self.select_range_label)
        top_layout.addWidget(self.select_range)

         # # Create the Matplotlib canvas and toolbar
        # self.figure=plt.figure()
        self.canvas = FigureCanvas(plt.Figure())
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Add the label and combo box to the horizontal layout
        top_layout.addWidget(self.graph_combo_box_label)
        top_layout.addWidget(self.graph_combo_box)

        # Create a back button to go to the previous page
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back_window)


        top_layout.addWidget(self.back_btn)
        top_layout.addWidget(self.toolbar)
        top_layout.addWidget(self.canvas)


    def back_window(self):
        from .line_graph import MainWindow
        self.close()
        self.back=MainWindow(self.db_file_path,self.ip_address,self.port)
        self.back.show()


    def populate_columns(self):
        try:
            conn=sqlite3.connect(self.db_file_path)
            cursor=conn.cursor()

            # fetch column names from the sensordata table
            cursor.execute("PRAGMA table_info(SensorData)")
            columns_info = cursor.fetchall()

            # Filter for only 'wind_speed' and 'wind_direction' columns
            # target_columns = ["Wind_Speed", "Wind_Direction"]
            columns = [column[1] for column in columns_info if column[1] != "timestamp"]
            # Add these specific columns to the checkable combo box
            self.graph_combo_box.addItems(columns)

            cursor.close()
            conn.close()
        except sqlite3.Error as e:
            print(f"An error occurred while fetching columns: {e}")


    def on_graph_type_selected(self):
        selected_columns = self.graph_combo_box.checkedItems()

        if not selected_columns:
            self.canvas.figure.clear()
            self.canvas.draw()
            QMessageBox.warning(self, "Warning", "Please select at least one column.")
            return

        # Ensure Wind_Speed and Wind_Direction are selected for the wind rose plot
        if 'Wind_Speed' in selected_columns or 'Wind_Direction' in selected_columns:
            if 'Wind_Speed' not in selected_columns:
                selected_columns.append('Wind_Speed')
            if 'Wind_Direction' not in selected_columns:
                selected_columns.append('Wind_Direction')

        # Fetch data from the database based on selected date range
        from_date = self.from_line_edit.text()
        to_date = self.to_line_edit.text()

        # Check if both dates are selected
        if from_date and to_date:
            data = self.load_data(from_date, to_date, selected_columns)

            print("Data loaded:", data.head())
            if 'Wind_Speed' not in data.columns or 'Wind_Direction' not in data.columns:
                QMessageBox.warning(self, "Warning", "The data for Wind Speed or Wind Direction is missing.")
                return
            else:
                self.plot_windrose_graph(data)
        else:
            QMessageBox.warning(self, "Warning", "Please select both from and to dates.")


        
    def load_data(self,from_date,to_date,selected_columns):
        try:
            conn=sqlite3.connect(self.db_file_path)
            cursor=conn.cursor()

            if 'Wind_Speed' in selected_columns and len(selected_columns) == 1:
                selected_columns=['Wind_Speed']
            elif 'Wind_Direction' not in selected_columns:
                selected_columns.append('Wind_Direction')

            if selected_columns:
                query=f"SELECT timestamp, {', '.join([f'\"{col}\"' for col in selected_columns])} FROM SensorData WHERE timestamp >= ? AND timestamp < ?"
                # Debugging: Print the SQL query
                print(f"SQL Query: {query}")
                cursor.execute(query, (from_date, to_date))
            else:
                return pd.DataFrame(cursor.fetchall(), columns=['timestamp'] + selected_columns)
            # Fetch all results into a DataFrame
            data=cursor.fetchall()
            # print("fetched data :")
            # for row in data:
            #     print(row)

            df=pd.DataFrame(data,columns=['timestamp']+selected_columns)
            cursor.close()
            conn.close()
            return df
        except sqlite3.Error as e:
            print(f"An error occurred while loading data: {e}")
            return pd.DataFrame()
        

    
    
    # ploting windrose diagram
    def plot_windrose_graph(self,data):
        print("columns in dataframe:",data.columns)
        if 'Wind_Speed' not in data.columns or 'Wind_Direction' not in data.columns:
            QMessageBox.warning(self,"warning","Wind Speed or Wind Direction data is missing.")
            return
        
        data['Wind_Speed']=pd.to_numeric(data['Wind_Speed'], errors='coerce')
        data['Wind_Direction']=pd.to_numeric(data['Wind_Direction'], errors='coerce')

        data = data.dropna(subset=['Wind_Speed', 'Wind_Direction'])

        if data.empty:
            QMessageBox.warning(self, "Warning", "No valid data to plot after cleaning.")
            return

        a = data.head(12)
        # print(a)
        self.canvas.figure.clear()
        # Create a WindroseAxes object
        # ax = WindroseAxes(self.canvas.figure.add_subplot(111,projection='polar'))
        ax = WindroseAxes(self.canvas.figure,[0.1,0.1,0.8,0.8])
        self.canvas.figure.add_axes(ax)

        # get the sleceted legent_range from combo box
        selected_Range=self.select_range.currentText()

        if selected_Range=='0-5':
            bins=np.arange(0,6,1)
        elif selected_Range == "0-10":
            bins = np.arange(0, 11, 2)
        elif selected_Range == "0-20":
            bins = np.arange(0, 21, 4)
        elif selected_Range=='Custom':
            bins=np.linspace(0,data['Wind_Speed'].max(),5)
        else:
            bins=np.linspace(0,data['Wind_Speed'].max(),5)

        # Ensure bins don't contain NaN values
        bins = bins[~np.isnan(bins)]

        if(len(bins))==0:
            QMessageBox.warning(self,"warning","No valid bins available for plotting.")
            return

        ax.bar(data['Wind_Direction'], data['Wind_Speed'],bins=bins, normed=True, opening=0.8, edgecolor='white')

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}%'))
        
        
        
        ax.set_legend(title="Wind Speed (m/s)",loc='lower right', bbox_to_anchor=(1.60, 0),fontsize=14)
        ax.set_title('Wind Rose Diagram')

        self.canvas.draw()
        
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
    mainWin = MainWindow('data_logger.db')
    mainWin.show()
    sys.exit(app.exec_())