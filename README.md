The DataCollector class is responsible for interfacing with a data logger to collect and retrieve data. It facilitates seamless communication between the data logger and a graphical user interface (GUI), allowing users to visualize and analyze data in real time.
Key Features:

**1> **Data Acquisition:****
Establishes a connection with the data logger to fetch data periodically.
Supports communication protocols (e.g., Serial, TCP/IP) based on the data logger specifications.

**2> GUI Integration:**
Updates the GUI in real-time as new data is collected to provide instant feedback and monitoring.

**3> Error Handling:**
Implements robust error handling to manage issues such as disconnection from the data logger or data retrieval errors.
Provides feedback to the user via the GUI in case of errors or warnings.

**4> Data Export:**
Offers functionality to export collected data to various formats (e.g., CSV, Excel) for further analysis or reporting.
