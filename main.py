import sys
from PyQt5.QtWidgets import QApplication,QErrorMessage
# from licensing.models import *
# from licensing.methods import *
from configuration.lice import LicenceWindow
from configuration.communication import CommWindow

def check_license_with_api():
    """Check license validity with an API."""
    # RSAPubKey = "<RSAKeyValue><Modulus>0rJNm16LrlZRF+9G5BYPleIoxOCZk2pkTYeC3Dnn/fI1fjYBIhqx6sPYG4tE9ByLZoz5V6cakctPQEKq4iDbKYBfZB57Rtca22Z3m2a8gKVqppln6pJWa3R55+lKO6ZH5KwfE5QbdSfM8pDLaicFsNIcDI64vBcW3sb0HupF9zHgnZNRCQmrD+/r7nZvSQaTonVC5/BILheoRMrgA+QGLJK34ASPNYg4EMRBnNv5VfrwtqLWvFEA3j+2XxdiBrIW1H7JPF/cuwamvZ8W08ZxL3q5sT1/SXKUJA5lLC2zrhdmn+A4E8Olzrqw5Xw8dKnTP29DVnjVAdhiMpwB+BNBgw==</Modulus><Exponent>AQAB</Exponent></RSAKeyValue>"
    # auth = "WyI5MjI4MTUxNSIsInp4TEU1NVFGbXJLUW1ZQU9EUndiZThJVXV5dSt0bzVPU2tSZGYzV08iXQ=="
    # if os.path.exists("licence_valid.txt"):
    #     with open("licence_valid.txt", "r") as f:
    #         lines = f.read().strip().split("\n")
    #         if len(lines) != 2:
    #         # If the file does not have exactly two lines, it's corrupted or incorrectly formatted
    #             os.remove("licence_valid.txt")
    #         return False
    #     product_id, license_key = lines  
    #     # Verify with API
    #     result = Key.activate(
    #         token=auth,
    #         rsa_pub_key=RSAPubKey,
    #         product_id=product_id,
    #         key=license_key,
    #         machine_code=Helpers.GetMachineCode(v=2)    
    #     )
    #     if result[0] is None or not Helpers.IsOnRightMachine(result[0], v=2):
    #         os.remove("licence_valid.txt") 
    #         return False
    #     return True
    return True

def create_window():
    """Create and return the appropriate window based on license validity."""
    if check_license_with_api():
        return CommWindow()
    return LicenceWindow()
if __name__ == "__main__":
    try:
        app=QApplication(sys.argv)
        window=create_window()
        window.setWindowTitle("SensorMart")
        window.show()
        sys.exit(app.exec_())
    except RuntimeError as e:
        # Handle specific known exceptions
        error_dialog = QErrorMessage()
        error_dialog.showMessage(f"A runtime error occurred:\n{str(e)}")
        error_dialog.exec_()
        sys.exit(1)
    except Exception as e:
        # Catch any other exceptions
        error_dialog = QErrorMessage()
        error_dialog.showMessage(f"An unexpected error occurred:\n{str(e)}")
        error_dialog.exec_()
        sys.exit(1)                                               
       