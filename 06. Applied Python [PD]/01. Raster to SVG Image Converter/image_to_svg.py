
import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import vtracer

class ConversionThread(QThread):
    update_log = pyqtSignal(str)
    conversion_complete = pyqtSignal(int)

    def __init__(self, files, output_folder):
        QThread.__init__(self)
        self.files = files
        self.output_folder = output_folder

    def run(self):
        converted_count = 0
        for file in self.files:
            if self.convert_file(file):
                converted_count += 1
        self.conversion_complete.emit(converted_count)

    def convert_file(self, input_path):
        filename = os.path.basename(input_path)
        output_path = os.path.join(self.output_folder, os.path.splitext(filename)[0] + ".svg")
        try:
            vtracer.convert_image_to_svg_py(input_path, output_path)
            self.update_log.emit(f"Converted: {filename} -> {output_path}")
            return True
        except Exception as e:
            self.update_log.emit(f"Error converting {filename}: {str(e)}")
            return False

class ImageToSVGConverter(QtWidgets.QMainWindow):
    def __init__(self):
        super(ImageToSVGConverter, self).__init__()
        uic.loadUi('image_to_svg_converter.ui', self)

        # Connect buttons to functions
        self.browseButton.clicked.connect(self.browse_input)
        self.outputBrowseButton.clicked.connect(self.browse_output)
        self.convertButton.clicked.connect(self.start_conversion)

        # Connect radio buttons to update browse button behavior
        self.filesRadioButton.toggled.connect(self.update_browse_button)
        self.folderRadioButton.toggled.connect(self.update_browse_button)

        # Initialize UI state
        self.update_browse_button()

    def update_browse_button(self):
        if self.filesRadioButton.isChecked():
            self.browseButton.setText("Select Files")
        else:
            self.browseButton.setText("Select Folder")

    def browse_input(self):
        if self.filesRadioButton.isChecked():
            files, _ = QFileDialog.getOpenFileNames(self, "Select Image Files", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
            if files:
                self.pathLineEdit.setText(";".join(files))
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Input Directory")
            if folder:
                self.pathLineEdit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.outputPathLineEdit.setText(folder)

    def start_conversion(self):
        input_path = self.pathLineEdit.text()
        output_folder = self.outputPathLineEdit.text()

        if not input_path:
            QMessageBox.critical(self, "Error", "Please select input files or a folder.")
            return

        if not output_folder:
            output_folder = os.path.dirname(input_path.split(";")[0])  # Use input directory if no output specified

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        files_to_convert = []

        if self.filesRadioButton.isChecked():
            files_to_convert = [f for f in input_path.split(";") if f.lower().endswith(image_extensions)]
        else:
            files_to_convert = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith(image_extensions)]

        if not files_to_convert:
            QMessageBox.warning(self, "No Images Found", "No supported image files were found in the selected location.")
            return

        self.logTextEdit.clear()
        self.disable_ui()

        self.conversion_thread = ConversionThread(files_to_convert, output_folder)
        self.conversion_thread.update_log.connect(self.update_log)
        self.conversion_thread.conversion_complete.connect(self.conversion_complete)
        self.conversion_thread.start()

    def update_log(self, message):
        self.logTextEdit.append(message)

    def conversion_complete(self, converted_count):
        self.enable_ui()
        QMessageBox.information(self, "Conversion Complete", f"Converted {converted_count} images to SVG.")

    def disable_ui(self):
        self.convertButton.setEnabled(False)
        self.browseButton.setEnabled(False)
        self.outputBrowseButton.setEnabled(False)
        self.filesRadioButton.setEnabled(False)
        self.folderRadioButton.setEnabled(False)
        self.pathLineEdit.setEnabled(False)
        self.outputPathLineEdit.setEnabled(False)

    def enable_ui(self):
        self.convertButton.setEnabled(True)
        self.browseButton.setEnabled(True)
        self.outputBrowseButton.setEnabled(True)
        self.filesRadioButton.setEnabled(True)
        self.folderRadioButton.setEnabled(True)
        self.pathLineEdit.setEnabled(True)
        self.outputPathLineEdit.setEnabled(True)
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ImageToSVGConverter()
    window.show()
    
    # Commenting out sys.exit for smoother exit in interactive environments
    # sys.exit(app.exec_())
    
    app.exec_()  # Use this line instead