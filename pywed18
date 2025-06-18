import sys
import os
import subprocess
import threading
import re
from de.runl import GPRMaxInputGenerator
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QPlainTextEdit, QTabWidget, QAction, QInputDialog, QVBoxLayout, QWidget,
    QToolBar, QSplitter, QFileSystemModel, QTreeView, QLineEdit, QLabel, QHBoxLayout,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QPushButton
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QDir, QObject, pyqtSignal


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

class GPRMaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rules = []

        # Format for keywords (GPRMax directives)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#007acc"))
        keyword_format.setFontWeight(QFont.Bold)
        constant_format = QTextCharFormat()
        constant_format.setForeground(QColor("#d19a66"))


        # List of GPRMax directives to highlight
        keywords = [
            "#title", "#domain", "#dx_dy_dz", "#time_window", "#pml_cells",
            "#material", "#waveform", "ca#hertzian_dipole", "#rx",
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
        self.setFixedSize(300, 150)

        layout = QFormLayout(self)

        self.n_input = QLineEdit(str(default_n))
        self.n_input.setPlaceholderText("e.g., 1")
        layout.addRow("Number of models (-n):", self.n_input)

        self.gpu_dropdown = QComboBox()
        self.gpu_dropdown.addItems(["No", "Yes"])
        self.gpu_dropdown.setCurrentText("No")
        layout.addRow("Use GPU:", self.gpu_dropdown)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_inputs(self):
        return self.n_input.text().strip(), self.gpu_dropdown.currentText().strip()


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
        layout.addRow("Velocity (m/s):", self.vel_input)

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
        layout.addRow("Velocity (m/s):", self.vel_input)

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


class GPRViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPR Viewer")
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

        self.convert_png_action = QAction("PNG to H5", self)
        self.convert_png_action.triggered.connect(self.convert_png_to_h5)
        

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.open_folder_action)
        file_menu.addAction(self.save_action)

        run_menu = menubar.addMenu("Run")
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.set_n_action)

        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.merge_action)
        tools_menu.addAction(self.plot_bscan_action)

        
        

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

       
        message = QLabel("""
            <h2 style='text-align: center;'>Welcome to GPR Viewer</h2>
            <p style='text-align: center;'>An IDE for GPRMax Simulation Files</p>
            <p style='text-align: center; font-size: 12px; color: gray;'>Built with ❤️ using PyQt5</p>
            <p style='text-align: center; font-size: 12px; color: gray;'>By Harsha</p>
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
        current_tab = self.tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, "filepath") or not current_tab.filepath:
            QMessageBox.warning(self, "No file", "Please save the file before running.")
            return

        dialog = RunDialog(default_n=self.n_models)
        if dialog.exec_() == QDialog.Accepted:
            n_models, gpu = dialog.get_inputs()

            if not n_models.isdigit():
                QMessageBox.warning(self, "Invalid Input", "Number of models must be an integer.")
                return

            self.n_models = int(n_models)
            cmd = f"python -m gprMax \"{current_tab.filepath}\" -n {self.n_models}"

            if gpu == "Yes":
                cmd += " --gpu"

            self.shell_output.appendPlainText(f"> {cmd}")
            self.run_command(cmd)


    def merge_output_files(self):
        base_name, ok = QInputDialog.getText(self, "Enter Output Base Name",
                                             "Enter base name for .out files (e.g., 'file' for file1.out):")
        if not ok or not base_name.strip():
            return

        remove, remove_ok = QInputDialog.getItem(
            self, "Remove Original .out Files?", "Remove after merging?",
            ["No", "Yes"], 0, False
        )

        cmd = f"python -m tools.outputfiles_merge {base_name.strip()}"
        if remove_ok and remove == "Yes":
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
            filename, components, cmap, dpi, velocity, gpu = dialog.get_inputs()

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
    
