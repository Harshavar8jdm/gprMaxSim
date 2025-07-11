import sys
import os
import subprocess
import threading
import re
import shutil
import time 
from de.runl import GPRMaxInputGenerator
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QPlainTextEdit, QTabWidget, QAction, QInputDialog, QVBoxLayout, QWidget,
    QToolBar, QSplitter, QFileSystemModel, QTreeView, QLineEdit, QLabel, QHBoxLayout,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QPushButton, QCheckBox, QMenu, QAbstractItemView,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QDir, QObject, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class FileTab(QWidget):
    def __init__(self, filepath=None):
        super().__init__()
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))

        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)

        self.filepath = filepath
        if filepath:
            try:
                # Try reading as text
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.editor.setPlainText(text)

                # Apply syntax highlighting only for .in files
                if filepath.endswith(".in"):
                    self.highlighter = GPRMaxHighlighter(self.editor.document())

            except UnicodeDecodeError:
                QMessageBox.warning(self, "Unsupported File",
                                    f"Cannot open binary file:\n{filepath}")
                self.editor.setPlainText("[Binary or unsupported file — cannot display]")
                self.editor.setReadOnly(True)

        self.editor.textChanged.connect(self.update_tab_title)

    def is_modified(self):
        return self.editor.document().isModified()

    def set_saved(self):
        self.editor.document().setModified(False)

    def update_tab_title(self):
        parent = self.parentWidget()
        while parent and not isinstance(parent, QTabWidget):
            parent = parent.parentWidget()
        if parent:
            index = parent.indexOf(self)
            name = os.path.basename(self.filepath) if self.filepath else "Untitled"
            if self.is_modified():
                name = "● " + name
            parent.setTabText(index, name)

class MaterialLibraryDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Material Property Library")
        self.setFixedSize(600, 400)

        self.materials = [
            ("Air", 1.0, 0.0, 3e8),
            ("Dry Sand", 4.0, 0.001, 1.5e8),
            ("Wet Soil", 15.0, 0.01, 7.75e7),
            ("Fresh Water", 80.0, 0.01, 3.35e7),
            ("Concrete", 6.0, 0.001, 1.22e8),
            ("Ice", 3.2, 0.0005, 1.68e8)
        ]

        self.table = QTableWidget()
        self.table.setRowCount(len(self.materials))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Material", "εr", "Conductivity (S/m)", "Velocity (m/s)"])

        for i, (name, er, cond, vel) in enumerate(self.materials):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(str(er)))
            self.table.setItem(i, 2, QTableWidgetItem(str(cond)))
            self.table.setItem(i, 3, QTableWidgetItem(f"{vel:.2e}"))

        self.use_button = QPushButton("Use Selected")
        self.use_button.clicked.connect(self.use_selected_material)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.use_button)
        button_layout.addWidget(close_button)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.selected_velocity = None

    def use_selected_material(self):
        selected = self.table.currentRow()
        if selected >= 0:
            vel_item = self.table.item(selected, 3)
            if vel_item:
                self.selected_velocity = vel_item.text()
                self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a material.")

class WaveformVisualizerDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Waveform Visualizer")
        self.setFixedSize(720, 520)

        self.waveform_type = QComboBox()
        self.waveform_type.addItems([
            "ricker", "gaussiandot", "gaussiandotnorm",
            "gaussiandotdot", "gaussiandotdotnorm",
            "sine", "contsine"
        ])
        self.freq_input = QLineEdit("100e6")
        self.window_input = QLineEdit("10e-9")
        self.peak_input = QLineEdit("5e-9")

        form = QFormLayout()
        form.addRow("Waveform Type:", self.waveform_type)
        form.addRow("Central Frequency (Hz):", self.freq_input)
        form.addRow("Time Window (s):", self.window_input)
        form.addRow("Peak Time (s):", self.peak_input)

        plot_btn = QPushButton("Plot Waveform")
        plot_btn.clicked.connect(self.plot_waveform)

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax_time = self.canvas.figure.add_subplot(211)
        self.ax_freq = self.canvas.figure.add_subplot(212)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(plot_btn)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def plot_waveform(self):
        try:
            f = float(self.freq_input.text())
            t_max = float(self.window_input.text())
            t0 = float(self.peak_input.text())
            waveform = self.waveform_type.currentText()

            t = np.linspace(0, t_max, 1000)
            arg = 2 * np.pi * f * (t - t0)

            if waveform == "ricker":
                y = (1 - 2 * (np.pi * f * (t - t0)) ** 2) * np.exp(-(np.pi * f * (t - t0)) ** 2)
            elif waveform == "gaussiandot":
                y = -arg * np.exp(-arg**2)
            elif waveform == "gaussiandotnorm":
                y = -2 * arg * np.exp(-arg**2)
            elif waveform == "gaussiandotdot":
                y = (2 * arg**2 - 1) * np.exp(-arg**2)
            elif waveform == "gaussiandotdotnorm":
                y = 4 * (arg**2 - 0.5) * np.exp(-arg**2)
            elif waveform == "sine":
                y = np.sin(arg)
            elif waveform == "contsine":
                y = np.sin(arg) * np.exp(-((t - t0)**2) / (2 * (1 / (2 * np.pi * f))**2))
            else:
                y = np.zeros_like(t)

            self.ax_time.clear()
            self.ax_time.plot(t * 1e9, y, label="Time Domain")
            self.ax_time.set_title("Time Domain (ns)")
            self.ax_time.set_xlabel("Time (ns)")
            self.ax_time.set_ylabel("Amplitude")

            self.ax_freq.clear()
            Y = np.abs(np.fft.fft(y))
            freq = np.fft.fftfreq(len(t), d=t[1] - t[0])
            self.ax_freq.plot(freq[freq > 0] * 1e-6, Y[freq > 0])
            self.ax_freq.set_title("Frequency Domain (MHz)")
            self.ax_freq.set_xlabel("Frequency (MHz)")
            self.ax_freq.set_ylabel("Magnitude")

            self.canvas.draw()
        except Exception as e:
            print(f"Error in plotting: {e}")


class GPRMaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rules = []

        # Format for keywords (GPRMax directives)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#007acc"))
        keyword_format.setFontWeight(QFont.Bold)


        # List of GPRMax directives to highlight
        keywords = [
            "#title", "#domain", "#dx_dy_dz", "#time_window", "#pml_cells",
            "#material", "#waveform", "#hertzian_dipole", "#rx",
            "#geometry_view", "#box", "#cylinder", "#sphere", "#include",
            "#outputfile", "#src_steps", "rx_steps", "#python", "#end_python", "#triangle",
            "#cylindrical_sector", "#snapshot", "geometry_only", "#bowtie", "#wire", 
            "#elec_probe", "#mag_probe", "#dump_fields", "#material_debye", "#material_drude",
            "#material_lorentz", "#include_file", "#restart", "#time_step_stability_factor", "#messages",
            "#output_dir", "#num_threads", "#add_dispersion_debye", "#add_dispersion_lorentz", 
            "#add_dispersion_drude", "#soil_peplinski", "#geometry_view", "#edge", "#plate", "#triangle",
            "#fractal_box", "#add_surface_roughness", "#add_surface_water", "#add_grass", "#geometry_objects_read",
            "#geometry_objects_write", "#excitation_file", "#magnetic_dipole", "#voltage_source", "#transmission_line",
            "#rx_array", "#pml_formulation", "#pml_cfs" 

        ]

        constants = ["c", "e0", "m0", "z0", "current_model_run", "inputfile", "number_model_runs"]



        for word in keywords:
            pattern = re.compile(re.escape(word))  
            self.highlight_rules.append((pattern, keyword_format))

        # Comments (everything after a semicolon)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("green"))
        comment_pattern = re.compile(r";[^\n]*")
        self.highlight_rules.append((comment_pattern, comment_format))

        # --- Constant format --
        constant_format = QTextCharFormat()
       # constant_format.setForeground(QColor("#d19a66"))
        constant_format.setFontWeight(QFont.Bold)
        constant_format.setForeground(QColor("#c678dd"))  # Soft purple
        constant_format.setFontItalic(True)

        for const in constants:
            pattern = re.compile(rf"\b{re.escape(const)}\b")
            self.highlight_rules.append((pattern, constant_format))


    def highlightBlock(self, text):
        for pattern, fmt in self.highlight_rules:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, fmt)    

class ImageTab(QWidget):
    def __init__(self, filepath):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel()
        pixmap = QPixmap(filepath)

        if pixmap.isNull():
            label.setText("Failed to load image.")
        else:
            # Scale image to fit the viewer size
            label.setPixmap(pixmap.scaled(1000, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)
    
class CommandRunner(QObject):
    output_received = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, universal_newlines=True)
            for line in iter(process.stdout.readline, ''):
                self.output_received.emit(line.rstrip())
            process.stdout.close()
            process.wait()
        except Exception as e:
            self.output_received.emit(f"[Exception] {str(e)}")

