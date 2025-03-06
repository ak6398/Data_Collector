from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
import sys
import os
from licensing.models import *
from licensing.methods import Key, Helpers
from .communication import CommWindow
from configuration.utils import resource_path



class LicenceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Licence Window")
        self.setWindowIcon(QIcon("../logo.png"))
        ui_file=resource_path("Gui/licence.ui")
        uic.loadUi(ui_file,self)
        self.licence_btn.clicked.connect(self.on_licencebtn_clicked)
        

    def on_licencebtn_clicked(self):
        
        RSAPubKey = "<RSAKeyValue><Modulus>0rJNm16LrlZRF+9G5BYPleIoxOCZk2pkTYeC3Dnn/fI1fjYBIhqx6sPYG4tE9ByLZoz5V6cakctPQEKq4iDbKYBfZB57Rtca22Z3m2a8gKVqppln6pJWa3R55+lKO6ZH5KwfE5QbdSfM8pDLaicFsNIcDI64vBcW3sb0HupF9zHgnZNRCQmrD+/r7nZvSQaTonVC5/BILheoRMrgA+QGLJK34ASPNYg4EMRBnNv5VfrwtqLWvFEA3j+2XxdiBrIW1H7JPF/cuwamvZ8W08ZxL3q5sT1/SXKUJA5lLC2zrhdmn+A4E8Olzrqw5Xw8dKnTP29DVnjVAdhiMpwB+BNBgw==</Modulus><Exponent>AQAB</Exponent></RSAKeyValue>"
        auth = "WyI5MjI4MTUxNSIsInp4TEU1NVFGbXJLUW1ZQU9EUndiZThJVXV5dSt0bzVPU2tSZGYzV08iXQ=="

        result = Key.activate(token=auth,\
                        rsa_pub_key=RSAPubKey,\
                        product_id=self.product_id_edit.text(), \
                        key=self.licence_edit.text(),\
                        machine_code=Helpers.GetMachineCode(v=2))

        if result[0] == None or not Helpers.IsOnRightMachine(result[0], v=2):
            # an error occurred or the key is invalid or it cannot be activated
            # (eg. the limit of activated devices was achieved)
            print("The license does not work: {0}".format(result[1]))
            QMessageBox.warning(self, "Invalid License or product id", "invalid value cannot be activated.")
        else:
            with open("licence_valid.txt",'w') as f:
                f.write(f"{self.product_id_edit.text()}\n{self.licence_edit.text()}")
            self.open_comm_window()

            # everything went fine if we are here!
            print("The license is valid!")
            license_key = result[0]
            print("Feature 1: " + str(license_key.f1))
            print("License expires: " + str(license_key.expires))
            
    def open_comm_window(self):
        
        self.commwindow1 = CommWindow()
        self.commwindow1.show()
        self.close()



