import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QListWidget, QComboBox,
                            QFileDialog, QMessageBox, QProgressBar, QTextEdit,
                            QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from fontTools.ttLib import TTFont
from fontTools.ttLib.woff2 import compress, decompress
import shutil

# This class handles the font conversion process in a separate thread so the app doesn't freeze
class FontConverter(QThread):
    # Signals to update the UI with progress, status, and completion
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    conversion_finished = pyqtSignal(bool, str)
    
    def __init__(self, font_files, output_format, output_dir):
        super().__init__()
        # Store the list of font files, the desired output format, and the output directory
        self.font_files = font_files
        self.output_format = output_format
        self.output_dir = output_dir
        
    def run(self):
        # This function runs when the thread starts
        try:
            total_files = len(self.font_files)
            successful_conversions = 0
            
            # Loop through each font file to convert it
            for i, font_file in enumerate(self.font_files):
                # Update the status to show which file is being converted
                self.status_updated.emit(f"Converting: {os.path.basename(font_file)}")
                
                # Try to convert the font file
                if self.convert_font(font_file):
                    successful_conversions += 1
                
                # Calculate and update progress (as a percentage)
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
            
            # Check if all conversions were successful
            if successful_conversions == total_files:
                self.conversion_finished.emit(True, f"All {total_files} files converted successfully!")
            else:
                self.conversion_finished.emit(True, f"{successful_conversions} out of {total_files} files converted successfully")
                
        except Exception as e:
            # If something goes wrong, send an error message
            self.conversion_finished.emit(False, f"Conversion error: {str(e)}")
    
    def convert_font(self, input_file):
        # This function decides which conversion method to use based on the output format
        try:
            # Get the file name without extension
            file_name = os.path.splitext(os.path.basename(input_file))[0]
            
            # Check the desired output format and call the right conversion function
            if self.output_format == "TTF":
                output_file = os.path.join(self.output_dir, f"{file_name}.ttf")
                return self.convert_to_ttf(input_file, output_file)
            elif self.output_format == "OTF":
                output_file = os.path.join(self.output_dir, f"{file_name}.otf")
                return self.convert_to_otf(input_file, output_file)
            elif self.output_format == "WOFF":
                output_file = os.path.join(self.output_dir, f"{file_name}.woff")
                return self.convert_to_woff(input_file, output_file)
            elif self.output_format == "WOFF2":
                output_file = os.path.join(self.output_dir, f"{file_name}.woff2")
                return self.convert_to_woff2(input_file, output_file)
            elif self.output_format == "EOT":
                output_file = os.path.join(self.output_dir, f"{file_name}.eot")
                return self.convert_to_eot(input_file, output_file)
            
        except Exception as e:
            # Print error if conversion fails for this file
            print(f"Error converting {input_file}: {str(e)}")
            return False
        
        return False
    
    def convert_to_ttf(self, input_file, output_file):
        # Convert a font to TTF format
        try:
            # Load the font file
            font = TTFont(input_file)
            
            # If the input is already a TTF, just copy it
            if input_file.lower().endswith('.ttf'):
                shutil.copy2(input_file, output_file)
                return True
            
            # Convert other formats to TTF
            font.flavor = None  # Remove WOFF/WOFF2 flavor
            font.save(output_file)
            return True
        except Exception as e:
            print(f"Error converting to TTF: {str(e)}")
            return False
    
    def convert_to_otf(self, input_file, output_file):
        # Convert a font to OTF format
        try:
            font = TTFont(input_file)
            
            # If the input is already OTF, just copy it
            if input_file.lower().endswith('.otf'):
                shutil.copy2(input_file, output_file)
                return True
                
            # For non-OTF fonts, convert to TTF instead
            font.flavor = None
            font.save(output_file.replace('.otf', '.ttf'))
            return True
        except Exception as e:
            print(f"Error converting to OTF: {str(e)}")
            return False
    
    def convert_to_woff(self, input_file, output_file):
        # Convert a font to WOFF format
        try:
            font = TTFont(input_file)
            font.flavor = 'woff'
            font.save(output_file)
            return True
        except Exception as e:
            print(f"Error converting to WOFF: {str(e)}")
            return False
    
    def convert_to_woff2(self, input_file, output_file):
        # Convert a font to WOFF2 format
        try:
            font = TTFont(input_file)
            font.flavor = 'woff2'
            font.save(output_file)
            return True
        except Exception as e:
            print(f"Error converting to WOFF2: {str(e)}")
            return False
    
    def convert_to_eot(self, input_file, output_file):
        # Convert a font to EOT format (simplified to TTF for now)
        try:
            # EOT is a Microsoft format and requires external tools
            # For simplicity, we convert to TTF instead
            return self.convert_to_ttf(input_file, output_file.replace('.eot', '.ttf'))
        except Exception as e:
            print(f"Error converting to EOT: {str(e)}")
            return False