class RunDialog(QDialog):
    def __init__(self, default_n=1):
        super().__init__()
        self.setWindowTitle("Run Simulation")
        self.setFixedSize(400, 270)

        layout = QFormLayout(self)

        # File input and browse
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("e.g., simulation_model.in")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_button)
        layout.addRow("Input .in File:", file_layout)

        self.n_input = QLineEdit(str(default_n))
        self.n_input.setPlaceholderText("e.g., 1")
        layout.addRow("Number of models (-n):", self.n_input)

        self.gpu_dropdown = QComboBox()
        self.gpu_dropdown.addItems(["No", "Yes"])
        self.gpu_dropdown.setCurrentText("No")
        layout.addRow("Use GPU:", self.gpu_dropdown)

        self.mpi_checkbox = QCheckBox("Enable MPI")
        self.mpi_checkbox.stateChanged.connect(self.toggle_mpi_inputs)
        layout.addRow("", self.mpi_checkbox)

        self.mpi_process_input = QLineEdit()
        self.mpi_process_input.setPlaceholderText("e.g., 61")
        self.mpi_process_input.setEnabled(False)
        layout.addRow("MPI Processes:", self.mpi_process_input)

        self.no_spawn_checkbox = QCheckBox("Use --mpi-no-spawn")
        self.no_spawn_checkbox.setEnabled(False)
        layout.addRow("", self.no_spawn_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def toggle_mpi_inputs(self, state):
        enabled = (state == Qt.Checked)
        self.mpi_process_input.setEnabled(enabled)
        self.no_spawn_checkbox.setEnabled(enabled)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .in File", "", "Input Files (*.in)")
        if path:
            self.file_input.setText(path)

    def get_inputs(self):
        return (
            self.file_input.text().strip(),
            self.n_input.text().strip(),
            self.gpu_dropdown.currentText().strip(),
            self.mpi_checkbox.isChecked(),
            self.mpi_process_input.text().strip(),
            self.no_spawn_checkbox.isChecked()
        )



class PlotBScanDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot B-scan")
        self.setFixedSize(400, 280)

        layout = QFormLayout(self)

        # File input with browse button
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("e.g., cylinder_Bscan_2D_merged.out")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        layout.addRow("Select .out File:", file_layout)

        self.component_input = QLineEdit()
        self.component_input.setPlaceholderText("e.g., Ex, Ez, Hy")
        layout.addRow("Field component:", self.component_input)

        self.cmap_dropdown = QComboBox()
        self.cmap_dropdown.addItems([
            "seismic", "gray", "viridis", "plasma", "inferno", "magma",
            "cividis", "coolwarm", "bwr", "Greys", "hot", "twilight", "turbo"
        ])
        self.cmap_dropdown.setCurrentText("seismic")
        layout.addRow("Colormap:", self.cmap_dropdown)

        self.vel_input = QLineEdit()
        self.vel_input.setPlaceholderText("e.g., 1.22e8")

        calc_vel_btn = QPushButton("Calc")
        calc_vel_btn.setFixedWidth(50)
        calc_vel_btn.clicked.connect(self.open_velocity_calculator)

        vel_layout = QHBoxLayout()
        vel_layout.addWidget(self.vel_input)
        vel_layout.addWidget(calc_vel_btn)

        layout.addRow("Velocity (m/s):", vel_layout)

        library_button = QPushButton("Library")
        library_button.setFixedWidth(60)
        library_button.clicked.connect(self.open_material_library)

        vel_layout = QHBoxLayout()
        vel_layout.addWidget(self.vel_input)
        vel_layout.addWidget(library_button)
        layout.addRow("Velocity (m/s):", vel_layout)


        self.dpi_input = QLineEdit()
        self.dpi_input.setPlaceholderText("e.g., 150 (optional)")
        layout.addRow("Plot DPI:", self.dpi_input)

        #Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .out File", "", "Output Files (*.out)")
        if path:
            self.file_input.setText(path)

    def get_inputs(self):
        return (
            self.file_input.text().strip(),
            self.component_input.text().strip(),
            self.cmap_dropdown.currentText().strip(),
            self.dpi_input.text().strip(),
            self.vel_input.text().strip()  
        )
    
    def open_velocity_calculator(self):
        presets = {
            "Air (εr ≈ 1)": 1.0,
            "Dry Sand (εr ≈ 4)": 4.0,
            "Wet Soil (εr ≈ 15)": 15.0,
            "Concrete (εr ≈ 6)": 6.0,
            "Fresh Water (εr ≈ 80)": 80.0,
            "Custom...": None
        }

        items = list(presets.keys())
        choice, ok = QInputDialog.getItem(
            self, "Select Material", "Choose a material:", items, 0, False
        )

        if ok:
            if presets[choice] is not None:
                eps = presets[choice]
            else:
                eps, eps_ok = QInputDialog.getDouble(
                    self, "Enter εr", "Relative Permittivity:", min=1.0, decimals=4
                )
                if not eps_ok:
                    return
            # Compute velocity
            c = 3e8  # m/s
            v = c / (eps ** 0.5)
            self.vel_input.setText(f"{v:.4e}")
    
    def open_material_library(self):
        dlg = MaterialLibraryDialog()
        if dlg.exec_() == QDialog.Accepted and dlg.selected_velocity:
            self.vel_input.setText(dlg.selected_velocity)



class PlotAScanDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot A-scan")
        self.setFixedSize(400, 260)

        layout = QFormLayout(self)

        # File input with Browse button
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("e.g., cylinder_Bscan_2D_merged.out")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_input)
        file_row.addWidget(browse_btn)
        layout.addRow("Select .out File:", file_row)

        # Colormap
        self.cmap_dropdown = QComboBox()
        self.cmap_dropdown.addItems([
            "seismic", "gray", "viridis", "plasma", "inferno", "magma",
            "cividis", "coolwarm", "bwr", "Greys", "hot", "twilight", "turbo"
        ])
        self.cmap_dropdown.setCurrentText("seismic")
        layout.addRow("Colormap:", self.cmap_dropdown)

        # Velocity (required)
        self.vel_input = QLineEdit()
        self.vel_input.setPlaceholderText("e.g., 1.22e8")

        calc_vel_btn = QPushButton("Calc")
        calc_vel_btn.setFixedWidth(50)
        calc_vel_btn.clicked.connect(self.open_velocity_calculator)
        # Velocity (required)
        
        self.vel_input = QLineEdit()
        self.vel_input.setPlaceholderText("e.g., 1.22e8")
        
        calc_vel_btn = QPushButton("Calc")
        calc_vel_btn.setFixedWidth(50)
        calc_vel_btn.clicked.connect(self.open_velocity_calculator)
        
        library_button = QPushButton("Library")  # 🔁 move this up
        library_button.setFixedWidth(60)
        library_button.clicked.connect(self.open_material_library)
        
        vel_layout = QHBoxLayout()
        vel_layout.addWidget(self.vel_input)
        vel_layout.addWidget(calc_vel_btn)
        vel_layout.addWidget(library_button)
        
        layout.addRow("Velocity (m/s):", vel_layout)



        # DPI (optional)
        self.dpi_input = QLineEdit()
        self.dpi_input.setPlaceholderText("e.g., 150 (optional)")
        layout.addRow("Plot DPI:", self.dpi_input)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        # Align buttons to bottom-right
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # pushes buttons to the right
        button_layout.addWidget(buttons)
        layout.addRow(button_layout)


        self.setLayout(layout)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .out File", "", "Output Files (*.out)")
        if path:
            self.file_input.setText(path)

    def get_inputs(self):
        return (
            self.file_input.text().strip(),
            self.cmap_dropdown.currentText().strip(),
            self.dpi_input.text().strip(),
            self.vel_input.text().strip(),
        )
    
    def open_velocity_calculator(self):
        eps, ok = QInputDialog.getDouble(
            self, "Calculate Wave Velocity", "Enter Relative Permittivity (εr):", min=1.0, decimals=4
        )

        if ok and eps > 0:
            c = 3e8  # speed of light in vacuum
            v = c / (eps ** 0.5)
            self.vel_input.setText(f"{v:.4e}")

    def open_material_library(self):
        dlg = MaterialLibraryDialog()
        if dlg.exec_() == QDialog.Accepted and dlg.selected_velocity:
            self.vel_input.setText(dlg.selected_velocity)


   
