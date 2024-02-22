from PySide6.QtWidgets import (
    QMainWindow, QStackedLayout, QHBoxLayout, QVBoxLayout, 
    QWidget, QLabel , QPushButton, QFileDialog
)
from PySide6.QtCore import(
    Signal
)


from GUI import mask_creation

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.window_layout = QStackedLayout()
        self.select_images_to_mask = ViewFiles()

        self.window_layout.addWidget(self.select_images_to_mask)
        self.window_layout.setCurrentIndex(0)

        self.mask_display = mask_creation.DisplayMask()
        self.window_layout.addWidget(self.mask_display)

        self.select_images_to_mask.display_masks.connect(self.display_mask_creation)

        widget = QWidget()
        widget.setLayout(self.window_layout)
        self.setCentralWidget(widget)

        self.setWindowTitle("Main page")
        self.display_mask_creation()

    def display_mask_creation(self):
        if self.mask_display.load_images(list(sorted(self.select_images_to_mask.files))):
            self.window_layout.setCurrentIndex(1)


class ViewFiles(QWidget):
    display_masks = Signal()
    def __init__(self):
        super(ViewFiles, self).__init__()

        self.v_layout = QVBoxLayout()

        self.files = set(['/home/psadmin/Numerisation/images/Eupholus/_x_00000_y_00960_.jpg', '/home/psadmin/Numerisation/images/Eupholus/_x_00000_y_02240_.jpg', '/home/psadmin/Numerisation/images/Eupholus/_x_00000_y_02880_.jpg', '/home/psadmin/Numerisation/images/Eupholus/_x_00050_y_00960_.jpg', '/home/psadmin/Numerisation/images/Eupholus/_x_00050_y_02720_.jpg'])
        self.select = SelectFiles()
        self.select.add_files.connect(self.set_files)
        self.v_layout.addWidget(self.select)

        self.go_to_mask = QPushButton("Mask 0 images")
        self.v_layout.addWidget(self.go_to_mask)

        self.go_to_mask.clicked.connect(self.display_masks.emit)

        self.setLayout(self.v_layout)

    def set_files(self, files):
        self.files.update(files)
        self.go_to_mask.setText(f"Mask {len(files)} images")


class SelectFiles(QWidget):
    add_files = Signal(object)

    def __init__(self):
        super(SelectFiles, self).__init__()

        self.h_layout = QHBoxLayout()

        self.label = QLabel("Select all images")
        self.h_layout.addWidget(self.label)

        self.browse = QPushButton("Browse..")
        self.h_layout.addWidget(self.browse)

        self.browse.clicked.connect(self.selectImages)

        self.setLayout(self.h_layout)


    def selectImages(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Save File", ".", "images (*.jpg *.jpeg *.tif *.tiff *.png)")
        self.add_files.emit(files)

