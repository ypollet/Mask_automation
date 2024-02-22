from logging.handlers import QueueHandler

import sys
# setting path
sys.path.append('./GUI')

from typing import Tuple
from PySide6.QtWidgets import (
    QApplication
)

from PySide6.QtGui import QScreen

import GUI.main as main

app = QApplication(sys.argv)

w = main.MainWindow()

w.show()
app.exec()