class PNGtoH5Dialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convert PNG to HDF5")
        self.setFixedSize(400, 200)

        layout = QFormLayout(self)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("e.g., C:/path/to/image.png")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        layout.addRow("PNG Image File:", file_layout)

        self.dx_input = QLineEdit()
        self.dx_input.setPlaceholderText("e.g., 0.002")
        self.dy_input = QLineEdit()
        self.dy_input.setPlaceholderText("e.g., 0.002")
        self.dz_input = QLineEdit()
        self.dz_input.setPlaceholderText("e.g., 0.002")
        layout.addRow("dx dy dz:", self.dx_input)
        layout.addWidget(self.dy_input)
        layout.addWidget(self.dz_input)

        self.zcells_input = QLineEdit()
        self.zcells_input.setPlaceholderText("Optional, e.g., 150")
        layout.addRow("Z-cells (optional):", self.zcells_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PNG", "", "PNG Images (*.png)")
        if path:
            self.file_input.setText(path)

    def get_inputs(self):
        return (
            self.file_input.text().strip(),
            self.dx_input.text().strip(),
            self.dy_input.text().strip(),
            self.dz_input.text().strip(),
            self.zcells_input.text().strip()
        )

class MergeOutputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merge Output Files")
        self.setFixedSize(400, 160)

        layout = QFormLayout(self)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("e.g., file (for file1.out, file2.out, ...)")
        layout.addRow("Base name:", self.file_input)

        self.remove_checkbox = QCheckBox("Remove original .out files after merging")
        layout.addRow("", self.remove_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def accept(self):
        base = self.file_input.text().strip()
        if not base:
            QMessageBox.warning(self, "Missing Input", "Please enter a base name for the output files.")
            return
        super().accept()

    def get_inputs(self):
        return (
            self.file_input.text().strip(),
            self.remove_checkbox.isChecked()
        )

        
class GPRViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gprStudio")
        self.setWindowIcon(QIcon("C:/Users/Harsha/gprMax/pyqt5gui/gprmax_app.png"))
        self.setGeometry(100, 100, 1200, 800)
        self.n_models = 1
        self.current_dir = QDir.currentPath()
        
        
        self.model = QFileSystemModel()
        self.model.setRootPath(self.current_dir)
        self.model.setNameFilters([])
        self.model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.current_dir))
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.doubleClicked.connect(self.load_file_from_explorer)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.clipboard_action = None
        self.clipboard_path = None
        self.tree.setDragDropMode(QAbstractItemView.DropOnly)
        self.setAcceptDrops(True)



        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        
        self.shell_output = QPlainTextEdit()
        self.shell_output.setReadOnly(True)
        self.shell_output.setFont(QFont("Consolas", 11))
        self.shell_output.setStyleSheet("background-color: black; color: lime;")

        self.shell_input = QLineEdit()
        self.shell_input.setPlaceholderText("Type shell command (PowerShell/CMD)...")
        self.shell_input.returnPressed.connect(self.execute_shell_command)

        self.shell_panel = QWidget()
        shell_layout = QVBoxLayout()
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.addWidget(self.shell_output)
        shell_layout.addWidget(self.shell_input)
        self.shell_panel.setLayout(shell_layout)

        editor_shell_splitter = QSplitter(Qt.Vertical)
        editor_shell_splitter.addWidget(self.tabs)
        editor_shell_splitter.addWidget(self.shell_panel)
        editor_shell_splitter.setSizes([600, 200])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.tree)
        main_splitter.addWidget(editor_shell_splitter)
        main_splitter.setSizes([250, 950])

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.create_actions()
        self.create_menu()
        self.create_toolbar()
        self.add_welcome_tab()
        self.apply_styles()

        self.wizard_action = QAction("Create Model (Wizard)", self)
        self.wizard_action.triggered.connect(self.GPRMaxInputGeneratorWizard)


    def create_actions(self):
        self.open_action = QAction("Open File", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)

        self.open_folder_action = QAction("Open Folder", self)
        self.open_folder_action.setShortcut("Ctrl+Shift+O")
        self.open_folder_action.triggered.connect(self.open_folder)

        self.save_action = QAction("Save As", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)

        self.run_action = QAction("Run", self)
        self.run_action.setShortcut("Ctrl+R")
        self.run_action.triggered.connect(self.run_current_file)

        self.set_n_action = QAction("Set -n", self)
        self.set_n_action.triggered.connect(self.set_n_models)

        self.merge_action = QAction("Merge Outputs", self)
        self.merge_action.triggered.connect(self.merge_output_files)

        self.plot_bscan_action = QAction("Plot B-scan", self)
        self.plot_bscan_action.triggered.connect(self.plot_bscan_file)

        self.new_file_action = QAction("New File", self)
        self.new_file_action.setShortcut("Ctrl+N")
        self.new_file_action.triggered.connect(self.add_blank_tab)  

        self.wizard_action = QAction("Create Model (Wizard)", self)
        self.wizard_action.triggered.connect(self.GPRMaxInputGeneratorWizard)

        self.ascan_action = QAction("Plot A-scan", self)
        self.ascan_action.triggered.connect(self.plot_ascan_file)

        self.convert_png_action = QAction("PNG to HDF5", self)
        self.convert_png_action.triggered.connect(self.convert_png_to_h5)

    def cut_file(self, path):
        self.clipboard_action = 'cut'
        self.clipboard_path = path

    def copy_file(self, path):
        self.clipboard_action = 'copy'
        self.clipboard_path = path

    def paste_file(self, destination_path):
        if not self.clipboard_path:
            return

        if os.path.isfile(destination_path):
            destination_path = os.path.dirname(destination_path)

        target = os.path.join(destination_path, os.path.basename(self.clipboard_path))

        try:
            if self.clipboard_action == 'copy':
                if os.path.isdir(self.clipboard_path):
                    shutil.copytree(self.clipboard_path, target)
                else:
                    shutil.copy2(self.clipboard_path, target)
            elif self.clipboard_action == 'cut':
                shutil.move(self.clipboard_path, target)
                self.clipboard_path = None
        except Exception as e:
            QMessageBox.critical(self, "Paste Error", str(e))

    def rename_file(self, path):
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=os.path.basename(path))
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            os.rename(path, new_path)

    def delete_file(self, path):
        confirm = QMessageBox.question(self, "Delete", f"Are you sure you want to delete '{os.path.basename(path)}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", str(e))
    
    
    def show_tree_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        file_path = self.model.filePath(index)

        menu = QMenu()

        # Actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.load_file_from_explorer(index))

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.cut_file(file_path))

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.copy_file(file_path))

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.paste_file(file_path))

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.rename_file(file_path))

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_file(file_path))

        # Add actions
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(cut_action)
        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith((".in", ".out", ".txt")):
                self.open_file_in_tab(file_path)

    def open_file_in_tab(self, file_path):
        for i in range(self.tabs.count()):
            if hasattr(self.tabs.widget(i), "filepath") and self.tabs.widget(i).filepath == file_path:
                self.tabs.setCurrentIndex(i)
                return

        file_tab = FileTab(file_path)
        self.tabs.addTab(file_tab, os.path.basename(file_path))
        self.tabs.setCurrentWidget(file_tab)

    def create_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.open_folder_action)
        file_menu.addAction(self.save_action)

        # Run menu
        run_menu = menubar.addMenu("Run")
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.set_n_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.merge_action)
        tools_menu.addAction(self.plot_bscan_action)

        # Add dark mode toggle to Tools
        toggle_theme_action = QAction("Toggle Dark Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_dark_mode)
        tools_menu.addAction(toggle_theme_action)

        # GPRPy menu
        gprpy_menu = menubar.addMenu("GPRPy")
        gprpy_action = QAction("Launch GPRPy App", self)
        gprpy_action.triggered.connect(self.launch_gprpy_app)
        gprpy_menu.addAction(gprpy_action)

        waveform_action = QAction("Waveform Visualizer", self)
        waveform_action.triggered.connect(self.open_waveform_dialog)
        tools_menu.addAction(waveform_action)
    
    def open_waveform_dialog(self):
        dlg = WaveformVisualizerDialog()
        dlg.exec_()


    def launch_gprpy_app(self):
        try:
            subprocess.Popen(["python", "-m", "gprpy", "p"], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch GPRPy app:\n{e}")

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_file_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.open_folder_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.set_n_action)
        toolbar.addAction(self.merge_action)
        toolbar.addAction(self.ascan_action)
        toolbar.addAction(self.plot_bscan_action)
        toolbar.addAction(self.wizard_action)
        toolbar.addAction(self.convert_png_action)

    def add_welcome_tab(self):
        welcome_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        timestamp = int(time.time())
        logo_filename = "gogo_dark.png" if getattr(self, "dark_mode", False) else "gogo.png"
        logo_path = f"{logo_filename}?v={timestamp}"

        message = QLabel()
        message.setTextFormat(Qt.RichText)
        message.setTextInteractionFlags(Qt.NoTextInteraction)
        message.setAlignment(Qt.AlignCenter)
        message.setText(f"""
            <div style="text-align: center; padding-top: 30px;">
                <img src="{logo_path}" alt="gprStudio Logo" width="100" style="margin-bottom: 20px;" />
                <h1 style="color: #0078d4; font-weight: bold; font-size: 24px; margin-bottom: 8px;">
                    gprStudio
                </h1>
                <p style="font-size: 13px;">
                    The professional IDE for GPRMax simulation projects.
                </p>
                <p style="font-size: 12px;">
                    Streamline your modeling, visualize results, and automate your workflow — all in one place.
                </p>
                <p style="font-size: 11px; margin-top: 20px;">
                    Built with ❤️ using PyQt5 · Developed by Harsha
                </p>
            </div>
        """)
        message.setAlignment(Qt.AlignCenter)

        
        gprmax_logo = QLabel()
        gprmax_pixmap = QPixmap("C:/Users/Harsha/gprMax/pyqt5gui/gprmax_app.png")
        gprmax_pixmap = gprmax_pixmap.scaled(140, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        gprmax_logo.setPixmap(gprmax_pixmap)
        gprmax_logo.setAlignment(Qt.AlignLeft)

       
        iit_logo = QLabel()
        iit_pixmap = QPixmap("C:/Users/Harsha/gprMax/pyqt5gui/Logo.png")
        iit_pixmap = iit_pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        iit_logo.setPixmap(iit_pixmap)
        iit_logo.setAlignment(Qt.AlignRight)

       
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(gprmax_logo, alignment=Qt.AlignLeft | Qt.AlignBottom)
        bottom_layout.addStretch()
        bottom_layout.addWidget(iit_logo, alignment=Qt.AlignRight | Qt.AlignBottom)

        
        layout.addStretch()
        layout.addWidget(message)
        layout.addStretch()
        layout.addLayout(bottom_layout)

        welcome_widget.setLayout(layout)
        self.tabs.addTab(welcome_widget, "Welcome")
    
    def refresh_welcome_tab(self):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Welcome":
                self.tabs.removeTab(i)
                break
        self.add_welcome_tab()


    def add_blank_tab(self):
        tab = FileTab()
        self.tabs.addTab(tab, "Untitled")
        self.tabs.setCurrentWidget(tab)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if path:
            tab = FileTab(path)
            self.tabs.addTab(tab, os.path.basename(path))
            self.tabs.setCurrentWidget(tab)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", self.current_dir)
        if folder_path:
            self.current_dir = folder_path
            self.model.setRootPath(folder_path)
            self.tree.setRootIndex(self.model.index(folder_path))
            self.shell_output.appendPlainText(f"[Info] Folder opened: {folder_path}")

    def save_file(self):
        current_tab = self.tabs.currentWidget()
        if current_tab:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*.*)")
            if path:
                with open(path, 'w') as f:
                    f.write(current_tab.editor.toPlainText())
                current_tab.filepath = path
                current_tab.set_saved()
                index = self.tabs.currentIndex()
                self.tabs.setTabText(index, os.path.basename(path))
                QMessageBox.information(self, "Saved", f"File saved at:\n{path}")

    def close_tab(self, index):
        tab = self.tabs.widget(index)
        if isinstance(tab, FileTab) and tab.is_modified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "This file has unsaved changes. Do you want to save it?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.tabs.setCurrentIndex(index)
                self.save_file()
        self.tabs.removeTab(index)

    def set_n_models(self):
        n, ok = QInputDialog.getInt(self, "Set -n", "Number of models (-n):", min=1, value=self.n_models)
        if ok:
            self.n_models = n

    def run_current_file(self):
        dialog = RunDialog(default_n=self.n_models)
        if dialog.exec_() == QDialog.Accepted:
            in_file, n_models, gpu, use_mpi, mpi_processes, no_spawn = dialog.get_inputs()

            if not os.path.isfile(in_file):
                QMessageBox.warning(self, "Invalid Input", "Please select a valid .in file.")
                return

            if not n_models.isdigit():
                QMessageBox.warning(self, "Invalid Input", "Number of models must be an integer.")
                return

            self.n_models = int(n_models)
            cmd = f"python -m gprMax \"{in_file}\" -n {self.n_models}"

            if gpu == "Yes":
                cmd += " --gpu"

            if use_mpi:
                if no_spawn:
                    cmd += " --mpi-no-spawn"
                else:
                    if not mpi_processes.isdigit():
                        QMessageBox.warning(self, "Invalid Input", "MPI processes must be an integer.")
                        return
                    cmd += f" -mpi {mpi_processes}"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)


    def merge_output_files(self):
        dialog = MergeOutputDialog()
        if dialog.exec_() == QDialog.Accepted:
            base_name, remove_flag = dialog.get_inputs()

            if not base_name:
                QMessageBox.warning(self, "Missing Base Name", "Please enter a valid base name.")
                return

            cmd = f"python -m tools.outputfiles_merge {base_name}"
            if remove_flag:
                cmd += " --remove-files"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)


        

    def plot_ascan_file(self):
       
        dialog = PlotAScanDialog()
        if dialog.exec_() == QDialog.Accepted:
            filename, cmap, velocity, dpi, gpu = dialog.get_inputs()

            if not filename:
                QMessageBox.warning(self, "Missing filename", "Please enter a filename.")
                return
            if not filename.endswith(".out"):
                filename += ".out"
            if not velocity:
                QMessageBox.warning(self, "Missing velocity", "Please enter wave velocity.")
                return

            cmd = f"python -m tools.plot_Ascan {filename} --velocity {velocity}"
            if cmap:
                cmd += f" --cmap {cmap}"
            if dpi and dpi.isdigit():
                cmd += f" --dpi {dpi}"
            if gpu.lower() == "yes":
                cmd += " --gpu"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)

        

    def plot_bscan_file(self):
        dialog = PlotBScanDialog()
        if dialog.exec_() == QDialog.Accepted:
            filename, components, cmap, dpi, velocity= dialog.get_inputs()

            if not filename:
                QMessageBox.warning(self, "Missing filename", "Please enter a filename.")
                return

            if not filename.endswith(".out"):
                filename += ".out"

            cmd = f"python -m tools.plot_Bscan {filename}"

            if components:
                cmd += " " + components
            if cmap:
                cmd += f" --cmap {cmap}"
            if velocity:  # velocity is required
                cmd += f" --velocity {velocity}"
            else:
                QMessageBox.warning(self, "Missing velocity", "You must enter wave velocity.")
                return
            if dpi and dpi.isdigit():
                cmd += f" --dpi {dpi}"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)

    def execute_shell_command(self):
        cmd = self.shell_input.text().strip()
        if not cmd:
            return
        self.shell_output.appendPlainText(f"> {cmd}")
        self.run_command(cmd)
        self.shell_input.clear()

    def run_command(self, cmd):
        self.runner = CommandRunner(cmd)
        self.runner.output_received.connect(self.shell_output.appendPlainText)
        thread = threading.Thread(target=self.runner.run)
        thread.start()

    def load_file_from_explorer(self, index):
        path = self.model.filePath(index)
        if not os.path.isfile(path):
            return

        ext = os.path.splitext(path)[1].lower()

        # Route image files to ImageTab
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            tab = ImageTab(path)
        # Route .in files to FileTab with syntax highlighting
        elif ext == '.in':
            tab = FileTab(path)
        # Try to load other text files safely
        else:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    f.read()
                tab = FileTab(path)
            except Exception:
                QMessageBox.warning(self, "Unsupported File",
                                    f"Cannot open binary or unsupported file:\n{path}")
                return

        self.tabs.addTab(tab, os.path.basename(path))
        self.tabs.setCurrentWidget(tab)

    def GPRMaxInputGeneratorWizard(self):
        wizard = GPRMaxInputGenerator(self)
        if wizard.exec_() == QDialog.Accepted:
            try:
                content = wizard.get_result()  # this should return the final model text
            except AttributeError:
                QMessageBox.warning(self, "Wizard Error", "Wizard did not return output correctly.")
                return

            tab = FileTab()
            tab.editor.setPlainText(content)
            self.tabs.addTab(tab, "GeneratedModel.in")
            self.tabs.setCurrentWidget(tab)

    def apply_styles(self):
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; background: #ffffff; }
            QTabBar::tab {
                background: #e0e0e0;
                color: #000;
                padding: 5px 15px;
            }
            QTabBar::tab:selected {
                background: #007acc;
                color: white;
            }
        """)
        self.shell_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: black;
                color: lime;
                font-family: Consolas, monospace;
                font-size: 12pt;
            }
        """)
    
    def closeEvent(self, event):
        unsaved_tabs = []

        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, FileTab) and tab.is_modified():
                unsaved_tabs.append((i, tab))

        if unsaved_tabs:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()
    def toggle_dark_mode(self):
        if hasattr(self, "dark_mode") and self.dark_mode:
            self.setStyleSheet("")  # Reset to light
            self.dark_mode = False
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget {
                background-color: #121212;
                color: #e0e0e0;
            }
            QMenuBar, QMenu {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background-color: #2a2a2a;
            }
            QPlainTextEdit, QTextEdit, QLineEdit, QComboBox, QTreeView {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QTabWidget::pane {
                border: 1px solid #444;
            }
            QTabBar::tab {
                background: #1e1e1e;
                color: #e0e0e0;
                padding: 6px;
            }
            QTabBar::tab:selected {
                background: #2e2e2e;
                border-bottom: 2px solid #0078d4;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #1e1e1e;
            }
            QScrollBar::handle {
                background: #444;
                border-radius: 4px;
            }
            """)
            self.dark_mode = True
            self.refresh_welcome_tab()


    
    def load_file_from_explorer(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            tab = FileTab(path)
            self.tabs.addTab(tab, os.path.basename(path))
            self.tabs.setCurrentWidget(tab)
    
    def convert_png_to_h5(self):
        dialog = PNGtoH5Dialog()
        if dialog.exec_() == QDialog.Accepted:
            filepath, dx, dy, dz, zcells = dialog.get_inputs()

            if not filepath or not dx or not dy or not dz:
                QMessageBox.warning(self, "Missing Input", "Please provide file and dx dy dz values.")
                return

            cmd = f'python -m tools.convert_png2h5 "{filepath}" {dx} {dy} {dz}'
            if zcells:
                cmd += f" -zcells {zcells}"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = GPRViewer()
    viewer.show()
    sys.exit(app.exec_())
