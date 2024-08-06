import sys
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtWidgets import QWidget,QDialog, QApplication, QVBoxLayout,QLineEdit, QHBoxLayout, QPushButton, QLabel, QCalendarWidget, QMainWindow, QAction, QMenu, QToolButton
from datetime import datetime, timedelta

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
        

        date_layout.addWidget(self.from_date_label)
        date_layout.addWidget(self.from_date_entry)
        date_layout.addWidget(self.to_date_label)
        date_layout.addWidget(self.to_date_entry)
        date_layout.addWidget(self.show_data_button)

        

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
                raise ValueError("From date must be before To date.")

            self.paint_widget.update_date_range(from_date_dt, to_date_dt)

        except ValueError as e:
            print(f"Error: {e}")

class PaintWidget(QWidget):
    def __init__(self, db_file_path):
        super().__init__()
        self.db_file_path = db_file_path
        self.start_date = None
        self.end_date = None
        self.date_time_data = {}
        self.date_labels = []
        self.setMinimumHeight(200)

    def update_date_range(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.date_time_data = self.get_date_time_data()
        self.update()

    def get_date_time_data(self):
        connection = sqlite3.connect(self.db_file_path)
        cursor = connection.cursor()

        query = """
            SELECT strftime('%Y-%m-%d', timestamp) as date, MAX(strftime('%H:%M', timestamp)) as latest_time 
            FROM SensorData
            WHERE date(timestamp) BETWEEN ? AND ?
            GROUP BY date 
            ORDER BY date
        """
        
        params = (self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))

        cursor.execute(query, params)
        rows = cursor.fetchall()

        date_time_data = {row[0]: row[1] for row in rows}

        connection.close()
        return date_time_data

    def drawrect(self, painter):
        if not self.start_date or not self.end_date:
            return

        rect_x = 10
        rect_y = 40
        rect_width = self.width() - 20
        rect_height = self.height() - 60

        delta = (self.end_date - self.start_date).days + 1
        dates = [(self.start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta)]

        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.drawRect(rect_x, rect_y, rect_width, rect_height)

        if len(dates) == 0:
            return

        line_spacing = rect_width / len(dates)

        for label in self.date_labels:
            label.deleteLater()
        self.date_labels.clear()

        
        for i, date in enumerate(dates):
            line_x = int(rect_x + i * line_spacing)
            if date in self.date_time_data:
                latest_time = self.date_time_data[date]
                hours, minutes = map(int, latest_time.split(':'))
                coverage_ratio = (hours * 60 + minutes) / (24 * 60)  # Convert to proportion of the day
                green_height = int(rect_height * coverage_ratio)
                red_height = rect_height - green_height
                # Draw green part for the covered ratio

                painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
                painter.drawRect(line_x, rect_y, int(line_spacing), green_height)

                # Draw red part for the uncovered ratio
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
                painter.drawRect(line_x, rect_y + green_height, int(line_spacing), red_height)
                
                
            else:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
                painter.drawRect(line_x, rect_y, int(line_spacing), rect_height)

            day_month = (self.start_date + timedelta(days=i)).strftime('%d/%m') 
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine)) 
            painter.drawText(line_x + 5, rect_y - 5, day_month)  
                

        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        for i, date in enumerate(dates):
            line_x = int(rect_x + i * line_spacing)
            painter.drawLine(line_x, rect_y, line_x, rect_y + rect_height)
            

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.drawrect(painter)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    widget = MyWidget()
    sys.exit(app.exec_())
