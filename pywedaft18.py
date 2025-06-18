import sys
import os
import subprocess
import threading
import re
import shutil
from de.runl import GPRMaxInputGenerator
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QPlainTextEdit, QTabWidget, QAction, QInputDialog, QVBoxLayout, QWidget,
    QToolBar, QSplitter, QFileSystemModel, QTreeView, QLineEdit, QLabel, QHBoxLayout,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QPushButton, QCheckBox, QMenu, QAbstractItemView
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

        self.convert_png_action = QAction("PNG to H5", self)
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

        logo_path = "gogo_dark.png" if getattr(self, "dark_mode", False) else "gogo.png"

        message = QLabel(f"""
            <div style="text-align: center; padding-top: 30px;">
                <img src="{logo_path}" alt="gprStudio Logo" width="100" style="margin-bottom: 20px;" />
                <h1 style="color: #0078d4; font-weight: bold; font-size: 24px; margin-bottom: 8px;">
                    gprStudio
                </h1>
                <p style="font-size: 13px; color: #aaa;">
                    The professional IDE for GPRMax simulation projects.
                </p>
                <p style="font-size: 12px; color: #888;">
                    Streamline your modeling, visualize results, and automate your workflow — all in one place.
                </p>
                <p style="font-size: 11px; color: #666; margin-top: 20px;">
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
    # Optional: Aero-style (Windows 7 inspired) styling
    

    viewer = GPRViewer()
    viewer.show()
    sys.exit(app.exec_())


    
