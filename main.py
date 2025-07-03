'''import sys
from queue import Queue
from PyQt6.QtWidgets import QApplication
from gui import MainWindow
from data_processor import DataProcessor

def main():
    mode = "file"  # Default to file mode
    if len(sys.argv) > 1 and sys.argv[1] in ["console", "file"]:
        mode = sys.argv[1]
    
    data_queue = Queue()
    processor = DataProcessor(data_queue, mode=mode)
    app = QApplication(sys.argv)
    window = MainWindow(data_queue, processor)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()'''
    
    
    
    
    
import sys
from queue import Queue
from PyQt6.QtWidgets import QApplication
from gui import MainWindow
from data_processor import DataProcessor

def main():
    mode = "file"  # Default to file mode
    if len(sys.argv) > 1 and sys.argv[1] in ["console", "file"]:
        mode = sys.argv[1]
    
    data_queue = Queue()
    processor = DataProcessor(data_queue, mode=mode, input_string="default_input")
    app = QApplication(sys.argv)
    window = MainWindow(data_queue, processor)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()