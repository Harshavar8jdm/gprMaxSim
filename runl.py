from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout, QMessageBox,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QFileDialog
)
from PyQt5.QtCore import Qt
import sys
import json

class ShapeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Shape")
        self.setStyleSheet(parent.load_styles())

        self.shape_type = QComboBox()
        self.shape_type.addItems(["Sphere", "Cylinder", "Block", "Ellipsoid", "Cone"])
        self.shape_type.currentTextChanged.connect(self.update_form)

        self.material_input = QLineEdit("half_space")

        self.form_layout = QFormLayout()
        self.param_widgets = {}

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("Select Shape Type:"))
        main_layout.addWidget(self.shape_type)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(QLabel("Material:"))
        main_layout.addWidget(self.material_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)
        self.update_form(self.shape_type.currentText())

    def clear_form(self):
        for label, widget in self.param_widgets.values():
            self.form_layout.removeWidget(label)
            self.form_layout.removeWidget(widget)
            label.deleteLater()
            widget.deleteLater()
        self.param_widgets.clear()

    def update_form(self, shape):
        self.clear_form()
        shape_params = {
            "Sphere": ["Center X", "Center Y", "Center Z", "Radius"],
            "Cylinder": ["Base X", "Base Y", "Base Z", "Radius", "Height"],
            "Block": ["Start X", "Start Y", "Start Z", "End X", "End Y", "End Z"],
            "Ellipsoid": ["Center X", "Center Y", "Center Z", "Radius X", "Radius Y", "Radius Z"],
            "Cone": ["Base X", "Base Y", "Base Z", "Base Radius", "Height"]
        }
        for param in shape_params[shape]:
            label = QLabel(f"{param}:")
            widget = QLineEdit()
            self.form_layout.addRow(label, widget)
            self.param_widgets[param] = (label, widget)

    def get_shape_data(self):
        shape = self.shape_type.currentText()
        data = {"type": shape, "material": self.material_input.text() or "half_space"}
        for param, (label, widget) in self.param_widgets.items():
            val = widget.text().strip() or "0"
            data[param.lower().replace(" ", "_")] = val
        return data


class GPRMaxInputGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gprMax Input File Generator")
        self.setGeometry(100, 100, 600, 850)
        self.setStyleSheet(self.load_styles())
        self.shapes = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)

        self.domain_x, self.domain_y, self.domain_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("Domain (x y z):", self._group(self.domain_x, self.domain_y, self.domain_z))

        self.dx, self.dy, self.dz = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("dx dy dz:", self._group(self.dx, self.dy, self.dz))

        self.time_window = QLineEdit()
        form.addRow("Time Window:", self.time_window)

        self.waveform_type = QComboBox()
        self.waveform_type.addItems([
            "ricker", "gaussian", "gaussiandot", "gaussiandotnorm",
            "gaussiandotdot", "gaussiandotdotnorm", "contsine"
        ])
        self.waveform_amp = QLineEdit()
        self.waveform_freq = QLineEdit()
        self.waveform_name = QLineEdit()
        form.addRow("Waveform Type:", self.waveform_type)
        form.addRow("Amplitude:", self.waveform_amp)
        form.addRow("Frequency (Hz):", self.waveform_freq)
        form.addRow("Waveform Name:", self.waveform_name)

        self.hertz_orientation = QLineEdit("z")
        self.hertz_x, self.hertz_y, self.hertz_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("Hertzian Dipole (x y z):", self._group(self.hertz_x, self.hertz_y, self.hertz_z))
        form.addRow("Orientation:", self.hertz_orientation)

        self.rx_x, self.rx_y, self.rx_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("Receiver Location (x y z):", self._group(self.rx_x, self.rx_y, self.rx_z))

        self.src_step_x, self.src_step_y, self.src_step_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("TX Steps (x y z):", self._group(self.src_step_x, self.src_step_y, self.src_step_z))

        self.rx_step_x, self.rx_step_y, self.rx_step_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("RX Steps (x y z):", self._group(self.rx_step_x, self.rx_step_y, self.rx_step_z))

        self.box_end_x, self.box_end_y, self.box_end_z = QLineEdit(), QLineEdit(), QLineEdit()
        form.addRow("Box End (x y z):", self._group(self.box_end_x, self.box_end_y, self.box_end_z))

        layout.addLayout(form)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Add Shapes:"))
        self.shapes_list = QListWidget()
        layout.addWidget(self.shapes_list)

        btns = QHBoxLayout()
        self.add_shape_btn = QPushButton("Add Shape")
        self.remove_shape_btn = QPushButton("Remove Selected")
        btns.addWidget(self.add_shape_btn)
        btns.addWidget(self.remove_shape_btn)
        layout.addLayout(btns)

        # New buttons
        new_btns = QHBoxLayout()
        self.reset_btn = QPushButton("Reset All Fields")
        self.save_as_btn = QPushButton("Save As")
        new_btns.addWidget(self.reset_btn)
        new_btns.addWidget(self.save_as_btn)
        layout.addLayout(new_btns)

        self.generate_btn = QPushButton("Generate gprMax Input File")
        layout.addWidget(self.generate_btn)

        self.add_shape_btn.clicked.connect(self.open_add_shape_dialog)
        self.remove_shape_btn.clicked.connect(self.remove_selected_shape)
        self.reset_btn.clicked.connect(self.reset_all_fields)
        self.save_as_btn.clicked.connect(self.generate_input_file_with_dialog)
        self.generate_btn.clicked.connect(self.generate_input_file)

        self.setLayout(layout)

    def _group(self, *widgets):
        box = QHBoxLayout()
        for w in widgets:
            box.addWidget(w)
        return box

    def open_add_shape_dialog(self):
        dialog = ShapeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.shapes.append(dialog.get_shape_data())
            self.update_shapes_list()

    def update_shapes_list(self):
        self.shapes_list.clear()
        for shape in self.shapes:
            desc = f"{shape['type']} [{shape['material']}]: " + ", ".join(
                f"{k.replace('_',' ').title()}={v}" for k,v in shape.items() if k not in ('type', 'material')
            )
            self.shapes_list.addItem(desc)

    def remove_selected_shape(self):
        index = self.shapes_list.currentRow()
        if index >= 0:
            del self.shapes[index]
            self.update_shapes_list()

    def reset_all_fields(self):
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        self.shapes.clear()
        self.update_shapes_list()

    def generate_input_file_with_dialog(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Input File", "gprmax_input.in", "Input Files (*.in)")
        if path:
            self.generate_input_file(path)

    def generate_input_file(self, path="gprmax_input.in"):
        try:
            lines = [
                f"#title: {self.title_input.text()}",
                f"#domain: {self.domain_x.text()} {self.domain_y.text()} {self.domain_z.text()}",
                f"#dx_dy_dz: {self.dx.text()} {self.dy.text()} {self.dz.text()}",
                f"#time_window: {self.time_window.text()}",
                "",
                "#material: 6 0 1 0 half_space",
                "",
                f"#waveform: {self.waveform_type.currentText()} {self.waveform_amp.text()} {self.waveform_freq.text()} {self.waveform_name.text()}",
                f"#hertzian_dipole: {self.hertz_orientation.text()} {self.hertz_x.text()} {self.hertz_y.text()} {self.hertz_z.text()} {self.waveform_name.text()}",
                f"#rx: {self.rx_x.text()} {self.rx_y.text()} {self.rx_z.text()}",
                f"#src_steps: {self.src_step_x.text()} {self.src_step_y.text()} {self.src_step_z.text()}",
                f"#rx_steps: {self.rx_step_x.text()} {self.rx_step_y.text()} {self.rx_step_z.text()}",
                f"#box: 0 0 0 {self.box_end_x.text()} {self.box_end_y.text()} {self.box_end_z.text()} half_space",
                ""
            ]

            for shape in self.shapes:
                material = shape.get("material", "half_space")
                t = shape['type']
                if t == "Sphere":
                    lines.append(f"#sphere: {shape['center_x']} {shape['center_y']} {shape['center_z']} {shape['radius']} {material}")
                elif t == "Cylinder":
                    lines.append(f"#cylinder: {shape['base_x']} {shape['base_y']} {shape['base_z']} {shape['radius']} {shape['height']} {material}")
                elif t == "Block":
                    lines.append(f"#block: {shape['start_x']} {shape['start_y']} {shape['start_z']} {shape['end_x']} {shape['end_y']} {shape['end_z']} {material}")
                elif t == "Ellipsoid":
                    lines.append(f"#ellipsoid: {shape['center_x']} {shape['center_y']} {shape['center_z']} {shape['radius_x']} {shape['radius_y']} {shape['radius_z']} {material}")
                elif t == "Cone":
                    lines.append(f"#cone: {shape['base_x']} {shape['base_y']} {shape['base_z']} {shape['base_radius']} {shape['height']} {material}")

            with open(path, "w") as f:
                f.write("\n".join(lines))

            QMessageBox.information(self, "Success", f"Input file saved as '{path}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def import_project_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Project", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.title_input.setText(data.get('title', ''))
                    self.domain_x.setText(data.get('domain', [''])[0])
                    self.domain_y.setText(data.get('domain', ['',''])[1])
                    self.domain_z.setText(data.get('domain', ['','',''])[2])
                    self.dx.setText(data.get('dx_dy_dz', [''])[0])
                    self.dy.setText(data.get('dx_dy_dz', ['',''])[1])
                    self.dz.setText(data.get('dx_dy_dz', ['','',''])[2])
                    self.time_window.setText(data.get('time_window', ''))
                    wf = data.get('waveform', {})
                    self.waveform_type.setCurrentText(wf.get('type', 'ricker'))
                    self.waveform_amp.setText(wf.get('amp', ''))
                    self.waveform_freq.setText(wf.get('freq', ''))
                    self.waveform_name.setText(wf.get('name', ''))
                    dip = data.get('dipole', {})
                    self.hertz_orientation.setText(dip.get('orientation', 'z'))
                    self.hertz_x.setText(dip.get('x', ''))
                    self.hertz_y.setText(dip.get('y', ''))
                    self.hertz_z.setText(dip.get('z', ''))
                    rx = data.get('rx', ['','',''])
                    self.rx_x.setText(rx[0])
                    self.rx_y.setText(rx[1])
                    self.rx_z.setText(rx[2])
                    src = data.get('src_steps', ['','',''])
                    self.src_step_x.setText(src[0])
                    self.src_step_y.setText(src[1])
                    self.src_step_z.setText(src[2])
                    rxs = data.get('rx_steps', ['','',''])
                    self.rx_step_x.setText(rxs[0])
                    self.rx_step_y.setText(rxs[1])
                    self.rx_step_z.setText(rxs[2])
                    box = data.get('box_end', ['','',''])
                    self.box_end_x.setText(box[0])
                    self.box_end_y.setText(box[1])
                    self.box_end_z.setText(box[2])
                    self.shapes = data.get('shapes', [])
                    self.update_shapes_list()
                    QMessageBox.information(self, "Success", "Project loaded from JSON")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_project_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Project", "project.json", "JSON Files (*.json)")
        if path:
            try:
                data = {
                    'title': self.title_input.text(),
                    'domain': [self.domain_x.text(), self.domain_y.text(), self.domain_z.text()],
                    'dx_dy_dz': [self.dx.text(), self.dy.text(), self.dz.text()],
                    'time_window': self.time_window.text(),
                    'waveform': {
                        'type': self.waveform_type.currentText(),
                        'amp': self.waveform_amp.text(),
                        'freq': self.waveform_freq.text(),
                        'name': self.waveform_name.text(),
                    },
                    'dipole': {
                        'orientation': self.hertz_orientation.text(),
                        'x': self.hertz_x.text(),
                        'y': self.hertz_y.text(),
                        'z': self.hertz_z.text(),
                    },
                    'rx': [self.rx_x.text(), self.rx_y.text(), self.rx_z.text()],
                    'src_steps': [self.src_step_x.text(), self.src_step_y.text(), self.src_step_z.text()],
                    'rx_steps': [self.rx_step_x.text(), self.rx_step_y.text(), self.rx_step_z.text()],
                    'box_end': [self.box_end_x.text(), self.box_end_y.text(), self.box_end_z.text()],
                    'shapes': self.shapes
                }
                with open(path, 'w') as f:
                    json.dump(data, f, indent=4)
                QMessageBox.information(self, "Success", f"Project saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


    def load_styles(self):
        return """
        QWidget {
            background-color: #f8f9fb;
            font-family: Segoe UI, sans-serif;
            font-size: 14px;
        }
        QLabel {
            font-weight: bold;
            color: #222;
        }
        QLineEdit, QComboBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #fff;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            font-weight: bold;
            padding: 8px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #005ea6;
        }
        QListWidget {
            border: 1px solid #ccc;
            border-radius: 4px;
            background: white;
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