# This class creates the main window and UI for the app
class FontConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize variables to store font files and output directory
        self.font_files = []
        self.output_dir = ""
        self.init_ui()
        
    def init_ui(self):
        # Set up the main window
        self.setWindowTitle("Font Converter")
        self.setWindowIcon(QIcon("./icons/icon.png"))  # Optional: set your own icon
        self.setGeometry(100, 100, 800, 600)
        
        # Create the central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add a title label
        title_label = QLabel("Font Converter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # Create a group for file selection
        file_group = QGroupBox("Select Font Files")
        file_layout = QVBoxLayout(file_group)
        
        # Add buttons for selecting files
        file_buttons_layout = QHBoxLayout()
        
        self.select_single_btn = QPushButton("Select Single Font")
        self.select_single_btn.clicked.connect(self.select_single_font)
        file_buttons_layout.addWidget(self.select_single_btn)
        
        self.select_multiple_btn = QPushButton("Select Multiple Fonts")
        self.select_multiple_btn.clicked.connect(self.select_multiple_fonts)
        file_buttons_layout.addWidget(self.select_multiple_btn)
        
        self.clear_files_btn = QPushButton("Clear List")
        self.clear_files_btn.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(self.clear_files_btn)
        
        file_layout.addLayout(file_buttons_layout)
        
        # Add a list to display selected files
        self.files_list = QListWidget()
        file_layout.addWidget(self.files_list)
        
        main_layout.addWidget(file_group)
        
        # Create a group for conversion settings
        conversion_group = QGroupBox("Conversion Settings")
        conversion_layout = QVBoxLayout(conversion_group)
        
        # Add a dropdown to choose the output format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TTF", "OTF", "WOFF", "WOFF2", "EOT"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        conversion_layout.addLayout(format_layout)
        
        # Add a section to choose the output directory
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel("No output directory selected")
        output_layout.addWidget(self.output_dir_label)
        
        self.select_output_btn = QPushButton("Select Output Directory")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        output_layout.addWidget(self.select_output_btn)
        
        conversion_layout.addLayout(output_layout)
        
        main_layout.addWidget(conversion_group)
        
        # Add the convert button
        self.convert_btn = QPushButton("Start Conversion")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        main_layout.addWidget(self.convert_btn)
        
        # Add a progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Add a text area for status updates
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Conversion status will appear here...")
        main_layout.addWidget(self.status_text)
        
    def select_single_font(self):
        # Open a dialog to select one font file
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Font File",
            "",
            "Font Files (*.ttf *.otf *.woff *.woff2 *.eot);;All Files (*)"
        )
        
        if file_path:
            # Replace the current list with the selected file
            self.font_files = [file_path]
            self.update_files_list()
            self.update_convert_button()
    
    def select_multiple_fonts(self):
        # Open a dialog to select multiple font files
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Font Files",
            "",
            "Font Files (*.ttf *.otf *.woff *.woff2 *.eot);;All Files (*)"
        )
        
        if file_paths:
            # Add new files to the list, avoiding duplicates
            for path in file_paths:
                if path not in self.font_files:
                    self.font_files.append(path)
            
            self.update_files_list()
            self.update_convert_button()
    
    def clear_files(self):
        # Clear the list of selected files
        self.font_files = []
        self.update_files_list()
        self.update_convert_button()
    
    def update_files_list(self):
        # Update the file list display
        self.files_list.clear()
        for file_path in self.font_files:
            self.files_list.addItem(os.path.basename(file_path))
    
    def select_output_directory(self):
        # Open a dialog to select the output directory
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir = directory
            self.output_dir_label.setText(f"Output Directory: {directory}")
            self.update_convert_button()
    
    def update_convert_button(self):
        # Enable the convert button only if files and output directory are selected
        self.convert_btn.setEnabled(
            len(self.font_files) > 0 and self.output_dir != ""
        )
    
    def start_conversion(self):
        # Start the conversion process
        if not self.font_files or not self.output_dir:
            QMessageBox.warning(self, "Error", "Please select font files and an output directory")
            return
        
        # Get the selected output format
        output_format = self.format_combo.currentText()
        
        # Show the progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.convert_btn.setEnabled(False)
        
        # Start conversion in a separate thread
        self.converter_thread = FontConverter(
            self.font_files, 
            output_format, 
            self.output_dir
        )
        
        # Connect signals to update the UI
        self.converter_thread.progress_updated.connect(self.update_progress)
        self.converter_thread.status_updated.connect(self.update_status)
        self.converter_thread.conversion_finished.connect(self.conversion_finished)
        
        self.converter_thread.start()
    
    def update_progress(self, value):
        # Update the progress bar
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        # Add a status message to the text area
        self.status_text.append(message)
    
    def conversion_finished(self, success, message):
        # Handle the end of the conversion process
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_text.append(f"✅ {message}")
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_text.append(f"❌ {message}")

def main():
    # Create and run the application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = FontConverterApp()
    window.show()
    
    # Start the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()