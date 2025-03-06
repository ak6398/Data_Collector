from builtins import int
import sys
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QBrush,QColor
from PyQt5.QtWidgets import QWidget,QDialog,QMessageBox,QFileDialog, QApplication, QVBoxLayout,QLineEdit, QHBoxLayout, QPushButton, QLabel, QCalendarWidget, QMainWindow, QAction, QMenu, QToolButton
from datetime import datetime, timedelta
import pandas as pd
import os

class CalendarDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.calendar=QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.select_date)

        layout=QVBoxLayout()
        layout.addWidget(self.calendar)
        self.setLayout(layout)
        self.setWindowTitle("Select Date")

    def select_date(self,date):
        self.parent().set_selected_date(date)
        self.accept() # Close the dialog


class MyWidget(QMainWindow):
    def __init__(self, db_file_path):
        super().__init__()
        self.db_file_path = db_file_path
        self.config_folder_path=os.path.dirname(db_file_path)
        self.initUI()
        self.show()

    def initUI(self):
        # Layouts
        main_layout = QVBoxLayout()
        date_layout = QHBoxLayout()

        # Calendar widgets for date range selection
        self.from_date_label = QLabel("From Date:")
        self.from_date_entry = QLineEdit()
        self.from_date_entry.setPlaceholderText("YYYY-MM-DD")
        self.from_date_entry.mousePressEvent=self.show_calendar_from

        self.to_date_label = QLabel("To Date (YYYY-MM-DD):")
        self.to_date_entry = QLineEdit()
        self.to_date_entry.setPlaceholderText("YYYY-MM-DD")
        self.to_date_entry.mousePressEvent = self.show_calendar_to

        self.show_data_button = QPushButton("Show Data")
        self.show_data_button.clicked.connect(self.update_data)

        # export to excel button
        self.export_excel_button=QPushButton("Export To Excel")
        self.export_excel_button.clicked.connect(self.export_excel)

        date_layout.addWidget(self.from_date_label)
        date_layout.addWidget(self.from_date_entry)
        date_layout.addWidget(self.to_date_label)
        date_layout.addWidget(self.to_date_entry)
        date_layout.addWidget(self.show_data_button)
        date_layout.addWidget(self.export_excel_button)

        

        # Widget for painting
        self.paint_widget = PaintWidget(self.db_file_path)
        main_layout.addLayout(date_layout)
        main_layout.addWidget(self.paint_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


    def show_calendar_from(self,event):
        self.current_date_entry=self.from_date_entry
        self.calendar_dialog=CalendarDialog(self)
        self.calendar_dialog.exec_()  # Show the calendar dialog

    def show_calendar_to(self,event):
        self.current_date_entry = self.to_date_entry  # Set the active field
        self.calendar_dialog = CalendarDialog(self)
        self.calendar_dialog.exec_()  # Show the calendar dialog

    def set_selected_date(self,date):
        if self.current_date_entry:
            self.current_date_entry.setText(date.toString("yyyy-MM-dd"))

    def export_excel(self):
        from_date=self.from_date_entry.text()
        to_date=self.to_date_entry.text()

        try:
            # Validate the date format
            from_date_obj=datetime.strptime(from_date,"%Y-%m-%d")
            to_date_obj=datetime.strptime(to_date,"%Y-%m-%d")

            data=self.fetch_data(from_date_obj,to_date_obj)

            if data.empty:
                QMessageBox.warning(self, "No Data", "No data available for the selected date range.")
                return
            # # Construct the file path for saving the Excel file
            file_name=f"Data_{from_date}_to_{to_date}.xlsx"
            file_path=os.path.join(self.config_folder_path,file_name)

            # Save the DataFrame to an Excel file
            data.to_excel(file_path, index=False)

            
            QMessageBox.information(self, "Success", f"Data exported successfully to {file_path}")
        except ValueError:
            QMessageBox.critical(self, "Error", "Please enter valid dates in the format YYYY-MM-DD.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while exporting data: {e}") 

    def fetch_data(self, from_date, to_date):
        
        conn_excel=sqlite3.connect(self.db_file_path)
        query=""" SELECT * FROM Sensordata
        WHERE timestamp >= ? AND timestamp < ? """

        # Add one day to the to_date for the strict less-than comparison
        next_day = to_date + timedelta(days=1)
        
        df=pd.read_sql_query(query,conn_excel,params=(from_date,next_day))
        conn_excel.close()
        return df



    def update_data(self):
        from_date = self.from_date_entry.text()
        to_date = self.to_date_entry.text()
        try:
             # Replace slashes with dashes in the input
            from_date = from_date.replace('/', '-')
            to_date = to_date.replace('/', '-')

            from_date_dt = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_dt = datetime.strptime(to_date, '%Y-%m-%d')
            
            if from_date_dt>to_date_dt:
                QMessageBox.warning(self, "Warning", "from date not shorter than current date.")
                return

            self.paint_widget.update_date(from_date_dt,to_date_dt)

        except ValueError as e:
            print(f"Error: {e}")

class PaintWidget(QWidget):
    def __init__(self, db_file_path):
        super().__init__()
        self.db_file_path = db_file_path
        self.start_date = None
        self.end_date = None
        self.setMinimumHeight(300)

    def update_date(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.update()

    def get_hour_data(self, date):
        conn = sqlite3.connect(self.db_file_path)
        cursor = conn.cursor()
        
        # Query to get the count of data points for each hour of the given date
        hour_query = """
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
            FROM SensorData
            WHERE date(timestamp) = ?
            GROUP BY hour 
            ORDER BY hour
        """
        cursor.execute(hour_query, (date.strftime('%Y-%m-%d'),))
        hour_data = cursor.fetchall()
        conn.close()
        
        # Create a dictionary to map hours to data presence
        hour_dict = {hour: count > 0 for hour, count in hour_data}
        return hour_dict

    def drawrect(self, painter):
        if not self.start_date or not self.end_date:
            print("Start date or end date is None.")
            return

        rect_x = 50  # Increase the left margin to accommodate time labels
        rect_y = 40
        rect_width = self.width() - 60  # Adjust the width accordingly
        rect_height = self.height() - 60

        # Calculate the number of days between start_date and end_date
        num_days = (self.end_date - self.start_date).days + 1
        day_width = rect_width / num_days

        # Draw the outer rectangle
        print("Drawing the outer rectangle...")
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.drawRect(rect_x, rect_y, rect_width, rect_height)

        # Draw the date labels above the rectangle
        current_date = self.start_date
        for day in range(num_days):
            # Calculate the position for each day rectangle
            day_rect_x = rect_x + day * day_width
            
            # Draw the date label at the start of each new day
            painter.setPen(QPen(QColor(0, 0, 0), 1, Qt.SolidLine))
            painter.drawText(int(day_rect_x + day_width / 2 - 20), int(rect_y - 10), current_date.strftime('%m-%d'))

            # Draw the time labels above the hour segments
            for hour in range(24):
                # Calculate the height for each hour segment
                hour_height = rect_height / 24
                hour_y = rect_y + hour * hour_height

                # Draw the time label above the hour segment
                time_label = f"{hour:02}:00"
                painter.drawText(rect_x - 40, int(hour_y + hour_height / 2), time_label)

                # Get data for the current date
                hour_data = self.get_hour_data(current_date)

                # Determine color based on data presence
                is_data_present = hour_data.get(str(hour).zfill(2), 0) > 0
                color = QColor(0, 255, 0) if is_data_present else QColor(255, 0, 0)  # Green if data is present, else red

                # Fill the hour segment with the chosen color
                painter.setBrush(QBrush(color))
                painter.drawRect(int(day_rect_x), int(hour_y), int(day_width), int(hour_height))

                # Draw the background rectangle (if needed)
                painter.drawRect(int(day_rect_x), int(hour_y), int(day_width), int(hour_height))

            # Draw the vertical lines separating days
            painter.drawLine(int(day_rect_x + day_width), int(rect_y), int(day_rect_x + day_width), int(rect_y + rect_height))
            
            # Move to the next day
            current_date += timedelta(days=1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.drawrect(painter)
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    widget = MyWidget()
    sys.exit(app.exec_())
