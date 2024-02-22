from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QLabel, QTabWidget, QSpinBox, QPushButton, QSizePolicy
)

from PySide6.QtGui import (
    QPalette, QPixmap, QResizeEvent, QImage, QIcon
)

from PySide6.QtCore import Qt, Signal, QSize

from scripts.mask_generator import MaskGenerator, CannyGenerator, ThreshGenerator


INIT_MIN = 50
INIT_MAX = 150
INIT_MAX_VAL = 255

class DisplayMask(QWidget):
    def __init__(self, images=None):
        super(DisplayMask, self).__init__()
        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0,0,0,0)
        self.image_choice = ImageChoice(images)
        self.image_choice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.v_layout.addWidget(self.image_choice)
        self.comparison = ComparisonImageMask(images[0] if images else None)
        self.v_layout.addWidget(self.comparison)

        self.parameters = MaskParameters()
        self.v_layout.addWidget(self.parameters)
        self.parameters.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.parameters.new_mask.connect(self.update_mask)
        self.image_choice.new_image.connect(self.set_image)

        self.parameters.update_mask()
        
        self.setLayout(self.v_layout)

    def load_images(self, images : list = None):
        self.image_choice.load_images(images)
        self.comparison.set_image(images[0] if len(images) > 0 else None)
        self.parameters.update_mask()
        return images
        
    def update_mask(self, mask_generator : MaskGenerator):
        self.comparison.generate_mask(mask_generator)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.parameters.update_mask()

    def set_image(self, image_path):
        self.comparison.set_image(image_path)
        self.parameters.update_mask()

class ImageChoice(QWidget):
    new_image = Signal(object)
    def __init__(self, images=None):
        super(ImageChoice, self).__init__()

        self.full_layout = QHBoxLayout()
        self.images = images if images else []
        self.index = 0
        self.title = QLabel(f"Image : ")
        self.image = QLabel(self.images[self.index] if self.index >= 0 and self.index < len(self.images) else None)
        self.pos_img = QLabel(f"{self.index+1}/{len(self.images)}")

        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.pos_img.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        self.left = QPushButton()
        self.left.setIcon(QIcon("resources/icons/arrow-180.png"))
        self.left.setIconSize(QSize(30, 30))
        self.left.clicked.connect(self.decrement_index)
        self.left.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self.right = QPushButton()
        self.right.setIcon(QIcon("resources/icons/arrow.png"))
        self.right.setIconSize(QSize(30, 30))
        self.right.clicked.connect(self.increment_index)
        self.left.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self.full_layout.addWidget(self.title)
        self.full_layout.addWidget(self.image)
        self.full_layout.addWidget(self.left)
        self.full_layout.addWidget(self.pos_img)
        self.full_layout.addWidget(self.right)

        self.setLayout(self.full_layout)

    def load_images(self, images : list = None):
        self.images = images if images else []
        self.index = 0
        self.title.setText(f"Image : ")
        self.image.setText(self.images[self.index] if self.index >= 0 and self.index < len(self.images) else None)
        self.pos_img.setText(f"{self.index+1}/{len(self.images)}")

    def increment_index(self):
        if self.index < len(self.images)-1:
            self.index += 1
            self.update_image()
    
    def decrement_index(self):
        if self.index > 0:
            self.index -= 1
            self.update_image()

    def update_image(self):
        self.image.setText(self.images[self.index] if self.index >= 0 and self.index < len(self.images) else None)
        self.pos_img.setText(f"{self.index+1}/{len(self.images)}")
        self.new_image.emit(self.images[self.index])

