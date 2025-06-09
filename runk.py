from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout, QMessageBox,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt
import sys

class ShapeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Shape")
        self.setStyleSheet(parent.load_styles())

        self.shape_type = QComboBox()
        self.shape_type.addItems(["Sphere", "Cylinder", "Block", "Ellipsoid", "Cone"])
        self.shape_type.currentTextChanged.connect(self.update_form)

        self.form_layout = QFormLayout()

        self.param_widgets = {}

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("Select Shape Type:"))
        main_layout.addWidget(self.shape_type)
        main_layout.addLayout(self.form_layout)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)

        self.update_form(self.shape_type.currentText())

    def clear_form(self):
        # Remove all param widgets
        for label, widget in self.param_widgets.values():
            self.form_layout.removeWidget(label)
            label.deleteLater()
            self.form_layout.removeWidget(widget)
            widget.deleteLater()
        self.param_widgets.clear()

    def update_form(self, shape):
        self.clear_form()
        # Define required params per shape
        params = []
        if shape == "Sphere":
            params = ["Center X", "Center Y", "Center Z", "Radius"]
        elif shape == "Cylinder":
            params = ["Base X", "Base Y", "Base Z", "Radius", "Height"]
        elif shape == "Block":
            params = ["Start X", "Start Y", "Start Z", "End X", "End Y", "End Z"]
        elif shape == "Ellipsoid":
            params = ["Center X", "Center Y", "Center Z", "Radius X", "Radius Y", "Radius Z"]
        elif shape == "Cone":
            params = ["Base X", "Base Y", "Base Z", "Base Radius", "Height"]

        for p in params:
            label = QLabel(p + ":")
            widget = QLineEdit()
            self.form_layout.addRow(label, widget)
            self.param_widgets[p] = (label, widget)

    def get_shape_data(self):
        shape = self.shape_type.currentText()
        data = {"type": shape}
        for param, (label, widget) in self.param_widgets.items():
            val = widget.text().strip()
            if not val:
                val = "0"
            data[param.lower().replace(" ", "_")] = val
        return data


class GPRMaxInputGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gprMax Input File Generator (Basic)")
        self.setGeometry(100, 100, 600, 750)
        self.setStyleSheet(self.load_styles())
        self.shapes = []  # Store shape dicts here
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        form_layout.addRow("Title:", self.title_input)

        # Domain (x y z)
        self.domain_x, self.domain_y, self.domain_z = QLineEdit(), QLineEdit(), QLineEdit()
        domain_layout = QHBoxLayout()
        domain_layout.addWidget(self.domain_x)
        domain_layout.addWidget(self.domain_y)
        domain_layout.addWidget(self.domain_z)
        form_layout.addRow("Domain (x y z):", domain_layout)

        # dx dy dz
        self.dx, self.dy, self.dz = QLineEdit(), QLineEdit(), QLineEdit()
        dxdy_layout = QHBoxLayout()
        dxdy_layout.addWidget(self.dx)
        dxdy_layout.addWidget(self.dy)
        dxdy_layout.addWidget(self.dz)
        form_layout.addRow("dx dy dz:", dxdy_layout)

        # Time Window
        self.time_window = QLineEdit()
        form_layout.addRow("Time Window (e.g., 3e-9):", self.time_window)

        # Waveform type and params
        self.waveform_type = QComboBox()
        self.waveform_type.addItems([
            "ricker", "gaussian", "gaussiandot", "gaussiandotnorm",
            "gaussiandotdot", "gaussiandotdotnorm", "contsine"
        ])
        self.waveform_amp = QLineEdit()
        self.waveform_freq = QLineEdit()
        self.waveform_name = QLineEdit()
        form_layout.addRow("Waveform Type:", self.waveform_type)
        form_layout.addRow("Amplitude:", self.waveform_amp)
        form_layout.addRow("Frequency (Hz):", self.waveform_freq)
        form_layout.addRow("Waveform Name:", self.waveform_name)

        # Hertzian Dipole Orientation and coordinates
        self.hertz_orientation = QLineEdit("z")
        self.hertz_x, self.hertz_y, self.hertz_z = QLineEdit(), QLineEdit(), QLineEdit()
        hertz_layout = QHBoxLayout()
        hertz_layout.addWidget(self.hertz_x)
        hertz_layout.addWidget(self.hertz_y)
        hertz_layout.addWidget(self.hertz_z)
        form_layout.addRow("Hertzian Dipole (x y z):", hertz_layout)
        form_layout.addRow("Orientation:", self.hertz_orientation)

        # Receiver location (x y z)
        self.rx_x, self.rx_y, self.rx_z = QLineEdit(), QLineEdit(), QLineEdit()
        rx_layout = QHBoxLayout()
        rx_layout.addWidget(self.rx_x)
        rx_layout.addWidget(self.rx_y)
        rx_layout.addWidget(self.rx_z)
        form_layout.addRow("Receiver Location (x y z):", rx_layout)

        # TX Steps (x y z)
        self.src_step_x, self.src_step_y, self.src_step_z = QLineEdit(), QLineEdit(), QLineEdit()
        src_step_layout = QHBoxLayout()
        src_step_layout.addWidget(self.src_step_x)
        src_step_layout.addWidget(self.src_step_y)
        src_step_layout.addWidget(self.src_step_z)
        form_layout.addRow("TX Steps (x y z):", src_step_layout)

        # RX Steps (x y z)
        self.rx_step_x, self.rx_step_y, self.rx_step_z = QLineEdit(), QLineEdit(), QLineEdit()
        rx_step_layout = QHBoxLayout()
        rx_step_layout.addWidget(self.rx_step_x)
        rx_step_layout.addWidget(self.rx_step_y)
        rx_step_layout.addWidget(self.rx_step_z)
        form_layout.addRow("RX Steps (x y z):", rx_step_layout)

        # Box End (x y z)
        self.box_end_x, self.box_end_y, self.box_end_z = QLineEdit(), QLineEdit(), QLineEdit()
        box_end_layout = QHBoxLayout()
        box_end_layout.addWidget(self.box_end_x)
        box_end_layout.addSpacing(10)
        box_end_layout.addWidget(self.box_end_y)
        box_end_layout.addSpacing(10)
        box_end_layout.addWidget(self.box_end_z)
        form_layout.addRow("Box End (x y z):", box_end_layout)

        layout.addLayout(form_layout)

        # Shapes Section
        shapes_layout = QVBoxLayout()
        shapes_label = QLabel("Shapes (Add multiple):")
        shapes_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 15px;")
        shapes_layout.addWidget(shapes_label)

        self.shapes_list = QListWidget()
        shapes_layout.addWidget(self.shapes_list)

        btn_layout = QHBoxLayout()
        self.add_shape_btn = QPushButton("➕ Add Shape")
        self.remove_shape_btn = QPushButton("🗑️ Remove Selected Shape")
        btn_layout.addWidget(self.add_shape_btn)
        btn_layout.addWidget(self.remove_shape_btn)
        shapes_layout.addLayout(btn_layout)

        layout.addLayout(shapes_layout)

        self.add_shape_btn.clicked.connect(self.open_add_shape_dialog)
        self.remove_shape_btn.clicked.connect(self.remove_selected_shape)

        generate_btn = QPushButton("💾 Generate gprMax Input File")
        generate_btn.clicked.connect(self.generate_input_file)
        layout.addWidget(generate_btn)

        self.setLayout(layout)

    def open_add_shape_dialog(self):
        dialog = ShapeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            shape_data = dialog.get_shape_data()
            self.shapes.append(shape_data)
            self.update_shapes_list()

    def update_shapes_list(self):
        self.shapes_list.clear()
        for shape in self.shapes:
            desc = f"{shape['type']}: " + ", ".join(
                f"{k.replace('_',' ').title()}={v}" for k,v in shape.items() if k != 'type'
            )
            self.shapes_list.addItem(desc)

    def remove_selected_shape(self):
        selected = self.shapes_list.currentRow()
        if selected >= 0:
            del self.shapes[selected]
            self.update_shapes_list()

    def generate_input_file(self):
        try:
            content = f"""#title: {self.title_input.text()}
#domain: {self.domain_x.text()} {self.domain_y.text()} {self.domain_z.text()}
#dx_dy_dz: {self.dx.text()} {self.dy.text()} {self.dz.text()}
#time_window: {self.time_window.text()}

#material: 6 0 1 0 half_space

#waveform: {self.waveform_type.currentText()} {self.waveform_amp.text()} {self.waveform_freq.text()} {self.waveform_name.text()}
#hertzian_dipole: {self.hertz_orientation.text()} {self.hertz_x.text()} {self.hertz_y.text()} {self.hertz_z.text()} {self.waveform_name.text()}
#rx: {self.rx_x.text()} {self.rx_y.text()} {self.rx_z.text()}
#src_steps: {self.src_step_x.text()} {self.src_step_y.text()} {self.src_step_z.text()}
#rx_steps: {self.rx_step_x.text()} {self.rx_step_y.text()} {self.rx_step_z.text()}

#box: 0 0 0 {self.box_end_x.text()} {self.box_end_y.text()} {self.box_end_z.text()} half_space
"""

            # Add shapes info
            for shape in self.shapes:
                if shape['type'] == "Sphere":
                    # Format: #sphere: cx cy cz radius material
                    content += f"#sphere: {shape['center_x']} {shape['center_y']} {shape['center_z']} {shape['radius']} half_space\n"
                elif shape['type'] == "Cylinder":
                    # #cylinder: base_x base_y base_z radius height material
                    content += f"#cylinder: {shape['base_x']} {shape['base_y']} {shape['base_z']} {shape['radius']} {shape['height']} half_space\n"
                elif shape['type'] == "Block":
                    # #block: start_x start_y start_z end_x end_y end_z material
                    content += f"#block: {shape['start_x']} {shape['start_y']} {shape['start_z']} {shape['end_x']} {shape['end_y']} {shape['end_z']} half_space\n"
                elif shape['type'] == "Ellipsoid":
                    # #ellipsoid: cx cy cz radius_x radius_y radius_z material
                    content += f"#ellipsoid: {shape['center_x']} {shape['center_y']} {shape['center_z']} {shape['radius_x']} {shape['radius_y']} {shape['radius_z']} half_space\n"
                elif shape['type'] == "Cone":
                    # #cone: base_x base_y base_z base_radius height material
                    content += f"#cone: {shape['base_x']} {shape['base_y']} {shape['base_z']} {shape['base_radius']} {shape['height']} half_space\n"

            with open("gprmax_input.in", "w") as f:
                f.write(content)
            QMessageBox.information(self, "Success", "✅ Input file generated as 'gprmax_input.in'")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_styles(self):
        return """
        QWidget {
            background-color: #f3f6fc;
            font-family: Segoe UI, sans-serif;
            font-size: 14px;
        }
        QLineEdit, QComboBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #0078d7;
        }
        QLabel {
            font-weight: bold;
            color: #333;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            padding: 10px;
            font-weight: bold;
            border-radius: 5px;
            min-height: 28px;
        }
        QPushButton:hover {
            background-color: #005bb5;
        }
        QListWidget {
            border: 1px solid #ccc;
            border-radius: 4px;
            background: white;
        }
        QListWidget::item {
            padding: 6px;
        }
        QListWidget::item:selected {
            background-color: #0078d7;
            color: white;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GPRMaxInputGenerator()
    window.show()
    sys.exit(app.exec_())
