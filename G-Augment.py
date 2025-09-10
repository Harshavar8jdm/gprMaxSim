"""
G-Augment: GPR Cropper with Image Augmentation Features

Requirements:

- Python 3.7 or Above
- Virtual Environment

Install dependencies:

1. Create a virtual environment:
    For Windows:

     Activate virtual environment (Command Prompt):
    .venv\Scripts\activate.bat

     Or if using PowerShell:
    .venv\Scripts\Activate.ps1

     Install dependencies
    pip install Pillow PyQt5 numpy


    For Linux:
    python3 -m venv .venv
    source .venv/bin/activate

2. Install required Python packages:
    pip install Pillow PyQt5 numpy

 How to run the app:
    Linux:
    source .venv/bin/activate      # Activate virtual environment
    python3 G-Augment.py           # Run the application

    Windows:
    #<venv_name>\Scripts\activate.bat  # Activate virtual environment
    python3 G-Augment.py               # Run the application

 What it does:
- Allows cropping images with a draggable crop box
- Apply Gaussian noise, Brightness, Contrast, Blur/Sharpen, and Horizontal Flip
- Saves the original cropped image in 'cropped_output' folder
- Saves the filtered (augmented) image in 'augmented_output' folder
"""





import sys, os, glob
import numpy as np
from PIL import ImageEnhance, Image, ImageFilter
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QFileDialog,
    QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QSlider, QCheckBox, QComboBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRect

class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap():
            qp = QPainter(self)
            pen = QPen(QColor(0, 255, 0), 2)
            qp.setPen(pen)
            qp.drawRect(self.parent.crop_x, self.parent.crop_y, self.parent.crop_w, self.parent.crop_h)

class CropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPR Cropper with Augmentations")
        self.setGeometry(100, 100, 1000, 750)

        self.crop_x, self.crop_y = 100, 100
        self.crop_w, self.crop_h = 400, 400
        self.dragging = False
        self.image_paths = []
        self.current_index = 0
        self.image_pixmap = None
        self.original_image = None
        self.display_scale = 1.0

        self.image_label = ImageLabel(self)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.start_drag
        self.image_label.mouseMoveEvent = self.do_drag
        self.image_label.mouseReleaseEvent = self.end_drag
        self.image_label.setAlignment(Qt.AlignCenter)

        self.x_input = QLineEdit(str(self.crop_x))
        self.y_input = QLineEdit(str(self.crop_y))
        self.w_input = QLineEdit(str(self.crop_w))
        self.h_input = QLineEdit(str(self.crop_h))
        for box in [self.x_input, self.y_input, self.w_input, self.h_input]:
            box.setFixedWidth(60)
            box.editingFinished.connect(self.update_crop_position)

        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("X:")); coord_layout.addWidget(self.x_input)
        coord_layout.addWidget(QLabel("Y:")); coord_layout.addWidget(self.y_input)
        coord_layout.addWidget(QLabel("W:")); coord_layout.addWidget(self.w_input)
        coord_layout.addWidget(QLabel("H:")); coord_layout.addWidget(self.h_input)

        # Buttons
        self.btn_open = QPushButton("Open Folder")
        self.btn_prev = QPushButton("Previous")
        self.btn_next = QPushButton("Next")
        self.btn_open.clicked.connect(self.open_folder)
        self.btn_prev.clicked.connect(self.show_prev_image)
        self.btn_next.clicked.connect(self.save_and_show_next_image)

        # Augmentation Controls
        self.noise_label = QLabel("Noise:")
        self.noise_slider = QSlider(Qt.Horizontal)
        self.noise_slider.setMinimum(0)
        self.noise_slider.setMaximum(100)
        self.noise_slider.setValue(0)
        self.noise_slider.setFixedWidth(150)
        self.noise_slider.setTickInterval(10)
        self.noise_slider.setTickPosition(QSlider.TicksBelow)

        self.brightness_dropdown = QComboBox()
        self.brightness_dropdown.addItems(["50%", "75%", "100%", "125%", "150%", "175%", "200%"])
        self.brightness_dropdown.setCurrentText("100%")
        self.brightness_dropdown.setFixedWidth(90)

        self.contrast_dropdown = QComboBox()
        self.contrast_dropdown.addItems(["50%", "75%", "100%", "125%", "150%", "175%", "200%"])
        self.contrast_dropdown.setCurrentText("100%")
        self.contrast_dropdown.setFixedWidth(90)

        self.kernel_slider = QSlider(Qt.Horizontal)
        self.kernel_slider.setMinimum(-1)
        self.kernel_slider.setMaximum(1)
        self.kernel_slider.setValue(0)
        self.kernel_slider.setFixedWidth(100)
        self.kernel_slider.setTickInterval(1)
        self.kernel_slider.setTickPosition(QSlider.TicksBelow)
        self.kernel_slider.setToolTip("Move left to blur, right to sharpen")

        kernel_layout = QHBoxLayout()
        kernel_layout.addWidget(QLabel("Blur"))
        kernel_layout.addWidget(self.kernel_slider)
        kernel_layout.addWidget(QLabel("Sharpen"))

        augment_layout = QHBoxLayout()
        augment_layout.addWidget(self.noise_label)
        augment_layout.addWidget(self.noise_slider)
        augment_layout.addWidget(QLabel("Brightness:"))
        augment_layout.addWidget(self.brightness_dropdown)
        augment_layout.addWidget(QLabel("Contrast:"))
        augment_layout.addWidget(self.contrast_dropdown)

        # Flip
        self.flip_checkbox = QCheckBox("Flip Horizontally")
        self.flip_checkbox.setChecked(False)
        flip_layout = QHBoxLayout()
        flip_layout.addWidget(self.flip_checkbox)

        # Final Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self.image_label, stretch=1)
        layout.addWidget(QLabel("<b>Crop Box Coordinates</b>"))
        layout.addLayout(coord_layout)
        layout.addLayout(augment_layout)
        layout.addLayout(kernel_layout)
        layout.addLayout(flip_layout)

        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.btn_open)
        btn_container.addWidget(self.btn_prev)
        btn_container.addWidget(self.btn_next)
        btn_container.addStretch()
        layout.addLayout(btn_container)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_paths = []
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"):
                self.image_paths.extend(glob.glob(os.path.join(folder, ext)))
            self.image_paths.sort()
            self.current_index = 0
            os.makedirs("cropped_output", exist_ok=True)
            os.makedirs("augmented_output", exist_ok=True)
            self.load_image()

    def resizeEvent(self, event):
        self.load_image()

    def load_image(self):
        if 0 <= self.current_index < len(self.image_paths):
            image_path = self.image_paths[self.current_index]
            self.original_image = Image.open(image_path).convert("RGB")
            qimage = QPixmap(image_path)
            self.image_label.clear()

            max_width = self.image_label.width()
            max_height = self.image_label.height()
            if max_width == 0 or max_height == 0:
                max_width, max_height = 800, 600

            img_width = qimage.width()
            img_height = qimage.height()

            scale = min(1.0, max_width / img_width, max_height / img_height)
            self.display_scale = scale

            scaled_pixmap = qimage.scaled(
                int(img_width * scale),
                int(img_height * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_pixmap = scaled_pixmap
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setFixedSize(scaled_pixmap.size())
            self.image_label.repaint()

    def start_drag(self, event):
        padding = 10
        rect = QRect(self.crop_x - padding, self.crop_y - padding, self.crop_w + 2 * padding, self.crop_h + 2 * padding)
        if rect.contains(event.pos()):
            self.dragging = True
            self.drag_offset = event.pos() - rect.topLeft()

    def do_drag(self, event):
        if self.dragging:
            new_pos = event.pos() - self.drag_offset
            self.crop_x = max(0, new_pos.x())
            self.crop_y = max(0, new_pos.y())
            self.x_input.setText(str(self.crop_x))
            self.y_input.setText(str(self.crop_y))
            self.image_label.repaint()

    def end_drag(self, event):
        self.dragging = False

    def update_crop_position(self):
        try:
            self.crop_x = int(self.x_input.text())
            self.crop_y = int(self.y_input.text())
            self.crop_w = int(self.w_input.text())
            self.crop_h = int(self.h_input.text())
            self.image_label.repaint()
        except ValueError:
            pass

    def apply_gaussian_noise(self, img, slider_value):
        arr = np.array(img).astype(np.float32)
        stddev = (slider_value / 100.0) * 25.0
        noise = np.random.normal(0, stddev, arr.shape)
        noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_arr)

    def save_crop(self):
        if not self.original_image:
            print("No original image loaded.")
            return

        scale = 1 / self.display_scale
        left = int(self.crop_x * scale)
        top = int(self.crop_y * scale)
        right = int(left + self.crop_w * scale)
        bottom = int(top + self.crop_h * scale)

        img_width, img_height = self.original_image.size
        left = max(0, min(left, img_width))
        right = max(0, min(right, img_width))
        top = max(0, min(top, img_height))
        bottom = max(0, min(bottom, img_height))

        cropped = self.original_image.crop((left, top, right, bottom))
        base_name = os.path.splitext(os.path.basename(self.image_paths[self.current_index]))[0]
        suffixes = []

        if self.flip_checkbox.isChecked():
            cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
            suffixes.append("flip")

        brightness = int(self.brightness_dropdown.currentText().replace('%', ''))
        if brightness != 100:
            enhancer = ImageEnhance.Brightness(cropped)
            cropped = enhancer.enhance(brightness / 100.0)
            suffixes.append(f"bright{brightness}")

        contrast = int(self.contrast_dropdown.currentText().replace('%', ''))
        if contrast != 100:
            enhancer = ImageEnhance.Contrast(cropped)
            cropped = enhancer.enhance(contrast / 100.0)
            suffixes.append(f"contrast{contrast}")

        kernel_value = self.kernel_slider.value()
        if kernel_value == -1:
            cropped = cropped.filter(ImageFilter.BLUR)
            suffixes.append("blur")
        elif kernel_value == 1:
            cropped = cropped.filter(ImageFilter.SHARPEN)
            suffixes.append("sharpen")

        cropped_name = base_name + ("_" + "_".join(suffixes) if suffixes else "") + ".png"
        cropped_path = os.path.join("cropped_output", cropped_name)
        cropped.save(cropped_path, format="PNG")
        print(f"Saved: {cropped_path}")

        stddev_value = self.noise_slider.value()
        if stddev_value > 0:
            noisy_img = self.apply_gaussian_noise(cropped, stddev_value)
            noise_suffix = f"noisy{stddev_value}"
            all_suffixes = suffixes + [noise_suffix]
            noisy_name = base_name + "_" + "_".join(all_suffixes) + ".png"
            noisy_path = os.path.join("augmented_output", noisy_name)
            noisy_img.save(noisy_path, format="PNG")
            print(f"Saved noisy: {noisy_path}")

    def save_and_show_next_image(self):
        if self.current_index < len(self.image_paths):
            self.save_crop()
            self.current_index += 1
            if self.current_index < len(self.image_paths):
                self.load_image()

    def show_prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CropApp()
    window.show()
    sys.exit(app.exec_())