class ComparisonImageMask(QWidget):

    def __init__(self, image_path):
        super(ComparisonImageMask, self).__init__()
        self.h_layout = QHBoxLayout()

        self.image_widget = QLabel()
        self.image_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.image_widget.setMinimumSize(100,100)
    

        self.mask_widget = QLabel()
        self.mask_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.mask_widget.setMinimumSize(100,100)

        self.h_layout.addWidget(self.image_widget)
        self.h_layout.addWidget(self.mask_widget)

        self.image_path = None
        self.image = None

        self.set_image(image_path)

        self.setLayout(self.h_layout)

    def set_image(self, image_path):
        if image_path is not None:
            self.image_path = image_path       
            self.image = QPixmap(image_path)
            self.mask_img = QPixmap(image_path)
            self.image_widget.setPixmap(self.image.scaled(self.image_widget.width(), self.image_widget.height(), Qt.AspectRatioMode.KeepAspectRatio))
            self.mask_widget.setPixmap(self.image.scaled(self.mask_widget.width(), self.mask_widget.height(), Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.image_widget.setBackgroundRole(QPalette.ColorRole.Base)
            self.mask_widget.setBackgroundRole(QPalette.ColorRole.Base)
    
    def generate_mask(self, mask_generator : MaskGenerator):
        if(self.image_path is None):
            return
        mask = mask_generator.generate_mask(self.image_path)
        height, width = mask.shape
        mask_img = QImage(mask.data, width, height, width, QImage.Format.Format_Grayscale8)

        self.mask_img = QPixmap(mask_img)
        self.mask_widget.setPixmap(self.mask_img.scaled(self.mask_widget.width(), self.mask_widget.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.image is not None:
            self.image_widget.setPixmap(self.image.scaled(self.image_widget.width(), self.image_widget.height(), Qt.AspectRatioMode.KeepAspectRatio))
            self.mask_widget.setPixmap(self.mask_img.scaled(self.mask_widget.width(), self.mask_widget.height(), Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.image_widget.setBackgroundRole(QPalette.ColorRole.Base)
            self.mask_widget.setBackgroundRole(QPalette.ColorRole.Base)


        
class MaskParameters(QTabWidget):

    new_mask = Signal(object)
    def __init__(self):
        super(MaskParameters, self).__init__()
        self.setTabPosition(QTabWidget.TabPosition.North)

        self.canny = CannyOutputParameters()
        self.canny.update_mask.connect(self.update_mask)
        self.canny.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.thresh = ThreshOutputParameters()
        self.thresh.update_mask.connect(self.update_mask)
        self.canny.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.addTab(self.canny, "canny")
        self.addTab(self.thresh, "threshold")

        self.setCurrentIndex(0)
        self.currentChanged.connect(self.update_mask)
        self.update_mask()

    def update_mask(self):
        match self.currentIndex():
            case 0:
                self.update_mask_canny()
            case 1:
                self.update_mask_thresh()
            

    def update_mask_canny(self):

        self.new_mask.emit(self.canny.get_generator())
    
    def update_mask_thresh(self):
        self.new_mask.emit(self.thresh.get_generator())


class CannyOutputParameters(QWidget):
    update_mask = Signal()
    def __init__(self):
        super(CannyOutputParameters, self).__init__()
        self.full_layout = QVBoxLayout()

        self.options_layout = QHBoxLayout()

        self.floodfill = QPushButton("Floodfill")
        self.floodfill.setCheckable(True)
        self.draw_contour = QPushButton("draw contour")
        self.draw_contour.setCheckable(True)

        self.options_layout.addWidget(self.floodfill)
        self.options_layout.addWidget(self.draw_contour)

        self.min_thresh = SpinBoxLabel("Min threshold", 0, INIT_MAX)
        self.min_thresh.setValue(INIT_MIN)
        
        self.max_thresh = SpinBoxLabel("Max threshold", INIT_MIN, 255)
        self.max_thresh.setValue(INIT_MAX)

        self.min_thresh.valueChanged.connect(self.lower_bound)
        self.max_thresh.valueChanged.connect(self.upper_bound)

        self.blur = SpinBoxLabel("Blur", 1, -1)
        self.blur.setValue(3)
        self.blur.setSingleStep(2)

        self.morpho = SpinBoxLabel("Noise Cancelling", 1, -1)
        self.morpho.setValue(3)
        self.morpho.setSingleStep(2)

        self.full_layout.addLayout(self.options_layout)
        self.full_layout.addWidget(self.min_thresh)
        self.full_layout.addWidget(self.max_thresh)
        self.full_layout.addWidget(self.blur)
        self.full_layout.addWidget(self.morpho)

        #update mask when value change
        self.floodfill.clicked.connect(self.update_mask.emit)
        self.draw_contour.clicked.connect(self.update_mask.emit)
        self.min_thresh.update_mask.connect(self.update_mask.emit)
        self.max_thresh.update_mask.connect(self.update_mask.emit)
        self.blur.update_mask.connect(self.update_mask.emit)
        self.morpho.update_mask.connect(self.update_mask.emit)
        self.setLayout(self.full_layout)


    def lower_bound(self, new_min):
        self.max_thresh.setMinimum(new_min)
    
    def upper_bound(self, new_max):
        self.min_thresh.setMaximum(new_max)

    def get_generator(self):
        thresh_min = self.min_thresh.value()
        thresh_max = self.max_thresh.value()
        blur = self.blur.value()
        morpho = self.morpho.value()
        floodfill = self.floodfill.isChecked()
        draw_contour = self.draw_contour.isChecked()
        return CannyGenerator(thresh_min, thresh_max, blur, morpho, floodfill, draw_contour)

class ThreshOutputParameters(QWidget):
    update_mask = Signal()
    def __init__(self):
        super(ThreshOutputParameters, self).__init__()
        self.full_layout = QVBoxLayout()
        self.full_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.options_layout = QHBoxLayout()

        self.floodfill = QPushButton("Floodfill")
        self.floodfill.setCheckable(True)
        self.draw_contour = QPushButton("draw contour")
        self.draw_contour.setCheckable(True)

        self.options_layout.addWidget(self.floodfill)
        self.options_layout.addWidget(self.draw_contour)
        
        self.thresh_layout = QHBoxLayout()
        self.otsu = QPushButton("Automatic thresh")
        self.otsu.setCheckable(True)
        self.otsu.setChecked(True)
        self.otsu.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.otsu.clicked.connect(self.show_tresh)
        self.thresh = SpinBoxLabel("Threshold", 0, 255)
        self.thresh.setValue(INIT_MIN)
        self.thresh.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.thresh.hide()
        self.placeholder = QLabel()
        self.placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.thresh_layout.addWidget(self.otsu)
        self.thresh_layout.addWidget(self.thresh)
        self.thresh_layout.addWidget(self.placeholder)
        
        self.max_val = SpinBoxLabel("Max value", 0, 255)
        self.max_val.setValue(INIT_MAX_VAL)

        self.blur = SpinBoxLabel("Blur", 1, -1)
        self.blur.setValue(3)
        self.blur.setSingleStep(2)

        self.morpho = SpinBoxLabel("Noise Cancelling", 1, -1)
        self.morpho.setValue(3)
        self.morpho.setSingleStep(2)

        self.morpho = SpinBoxLabel("Noise Cancelling", 1, -1)
        self.morpho.setValue(3)
        self.morpho.setSingleStep(2)

        self.background = QPushButton("Inverse Background")
        self.background.setCheckable(True)

        self.full_layout.addLayout(self.options_layout)
        self.full_layout.addLayout(self.thresh_layout)
        self.full_layout.addWidget(self.max_val)
        self.full_layout.addWidget(self.blur)
        self.full_layout.addWidget(self.morpho)
        self.full_layout.addWidget(self.background)

        #update mask when value change
        self.floodfill.clicked.connect(self.update_mask.emit)
        self.draw_contour.clicked.connect(self.update_mask.emit)
        self.otsu.clicked.connect(self.update_mask.emit)
        self.thresh.update_mask.connect(self.update_mask.emit)
        self.max_val.update_mask.connect(self.update_mask.emit)
        self.blur.update_mask.connect(self.update_mask.emit)
        self.morpho.update_mask.connect(self.update_mask.emit)
        self.background.clicked.connect(self.update_mask.emit)
        self.setLayout(self.full_layout)

    def show_tresh(self):
        if self.otsu.isChecked():
            self.thresh.hide()
            self.placeholder.show()
        else:
            self.placeholder.hide()
            self.thresh.show()
    
    def get_generator(self):
        thresh = self.thresh.value()
        max_val = self.max_val.value()
        blur = self.blur.value()
        morpho = self.morpho.value()
        white_background = self.background.isChecked()
        auto_thresh = self.otsu.isChecked()
        floodfill = self.floodfill.isChecked()
        draw_contour = self.draw_contour.isChecked()
        
        return ThreshGenerator(thresh, max_val, blur, morpho, white_background, auto_thresh, floodfill, draw_contour)

class SpinBoxLabel(QWidget):
    valueChanged = Signal(int)
    update_mask = Signal()
    def __init__(self, label, min=-1, max=-1):
        super(SpinBoxLabel, self).__init__()

        self.h_layout = QHBoxLayout()
        self.label = QLabel(f"{label} :")
        self.spinbox = QSpinBox()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.spinbox)

        self.spinbox.valueChanged.connect(self.valueChanged.emit)
        self.spinbox.valueChanged.connect(self.updated_val)

        if min >= 0:
            self.spinbox.setMinimum(min)
        
        if max >= 0:
            self.spinbox.setMaximum(max)
        
        self.setLayout(self.h_layout)
    
    def setMinimum(self, val):
        self.spinbox.setMinimum(val)
    
    def setMaximum(self, val):
        self.spinbox.setMaximum(val)

    def value(self):
        return self.spinbox.value()

    def setValue(self, val):
        self.spinbox.setValue(val)
    
    def setSingleStep(self, val):
        self.spinbox.setSingleStep(val)

    def updated_val(self):
        self.update_mask.emit()





