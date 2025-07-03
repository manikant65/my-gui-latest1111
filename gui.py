        
'''  
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        key_layout.addWidget(self.key_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        if self.mode == "console":
            self.resume_button.setVisible(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 6000), y_range=(0, 10)):
            plot_widget.setLabel('bottom', 'Time (ms)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 6001, 500)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate", y_range=(0, 10))

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate", y_range=(0, 10))

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio", y_range=(0, 1))

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio", y_range=(0, 1))

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} ms\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = (time.time() - self.start_time) * 1000  # Convert to milliseconds
                logging.debug(f"Processing data: {data}")

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                        if new_session % 2 == 0:
                            expected_types.add('key')
                        else:
                            expected_types.add('kbps_data')
                        missing_types = expected_types - self.session_data_types
                        if missing_types and self.current_session != -1:
                            logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                            if 'key' not in self.session_data_types:
                                self.key_display.setText(f"Key (Session {self.current_session}, Length N/A): Not Available")
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                    continue

                self.session_data_types.add(data['type'])

                if data['type'] == 'timestamp_spd1':
                    timestamp_ps = int(data['value'])
                    logging.debug(f"SPD1 timestamp: {timestamp_ps}")
                    partition1 = min((timestamp_ps // 100) % 40, 39)
                    self.hist_data_all[partition1] += 1
                    self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
                    self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
                    self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
                    self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
                    logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

                    self.hist_data_tab[partition1] += 1
                    self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
                    self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
                    self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
                    self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
                    logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")

                elif data['type'] == 'timestamp_spd2':
                    timestamp_ps = int(data['value'])
                    logging.debug(f"SPD2 timestamp: {timestamp_ps}")
                    partition2 = min((timestamp_ps // 100) % 40, 39)
                    self.hist2_data_all[partition2] += 1
                    self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
                    self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
                    self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
                    self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
                    logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

                    self.hist2_data_tab[partition2] += 1
                    self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
                    self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
                    self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
                    self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
                    logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")

                elif data['type'] == 'qber':
                    qber_val = float(data['value'])
                    logging.debug(f"QBER: {qber_val}")
                    self.qber_x_all.append(current_time)
                    self.qber_y_all.append(qber_val)
                    while self.qber_x_all and self.qber_x_all[0] < current_time - 6000:
                        self.qber_x_all.pop(0)
                        self.qber_y_all.pop(0)
                    self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
                    self.qber_plot_all.setXRange(max(0, current_time - 6000), current_time)

                    self.qber_x_tab.append(current_time)
                    self.qber_y_tab.append(qber_val)
                    while self.qber_x_tab and self.qber_x_tab[0] < current_time - 6000:
                        self.qber_x_tab.pop(0)
                        self.qber_y_tab.pop(0)
                    self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
                    self.qber_plot_tab.setXRange(max(0, current_time - 6000), current_time)

                elif data['type'] == 'kbps_data':
                    kbps = float(data['kbps'])
                    logging.debug(f"KBPS: {kbps}")
                    self.kbps_x_all.append(current_time)
                    self.kbps_y_all.append(kbps)
                    while self.kbps_x_all and self.kbps_x_all[0] < current_time - 6000:
                        self.kbps_x_all.pop(0)
                        self.kbps_y_all.pop(0)
                    self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
                    self.kbps_plot_all.setXRange(max(0, current_time - 6000), current_time)

                    self.kbps_x_tab.append(current_time)
                    self.kbps_y_tab.append(kbps)
                    while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 6000:
                        self.kbps_x_tab.pop(0)
                        self.kbps_y_tab.pop(0)
                    self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
                    self.kbps_plot_tab.setXRange(max(0, current_time - 6000), current_time)

                elif data['type'] == 'key':
                    logging.debug(f"Key (length {data['length']}): {data['value'][:40]}...")
                    self.key_display.setText(f"Key (Session {self.current_session}, Length {data['length']}): {data['value'][:40]}...")
                    self.key_display.setToolTip(data['value'])

                elif data['type'] == 'visibility':
                    vis_val = float(data['value'])
                    logging.debug(f"Visibility: {vis_val}")
                    self.visibility_x_all.append(current_time)
                    self.visibility_y_all.append(vis_val)
                    while self.visibility_x_all and self.visibility_x_all[0] < current_time - 6000:
                        self.visibility_x_all.pop(0)
                        self.visibility_y_all.pop(0)
                    self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
                    self.visibility_plot_all.setXRange(max(0, current_time - 6000), current_time)

                    self.visibility_x_tab.append(current_time)
                    self.visibility_y_tab.append(vis_val)
                    while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 6000:
                        self.visibility_x_tab.pop(0)
                        self.visibility_y_tab.pop(0)
                    self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
                    self.visibility_plot_tab.setXRange(max(0, current_time - 6000), current_time)

                elif data['type'] == 'spd1_decaystate':
                    spd1_val = float(data['value'])
                    logging.debug(f"SPD1 Decay: {spd1_val}")
                    self.spd1_x_all.append(current_time)
                    self.spd1_y_all.append(spd1_val)
                    while self.spd1_x_all and self.spd1_x_all[0] < current_time - 6000:
                        self.spd1_x_all.pop(0)
                        self.spd1_y_all.pop(0)
                    self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
                    self.spd1_plot_all.setXRange(max(0, current_time - 6000), current_time)

                    self.spd1_x_tab.append(current_time)
                    self.spd1_y_tab.append(spd1_val)
                    while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 6000:
                        self.spd1_x_tab.pop(0)
                        self.spd1_y_tab.pop(0)
                    self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
                    self.spd1_plot_tab.setXRange(max(0, current_time - 6000), current_time)

        except Empty:
            pass

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.key_display.setText(f"Key (None): None")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept()'''
        
        
        
        

#BELOW IS FOR DYNAMIC Y-AXIS FOR QBER AND VISIBILITY
'''
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        key_layout.addWidget(self.key_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        if self.mode == "console":
            self.resume_button.setVisible(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 60), y_range=None):
            plot_widget.setLabel('bottom', 'Time (s)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            if y_range:
                plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 61, 5)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate")

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate")

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio")

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio")

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} s\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = time.time() - self.start_time  # Time in seconds
                logging.debug(f"Processing data: {data}")

                # Calculate dynamic x-axis ticks for the current 60-second window
                x_min = max(0, current_time - 60)
                x_start = math.floor(x_min / 5) * 5  # Nearest 5-second mark below x_min
                x_ticks = [(i, f"{i:.0f}") for i in range(x_start, int(current_time) + 5, 5)]
                
                # List of all line plots to update x-axis ticks
                line_plots = [
                    (self.qber_plot_all, self.qber_x_all, self.qber_y_all, self.qber_line_all),
                    (self.qber_plot_tab, self.qber_x_tab, self.qber_y_tab, self.qber_line_tab),
                    (self.kbps_plot_all, self.kbps_x_all, self.kbps_y_all, self.kbps_line_all),
                    (self.kbps_plot_tab, self.kbps_x_tab, self.kbps_y_tab, self.kbps_line_tab),
                    (self.visibility_plot_all, self.visibility_x_all, self.visibility_y_all, self.visibility_line_all),
                    (self.visibility_plot_tab, self.visibility_x_tab, self.visibility_y_tab, self.visibility_line_tab),
                    (self.spd1_plot_all, self.spd1_x_all, self.spd1_y_all, self.spd1_line_all),
                    (self.spd1_plot_tab, self.spd1_x_tab, self.spd1_y_tab, self.spd1_line_tab)
                ]

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                        if new_session % 2 == 0:
                            expected_types.add('key')
                        else:
                            expected_types.add('kbps_data')
                        missing_types = expected_types - self.session_data_types
                        if missing_types and self.current_session != -1:
                            logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                            if 'key' not in self.session_data_types:
                                self.key_display.setText(f"Key (Session {self.current_session}, Length N/A): Not Available")
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                    continue

                self.session_data_types.add(data['type'])

                if data['type'] == 'timestamp_spd1':
                    timestamp_ps = int(data['value'])
                    logging.debug(f"SPD1 timestamp: {timestamp_ps}")
                    partition1 = min((timestamp_ps // 100) % 40, 39)
                    self.hist_data_all[partition1] += 1
                    self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
                    self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
                    self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
                    self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
                    logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

                    self.hist_data_tab[partition1] += 1
                    self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
                    self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
                    self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
                    self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
                    logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")

                elif data['type'] == 'timestamp_spd2':
                    timestamp_ps = int(data['value'])
                    logging.debug(f"SPD2 timestamp: {timestamp_ps}")
                    partition2 = min((timestamp_ps // 100) % 40, 39)
                    self.hist2_data_all[partition2] += 1
                    self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
                    self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
                    self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
                    self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
                    logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

                    self.hist2_data_tab[partition2] += 1
                    self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
                    self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
                    self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
                    self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
                    logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")

                elif data['type'] == 'qber':
                    qber_val = float(data['value'])
                    logging.debug(f"QBER: {qber_val}")
                    self.qber_x_all.append(current_time)
                    self.qber_y_all.append(qber_val)
                    while self.qber_x_all and self.qber_x_all[0] < current_time - 60:
                        self.qber_x_all.pop(0)
                        self.qber_y_all.pop(0)
                    self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
                    self.qber_plot_all.setXRange(max(0, current_time - 60), current_time)
                    self.qber_plot_all.getAxis('bottom').setTicks([x_ticks])
                    qber_lower = math.floor(qber_val) - 10
                    qber_upper = math.floor(qber_val) + 10
                    if qber_lower < 0:
                        qber_lower = 0
                        qber_upper = 20
                    qber_ticks = list(range(int(qber_lower), int(qber_upper) + 1, 2))
                    self.qber_plot_all.setYRange(qber_lower, qber_upper)
                    self.qber_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

                    self.qber_x_tab.append(current_time)
                    self.qber_y_tab.append(qber_val)
                    while self.qber_x_tab and self.qber_x_tab[0] < current_time - 60:
                        self.qber_x_tab.pop(0)
                        self.qber_y_tab.pop(0)
                    self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
                    self.qber_plot_tab.setXRange(max(0, current_time - 60), current_time)
                    self.qber_plot_tab.getAxis('bottom').setTicks([x_ticks])
                    self.qber_plot_tab.setYRange(qber_lower, qber_upper)
                    self.qber_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

                elif data['type'] == 'kbps_data':
                    kbps = float(data['kbps'])
                    logging.debug(f"KBPS: {kbps}")
                    self.kbps_x_all.append(current_time)
                    self.kbps_y_all.append(kbps)
                    while self.kbps_x_all and self.kbps_x_all[0] < current_time - 60:
                        self.kbps_x_all.pop(0)
                        self.kbps_y_all.pop(0)
                    self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
                    self.kbps_plot_all.setXRange(max(0, current_time - 60), current_time)
                    self.kbps_plot_all.getAxis('bottom').setTicks([x_ticks])

                    self.kbps_x_tab.append(current_time)
                    self.kbps_y_tab.append(kbps)
                    while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 60:
                        self.kbps_x_tab.pop(0)
                        self.kbps_y_tab.pop(0)
                    self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
                    self.kbps_plot_tab.setXRange(max(0, current_time - 60), current_time)
                    self.kbps_plot_tab.getAxis('bottom').setTicks([x_ticks])

                elif data['type'] == 'key':
                    logging.debug(f"Key (length {data['length']}): {data['value'][:40]}...")
                    self.key_display.setText(f"Key (Session {self.current_session}, Length {data['length']}): {data['value'][:40]}...")
                    self.key_display.setToolTip(data['value'])

                elif data['type'] == 'visibility':
                    vis_val = float(data['value'])
                    logging.debug(f"Visibility: {vis_val}")
                    self.visibility_x_all.append(current_time)
                    self.visibility_y_all.append(vis_val)
                    while self.visibility_x_all and self.visibility_x_all[0] < current_time - 60:
                        self.visibility_x_all.pop(0)
                        self.visibility_y_all.pop(0)
                    self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
                    self.visibility_plot_all.setXRange(max(0, current_time - 60), current_time)
                    self.visibility_plot_all.getAxis('bottom').setTicks([x_ticks])
                    vis_lower = math.floor(vis_val * 10) / 10 - 0.1
                    vis_upper = math.floor(vis_val * 10) / 10 + 0.1
                    if vis_lower < 0:
                        vis_lower = 0
                        vis_upper = 0.2
                    vis_ticks = [vis_lower + i * 0.02 for i in range(int((vis_upper - vis_lower) / 0.02) + 1)]
                    self.visibility_plot_all.setYRange(vis_lower, vis_upper)
                    self.visibility_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

                    self.visibility_x_tab.append(current_time)
                    self.visibility_y_tab.append(vis_val)
                    while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 60:
                        self.visibility_x_tab.pop(0)
                        self.visibility_y_tab.pop(0)
                    self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
                    self.visibility_plot_tab.setXRange(max(0, current_time - 60), current_time)
                    self.visibility_plot_tab.getAxis('bottom').setTicks([x_ticks])
                    self.visibility_plot_tab.setYRange(vis_lower, vis_upper)
                    self.visibility_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

                elif data['type'] == 'spd1_decaystate':
                    spd1_val = float(data['value'])
                    logging.debug(f"SPD1 Decay: {spd1_val}")
                    self.spd1_x_all.append(current_time)
                    self.spd1_y_all.append(spd1_val)
                    while self.spd1_x_all and self.spd1_x_all[0] < current_time - 60:
                        self.spd1_x_all.pop(0)
                        self.spd1_y_all.pop(0)
                    self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
                    self.spd1_plot_all.setXRange(max(0, current_time - 60), current_time)
                    self.spd1_plot_all.getAxis('bottom').setTicks([x_ticks])

                    self.spd1_x_tab.append(current_time)
                    self.spd1_y_tab.append(spd1_val)
                    while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 60:
                        self.spd1_x_tab.pop(0)
                        self.spd1_y_tab.pop(0)
                    self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
                    self.spd1_plot_tab.setXRange(max(0, current_time - 60), current_time)
                    self.spd1_plot_tab.getAxis('bottom').setTicks([x_ticks])

        except Empty:
            pass

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.key_display.setText(f"Key (None): None")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept()'''
        
        
'''      
#BELOW IS FOR PLOTTING PREVIOUS SESSION DATA IF DATA IN CURRENT SESSION IS MISSING

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        key_layout.addWidget(self.key_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        if self.mode == "console":
            self.resume_button.setVisible(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 60), y_range=None):
            plot_widget.setLabel('bottom', 'Time (s)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            if y_range:
                plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 61, 5)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate")

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate")

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio")

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio")

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} s\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = time.time() - self.start_time  # Time in seconds
                logging.debug(f"Processing data: {data}")

                # Calculate dynamic x-axis ticks for the current 60-second window
                x_min = max(0, current_time - 60)
                x_start = math.floor(x_min / 5) * 5  # Nearest 5-second mark below x_min
                x_ticks = [(i, f"{i:.0f}") for i in range(x_start, int(current_time) + 5, 5)]
                
                # List of all line plots to update x-axis ticks
                line_plots = [
                    (self.qber_plot_all, self.qber_x_all, self.qber_y_all, self.qber_line_all),
                    (self.qber_plot_tab, self.qber_x_tab, self.qber_y_tab, self.qber_line_tab),
                    (self.kbps_plot_all, self.kbps_x_all, self.kbps_y_all, self.kbps_line_all),
                    (self.kbps_plot_tab, self.kbps_x_tab, self.kbps_y_tab, self.kbps_line_tab),
                    (self.visibility_plot_all, self.visibility_x_all, self.visibility_y_all, self.visibility_line_all),
                    (self.visibility_plot_tab, self.visibility_x_tab, self.visibility_y_tab, self.visibility_line_tab),
                    (self.spd1_plot_all, self.spd1_x_all, self.spd1_y_all, self.spd1_line_all),
                    (self.spd1_plot_tab, self.spd1_x_tab, self.spd1_y_tab, self.spd1_line_tab)
                ]

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                        if new_session % 2 == 0:
                            expected_types.add('key')
                        else:
                            expected_types.add('kbps_data')
                        missing_types = expected_types - self.session_data_types
                        if missing_types and self.current_session != -1:
                            logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                            # If session was empty, reuse last session's data
                            if not self.session_data_types:
                                logging.info(f"Session {self.current_session} was empty, reusing last session data")
                                for data_type in expected_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        for value in self.last_session_data[data_type]:
                                            self.update_plot_data(data_type, value, current_time, x_ticks)
                                    elif self.last_session_data[data_type] is not None:
                                        if data_type == 'key':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, length=len(self.last_session_data[data_type]))
                                        elif data_type == 'kbps_data':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, kbps=True)
                                        else:
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks)
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                        # Reset histogram data for new session
                        self.last_session_data["timestamp_spd1"] = []
                        self.last_session_data["timestamp_spd2"] = []
                    continue

                self.session_data_types.add(data['type'])
                self.update_plot_data(data['type'], data.get('value', data.get('kbps')), current_time, x_ticks, length=data.get('length'), kbps='kbps' in data)

        except Empty:
            pass

    def update_plot_data(self, data_type, value, current_time, x_ticks, length=None, kbps=False):
        if data_type == 'timestamp_spd1':
            timestamp_ps = int(value)
            logging.debug(f"SPD1 timestamp: {timestamp_ps}")
            partition1 = min((timestamp_ps // 100) % 40, 39)
            self.hist_data_all[partition1] += 1
            self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
            self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
            self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
            self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
            logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

            self.hist_data_tab[partition1] += 1
            self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
            self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
            self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
            self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")
            self.last_session_data["timestamp_spd1"].append(timestamp_ps)

        elif data_type == 'timestamp_spd2':
            timestamp_ps = int(value)
            logging.debug(f"SPD2 timestamp: {timestamp_ps}")
            partition2 = min((timestamp_ps // 100) % 40, 39)
            self.hist2_data_all[partition2] += 1
            self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
            self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
            self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
            self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
            logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

            self.hist2_data_tab[partition2] += 1
            self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
            self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
            self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
            self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")
            self.last_session_data["timestamp_spd2"].append(timestamp_ps)

        elif data_type == 'qber':
            qber_val = float(value)
            logging.debug(f"QBER: {qber_val}")
            self.qber_x_all.append(current_time)
            self.qber_y_all.append(qber_val)
            while self.qber_x_all and self.qber_x_all[0] < current_time - 60:
                self.qber_x_all.pop(0)
                self.qber_y_all.pop(0)
            self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
            self.qber_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_all.getAxis('bottom').setTicks([x_ticks])
            qber_lower = math.floor(qber_val) - 10
            qber_upper = math.floor(qber_val) + 10
            if qber_lower < 0:
                qber_lower = 0
                qber_upper = 20
            qber_ticks = list(range(int(qber_lower), int(qber_upper) + 1, 2))
            self.qber_plot_all.setYRange(qber_lower, qber_upper)
            self.qber_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

            self.qber_x_tab.append(current_time)
            self.qber_y_tab.append(qber_val)
            while self.qber_x_tab and self.qber_x_tab[0] < current_time - 60:
                self.qber_x_tab.pop(0)
                self.qber_y_tab.pop(0)
            self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
            self.qber_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.qber_plot_tab.setYRange(qber_lower, qber_upper)
            self.qber_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])
            self.last_session_data["qber"] = qber_val

        elif data_type == 'kbps_data':
            kbps = float(value)
            logging.debug(f"KBPS: {kbps}")
            self.kbps_x_all.append(current_time)
            self.kbps_y_all.append(kbps)
            while self.kbps_x_all and self.kbps_x_all[0] < current_time - 60:
                self.kbps_x_all.pop(0)
                self.kbps_y_all.pop(0)
            self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
            self.kbps_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.kbps_x_tab.append(current_time)
            self.kbps_y_tab.append(kbps)
            while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 60:
                self.kbps_x_tab.pop(0)
                self.kbps_y_tab.pop(0)
            self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
            self.kbps_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["kbps_data"] = kbps

        elif data_type == 'key':
            logging.debug(f"Key (length {length}): {value[:40]}...")
            self.key_display.setText(f"Key (Session {self.current_session}, Length {length}): {value[:40]}...")
            self.key_display.setToolTip(value)
            self.last_session_data["key"] = value

        elif data_type == 'visibility':
            vis_val = float(value)
            logging.debug(f"Visibility: {vis_val}")
            self.visibility_x_all.append(current_time)
            self.visibility_y_all.append(vis_val)
            while self.visibility_x_all and self.visibility_x_all[0] < current_time - 60:
                self.visibility_x_all.pop(0)
                self.visibility_y_all.pop(0)
            self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
            self.visibility_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_all.getAxis('bottom').setTicks([x_ticks])
            vis_lower = math.floor(vis_val * 10) / 10 - 0.1
            vis_upper = math.floor(vis_val * 10) / 10 + 0.1
            if vis_lower < 0:
                vis_lower = 0
                vis_upper = 0.2
            vis_ticks = [vis_lower + i * 0.02 for i in range(int((vis_upper - vis_lower) / 0.02) + 1)]
            self.visibility_plot_all.setYRange(vis_lower, vis_upper)
            self.visibility_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

            self.visibility_x_tab.append(current_time)
            self.visibility_y_tab.append(vis_val)
            while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 60:
                self.visibility_x_tab.pop(0)
                self.visibility_y_tab.pop(0)
            self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
            self.visibility_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.visibility_plot_tab.setYRange(vis_lower, vis_upper)
            self.visibility_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])
            self.last_session_data["visibility"] = vis_val

        elif data_type == 'spd1_decaystate':
            spd1_val = float(value)
            logging.debug(f"SPD1 Decay: {spd1_val}")
            self.spd1_x_all.append(current_time)
            self.spd1_y_all.append(spd1_val)
            while self.spd1_x_all and self.spd1_x_all[0] < current_time - 60:
                self.spd1_x_all.pop(0)
                self.spd1_y_all.pop(0)
            self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
            self.spd1_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.spd1_x_tab.append(current_time)
            self.spd1_y_tab.append(spd1_val)
            while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 60:
                self.spd1_x_tab.pop(0)
                self.spd1_y_tab.pop(0)
            self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
            self.spd1_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["spd1_decaystate"] = spd1_val

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.key_display.setText(f"Key (None): None")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept()'''
        
        
        
        
'''        
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        key_layout.addWidget(self.key_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        if self.mode == "console":
            self.resume_button.setVisible(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 60), y_range=None):
            plot_widget.setLabel('bottom', 'Time (s)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            if y_range:
                plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 61, 5)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate")

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate")

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio")

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio")

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} s\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = time.time() - self.start_time  # Time in seconds
                logging.debug(f"Processing data: {data}")

                # Calculate dynamic x-axis ticks for the current 60-second window
                x_min = max(0, current_time - 60)
                x_start = math.floor(x_min / 5) * 5  # Nearest 5-second mark below x_min
                x_ticks = [(i, f"{i:.0f}") for i in range(x_start, int(current_time) + 5, 5)]
                
                # List of all line plots to update x-axis ticks
                line_plots = [
                    (self.qber_plot_all, self.qber_x_all, self.qber_y_all, self.qber_line_all),
                    (self.qber_plot_tab, self.qber_x_tab, self.qber_y_tab, self.qber_line_tab),
                    (self.kbps_plot_all, self.kbps_x_all, self.kbps_y_all, self.kbps_line_all),
                    (self.kbps_plot_tab, self.kbps_x_tab, self.kbps_y_tab, self.kbps_line_tab),
                    (self.visibility_plot_all, self.visibility_x_all, self.visibility_y_all, self.visibility_line_all),
                    (self.visibility_plot_tab, self.visibility_x_tab, self.visibility_y_tab, self.visibility_line_tab),
                    (self.spd1_plot_all, self.spd1_x_all, self.spd1_y_all, self.spd1_line_all),
                    (self.spd1_plot_tab, self.spd1_x_tab, self.spd1_y_tab, self.spd1_line_tab)
                ]

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                        if new_session % 2 == 0:
                            expected_types.add('key')
                        else:
                            expected_types.add('kbps_data')
                        missing_types = expected_types - self.session_data_types
                        if missing_types:
                            logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                            if self.current_session == -1:
                                # Initialize missing data for first session (except timestamps)
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        continue  # Keep timestamps empty
                                    elif data_type == 'key':
                                        self.update_plot_data('key', "0" * 128, current_time, x_ticks, length=128)
                                        self.last_session_data['key'] = "0" * 128
                                        logging.info(f"Initialized missing {data_type} to '{'0' * 128}' for session {self.current_session}")
                                    else:
                                        self.update_plot_data(data_type, 0, current_time, x_ticks, kbps=(data_type == 'kbps_data'))
                                        self.last_session_data[data_type] = 0
                                        logging.info(f"Initialized missing {data_type} to 0 for session {self.current_session}")
                            else:
                                # Reuse last session data for subsequent sessions
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        for value in self.last_session_data[data_type]:
                                            self.update_plot_data(data_type, value, current_time, x_ticks)
                                    elif self.last_session_data[data_type] is not None:
                                        if data_type == 'key':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, length=len(self.last_session_data[data_type]))
                                        elif data_type == 'kbps_data':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, kbps=True)
                                        else:
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks)
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                        # Reset histogram data for new session
                        self.last_session_data["timestamp_spd1"] = []
                        self.last_session_data["timestamp_spd2"] = []
                    continue

                self.session_data_types.add(data['type'])
                self.update_plot_data(data['type'], data.get('value', data.get('kbps')), current_time, x_ticks, length=data.get('length'), kbps='kbps' in data)

        except Empty:
            pass

    def update_plot_data(self, data_type, value, current_time, x_ticks, length=None, kbps=False):
        if data_type == 'timestamp_spd1':
            timestamp_ps = int(value)
            logging.debug(f"SPD1 timestamp: {timestamp_ps}")
            partition1 = min((timestamp_ps // 100) % 40, 39)
            self.hist_data_all[partition1] += 1
            self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
            self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
            self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
            self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
            logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

            self.hist_data_tab[partition1] += 1
            self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
            self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
            self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
            self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")
            self.last_session_data["timestamp_spd1"].append(timestamp_ps)

        elif data_type == 'timestamp_spd2':
            timestamp_ps = int(value)
            logging.debug(f"SPD2 timestamp: {timestamp_ps}")
            partition2 = min((timestamp_ps // 100) % 40, 39)
            self.hist2_data_all[partition2] += 1
            self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
            self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
            self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
            self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
            logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

            self.hist2_data_tab[partition2] += 1
            self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
            self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
            self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
            self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")
            self.last_session_data["timestamp_spd2"].append(timestamp_ps)

        elif data_type == 'qber':
            qber_val = float(value)
            logging.debug(f"QBER: {qber_val}")
            self.qber_x_all.append(current_time)
            self.qber_y_all.append(qber_val)
            while self.qber_x_all and self.qber_x_all[0] < current_time - 60:
                self.qber_x_all.pop(0)
                self.qber_y_all.pop(0)
            self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
            self.qber_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_all.getAxis('bottom').setTicks([x_ticks])
            qber_lower = math.floor(qber_val) - 10
            qber_upper = math.floor(qber_val) + 10
            if qber_lower < 0:
                qber_lower = 0
                qber_upper = 20
            qber_ticks = list(range(int(qber_lower), int(qber_upper) + 1, 2))
            self.qber_plot_all.setYRange(qber_lower, qber_upper)
            self.qber_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

            self.qber_x_tab.append(current_time)
            self.qber_y_tab.append(qber_val)
            while self.qber_x_tab and self.qber_x_tab[0] < current_time - 60:
                self.qber_x_tab.pop(0)
                self.qber_y_tab.pop(0)
            self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
            self.qber_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.qber_plot_tab.setYRange(qber_lower, qber_upper)
            self.qber_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])
            self.last_session_data["qber"] = qber_val

        elif data_type == 'kbps_data':
            kbps = float(value)
            logging.debug(f"KBPS: {kbps}")
            self.kbps_x_all.append(current_time)
            self.kbps_y_all.append(kbps)
            while self.kbps_x_all and self.kbps_x_all[0] < current_time - 60:
                self.kbps_x_all.pop(0)
                self.kbps_y_all.pop(0)
            self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
            self.kbps_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.kbps_x_tab.append(current_time)
            self.kbps_y_tab.append(kbps)
            while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 60:
                self.kbps_x_tab.pop(0)
                self.kbps_y_tab.pop(0)
            self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
            self.kbps_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["kbps_data"] = kbps

        elif data_type == 'key':
            logging.debug(f"Key (length {length}): {value[:40]}...")
            self.key_display.setText(f"Key (Session {self.current_session}, Length {length}): {value[:40]}...")
            self.key_display.setToolTip(value)
            self.last_session_data["key"] = value

        elif data_type == 'visibility':
            vis_val = float(value)
            logging.debug(f"Visibility: {vis_val}")
            self.visibility_x_all.append(current_time)
            self.visibility_y_all.append(vis_val)
            while self.visibility_x_all and self.visibility_x_all[0] < current_time - 60:
                self.visibility_x_all.pop(0)
                self.visibility_y_all.pop(0)
            self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
            self.visibility_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_all.getAxis('bottom').setTicks([x_ticks])
            vis_lower = math.floor(vis_val * 10) / 10 - 0.1
            vis_upper = math.floor(vis_val * 10) / 10 + 0.1
            if vis_lower < 0:
                vis_lower = 0
                vis_upper = 0.2
            vis_ticks = [vis_lower + i * 0.02 for i in range(int((vis_upper - vis_lower) / 0.02) + 1)]
            self.visibility_plot_all.setYRange(vis_lower, vis_upper)
            self.visibility_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

            self.visibility_x_tab.append(current_time)
            self.visibility_y_tab.append(vis_val)
            while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 60:
                self.visibility_x_tab.pop(0)
                self.visibility_y_tab.pop(0)
            self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
            self.visibility_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.visibility_plot_tab.setYRange(vis_lower, vis_upper)
            self.visibility_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])
            self.last_session_data["visibility"] = vis_val

        elif data_type == 'spd1_decaystate':
            spd1_val = float(value)
            logging.debug(f"SPD1 Decay: {spd1_val}")
            self.spd1_x_all.append(current_time)
            self.spd1_y_all.append(spd1_val)
            while self.spd1_x_all and self.spd1_x_all[0] < current_time - 60:
                self.spd1_x_all.pop(0)
                self.spd1_y_all.pop(0)
            self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
            self.spd1_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.spd1_x_tab.append(current_time)
            self.spd1_y_tab.append(spd1_val)
            while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 60:
                self.spd1_x_tab.pop(0)
                self.spd1_y_tab.pop(0)
            self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
            self.spd1_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["spd1_decaystate"] = spd1_val

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.key_display.setText(f"Key (None): None")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept() '''
        
        
        
        
# INPUT VISIBLE IN BOTH MODE
'''
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar, QLineEdit
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None,
            "input_string": None
        }
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay, QLabel#inputDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QLineEdit#inputField {
                background: #263238;
                color: #E0F7FA;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        self.input_display = QLabel("Input: None", objectName="inputDisplay")
        key_layout.addWidget(self.key_display)
        key_layout.addWidget(self.input_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.input_label = QLabel("Input String:", objectName="marqueeLabel")
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Enter input string for QKD simulation")
        self.input_field.setMinimumWidth(200)
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        if self.mode == "console":
            self.resume_button.setVisible(False)
        button_layout.addWidget(self.input_label)
        button_layout.addWidget(self.input_field)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        input_string = self.input_field.text() or "default_input" if self.mode == "console" else None
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position, input_string=input_string)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        self.input_label.setVisible(self.mode == "console")
        self.input_field.setVisible(self.mode == "console")
        self.input_display.setText("Input: None")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 60), y_range=None):
            plot_widget.setLabel('bottom', 'Time (s)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            if y_range:
                plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 61, 5)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate")

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate")

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio")

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio")

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} s\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = time.time() - self.start_time
                logging.debug(f"Processing data: {data}")

                x_min = max(0, current_time - 60)
                x_start = math.floor(x_min / 5) * 5
                x_ticks = [(i, f"{i:.0f}") for i in range(x_start, int(current_time) + 5, 5)]

                line_plots = [
                    (self.qber_plot_all, self.qber_x_all, self.qber_y_all, self.qber_line_all),
                    (self.qber_plot_tab, self.qber_x_tab, self.qber_y_tab, self.qber_line_tab),
                    (self.kbps_plot_all, self.kbps_x_all, self.kbps_y_all, self.kbps_line_all),
                    (self.kbps_plot_tab, self.kbps_x_tab, self.kbps_y_tab, self.kbps_line_tab),
                    (self.visibility_plot_all, self.visibility_x_all, self.visibility_y_all, self.visibility_line_all),
                    (self.visibility_plot_tab, self.visibility_x_tab, self.visibility_y_tab, self.visibility_line_tab),
                    (self.spd1_plot_all, self.spd1_x_all, self.spd1_y_all, self.spd1_line_all),
                    (self.spd1_plot_tab, self.spd1_x_tab, self.spd1_y_tab, self.spd1_line_tab)
                ]

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber','kbps_data','input_string'}
                        if self.mode == 'console':
                            expected_types.add('input_string')
                        missing_types = expected_types - self.session_data_types
                        if missing_types:
                            logging.info(f"Session {self.current_session} missing data types: {missing_types}")
                            if self.current_session == -1:
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        continue
                                    elif data_type == 'key':
                                        self.update_plot_data('key', "0" * 128, current_time, x_ticks, length=128)
                                        self.last_session_data['key'] = "0" * 128
                                        logging.info(f"Initialized missing {data_type} to '{'0' * 128}' for session {self.current_session}")
                                    elif data_type == 'input_string' and self.mode == 'console':
                                        self.update_plot_data('input_string', "default_input", current_time, x_ticks)
                                        self.last_session_data['input_string'] = "default_input"
                                        logging.info(f"Initialized missing {data_type} to 'default_input' for session {self.current_session}")
                                    elif data_type != 'input_string':
                                        self.update_plot_data(data_type, 0, current_time, x_ticks, kbps=(data_type == 'kbps_data'))
                                        self.last_session_data[data_type] = 0
                                        logging.info(f"Initialized missing {data_type} to 0 for session {self.current_session}")
                            else:
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        for value in self.last_session_data[data_type]:
                                            self.update_plot_data(data_type, value, current_time, x_ticks)
                                    elif self.last_session_data[data_type] is not None and data_type != 'input_string':
                                        if data_type == 'key':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, length=len(self.last_session_data[data_type]))
                                        elif data_type == 'kbps_data':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, kbps=True)
                                        else:
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks)
                                    elif data_type == 'input_string' and self.mode == 'console':
                                        self.update_plot_data('input_string', self.last_session_data['input_string'], current_time, x_ticks)
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                        self.last_session_data["timestamp_spd1"] = []
                        self.last_session_data["timestamp_spd2"] = []
                    continue

                self.session_data_types.add(data['type'])
                self.update_plot_data(data['type'], data.get('value', data.get('kbps')), current_time, x_ticks, length=data.get('length'), kbps='kbps' in data)

        except Empty:
            pass

    def update_plot_data(self, data_type, value, current_time, x_ticks, length=None, kbps=False):
        if data_type == 'timestamp_spd1':
            timestamp_ps = int(value)
            logging.debug(f"SPD1 timestamp: {timestamp_ps}")
            partition1 = min((timestamp_ps // 100) % 40, 39)
            self.hist_data_all[partition1] += 1
            self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
            self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
            self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
            self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
            logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

            self.hist_data_tab[partition1] += 1
            self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
            self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
            self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
            self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")
            self.last_session_data["timestamp_spd1"].append(timestamp_ps)

        elif data_type == 'timestamp_spd2':
            timestamp_ps = int(value)
            logging.debug(f"SPD2 timestamp: {timestamp_ps}")
            partition2 = min((timestamp_ps // 100) % 40, 39)
            self.hist2_data_all[partition2] += 1
            self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
            self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
            self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
            self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
            logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

            self.hist2_data_tab[partition2] += 1
            self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
            self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
            self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
            self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")
            self.last_session_data["timestamp_spd2"].append(timestamp_ps)

        elif data_type == 'qber':
            qber_val = float(value)
            logging.debug(f"QBER: {qber_val}")
            self.qber_x_all.append(current_time)
            self.qber_y_all.append(qber_val)
            while self.qber_x_all and self.qber_x_all[0] < current_time - 60:
                self.qber_x_all.pop(0)
                self.qber_y_all.pop(0)
            self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
            self.qber_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_all.getAxis('bottom').setTicks([x_ticks])
            qber_lower = math.floor(qber_val) - 10
            qber_upper = math.floor(qber_val) + 10
            if qber_lower < 0:
                qber_lower = 0
                qber_upper = 20
            qber_ticks = list(range(int(qber_lower), int(qber_upper) + 1, 2))
            self.qber_plot_all.setYRange(qber_lower, qber_upper)
            self.qber_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

            self.qber_x_tab.append(current_time)
            self.qber_y_tab.append(qber_val)
            while self.qber_x_tab and self.qber_x_tab[0] < current_time - 60:
                self.qber_x_tab.pop(0)
                self.qber_y_tab.pop(0)
            self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
            self.qber_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.qber_plot_tab.setYRange(qber_lower, qber_upper)
            self.qber_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])
            self.last_session_data["qber"] = qber_val

        elif data_type == 'kbps_data':
            kbps = float(value)
            logging.debug(f"KBPS: {kbps}")
            self.kbps_x_all.append(current_time)
            self.kbps_y_all.append(kbps)
            while self.kbps_x_all and self.kbps_x_all[0] < current_time - 60:
                self.kbps_x_all.pop(0)
                self.kbps_y_all.pop(0)
            self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
            self.kbps_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.kbps_x_tab.append(current_time)
            self.kbps_y_tab.append(kbps)
            while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 60:
                self.kbps_x_tab.pop(0)
                self.kbps_y_tab.pop(0)
            self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
            self.kbps_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["kbps_data"] = kbps

        elif data_type == 'key':
            logging.debug(f"Key (length {length}): {value[:40]}...")
            self.key_display.setText(f"Key (Session {self.current_session}, Length {length}): {value[:40]}...")
            self.key_display.setToolTip(value)
            self.last_session_data["key"] = value

        elif data_type == 'visibility':
            vis_val = float(value)
            logging.debug(f"Visibility: {vis_val}")
            self.visibility_x_all.append(current_time)
            self.visibility_y_all.append(vis_val)
            while self.visibility_x_all and self.visibility_x_all[0] < current_time - 60:
                self.visibility_x_all.pop(0)
                self.visibility_y_all.pop(0)
            self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
            self.visibility_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_all.getAxis('bottom').setTicks([x_ticks])
            vis_lower = math.floor(vis_val * 10) / 10 - 0.1
            vis_upper = math.floor(vis_val * 10) / 10 + 0.1
            if vis_lower < 0:
                vis_lower = 0
                vis_upper = 0.2
            vis_ticks = [vis_lower + i * 0.02 for i in range(int((vis_upper - vis_lower) / 0.02) + 1)]
            self.visibility_plot_all.setYRange(vis_lower, vis_upper)
            self.visibility_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

            self.visibility_x_tab.append(current_time)
            self.visibility_y_tab.append(vis_val)
            while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 60:
                self.visibility_x_tab.pop(0)
                self.visibility_y_tab.pop(0)
            self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
            self.visibility_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.visibility_plot_tab.setYRange(vis_lower, vis_upper)
            self.visibility_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])
            self.last_session_data["visibility"] = vis_val

        elif data_type == 'spd1_decaystate':
            spd1_val = float(value)
            logging.debug(f"SPD1 Decay: {spd1_val}")
            self.spd1_x_all.append(current_time)
            self.spd1_y_all.append(spd1_val)
            while self.spd1_x_all and self.spd1_x_all[0] < current_time - 60:
                self.spd1_x_all.pop(0)
                self.spd1_y_all.pop(0)
            self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
            self.spd1_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.spd1_x_tab.append(current_time)
            self.spd1_y_tab.append(spd1_val)
            while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 60:
                self.spd1_x_tab.pop(0)
                self.spd1_y_tab.pop(0)
            self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
            self.spd1_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["spd1_decaystate"] = spd1_val

        elif data_type == 'input_string':
            logging.debug(f"Input String: {value}")
            self.last_session_data["input_string"] = value
            if self.mode == 'console':
                self.input_display.setText(f"Input: {value[:40]}..." if len(value) > 40 else f"Input: {value}")

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        input_string = self.input_field.text() or "default_input" if self.mode == "console" else None
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0, input_string=input_string)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None,
            "input_string": None
        }
        self.key_display.setText(f"Key (None): None")
        self.input_display.setText("Input: None")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position, input_string=None)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept()'''
        
        
        
        
import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSpacerItem, QLabel, QTabWidget, QGridLayout, QSizePolicy, QStatusBar, QLineEdit
)
from PyQt6.QtCore import QTimer, Qt
from queue import Queue, Empty
import pyqtgraph as pg
import time
import logging
from data_processor import DataProcessor
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QWidget):
    def __init__(self, data_queue, processor):
        super().__init__()
        self.setObjectName("mainWindow")
        self.data_queue = data_queue
        self.processor = processor
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.mode = self.processor.mode
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.init_ui()
        self.setup_plots()
        self.setup_timer()
        self.setup_marquee()

    def init_ui(self):
        self.setWindowTitle("Quantum Key Distribution Analyzer")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QWidget#mainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A3C34, stop:1 #0A2522);
                color: #E0F7FA;
                font-family: Roboto, Arial, sans-serif;
            }
            QTabWidget::pane {
                background: #1A3C34;
                border: 2px solid #4DD0E1;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #263238;
                color: #80DEEA;
                padding: 10px 25px;
                font-size: 14pt;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #00ACC1;
                color: #E0F7FA;
                border-bottom: 3px solid #B2EBF2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ACC1, stop:1 #26C6DA);
                color: #E0F7FA;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #4DD0E1;
            }
            QPushButton#stopButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF5350, stop:1 #F06292);
            }
            QPushButton#modeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7CB342, stop:1 #9CCC65);
            }
            QPushButton#resumeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB300, stop:1 #FFCA28);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #26C6DA, stop:1 #4DD0E1);
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E53935, stop:1 #EC407A);
            }
            QPushButton#modeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BC34A, stop:1 #AED581);
            }
            QPushButton#resumeButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFA000, stop:1 #FFB300);
            }
            pg.PlotWidget {
                border: 2px solid #4DD0E1;
                background: #ECEFF1;
                border-radius: 6px;
            }
            QLabel#marqueeLabel {
                color: #B2EBF2;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                text-align: center;
                background: #263238;
                border-radius: 6px;
            }
            QLabel#keyDisplay {
                color: #E0F7FA;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                background: #263238;
                border-radius: 6px;
            }
            QLineEdit#inputField {
                background: #263238;
                color: #E0F7FA;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QWidget#marqueeContainer, QWidget#buttonContainer, QWidget#keyContainer {
                background: #263238;
                border: 1px solid #4DD0E1;
                border-radius: 6px;
                padding: 8px;
            }
            QStatusBar {
                background: #263238;
                color: #B2EBF2;
                font-size: 14px;
                padding: 5px;
            }
        """)

        main_layout = QVBoxLayout()

        marquee_container = QWidget(objectName="marqueeContainer")
        marquee_layout = QHBoxLayout()
        marquee_layout.addStretch()
        self.marquee_label = QLabel("Quantum Key Distribution Output Analyzer   ", objectName="marqueeLabel")
        marquee_layout.addWidget(self.marquee_label)
        marquee_layout.addStretch()
        marquee_container.setLayout(marquee_layout)
        main_layout.addWidget(marquee_container)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { margin: 10px; }")

        all_tab = QWidget()
        all_layout = QVBoxLayout()

        hist_container_all = QHBoxLayout()
        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.hist_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        hist_container_all.addWidget(self.hist_plot_all)

        self.hist2_plot_all = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        hist_container_all.addWidget(self.hist2_plot_all)

        hist_container_all.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        all_layout.addLayout(hist_container_all)
        all_layout.setStretchFactor(hist_container_all, 3)

        bottom_layout_all = QGridLayout()
        bottom_layout_all.setSpacing(10)

        self.qber_plot_all = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        bottom_layout_all.addWidget(self.qber_plot_all, 0, 0)

        self.kbps_plot_all = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        bottom_layout_all.addWidget(self.kbps_plot_all, 0, 1)

        self.visibility_plot_all = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        bottom_layout_all.addWidget(self.visibility_plot_all, 1, 0)

        self.spd1_plot_all = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        bottom_layout_all.addWidget(self.spd1_plot_all, 1, 1)

        all_layout.addLayout(bottom_layout_all)
        all_layout.setStretchFactor(bottom_layout_all, 2)
        all_tab.setLayout(all_layout)
        tab_widget.addTab(all_tab, "Overview")

        hist_tab = QWidget()
        hist_tab_layout = QHBoxLayout()
        hist_tab_layout.addStretch()
        self.hist_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD1)", objectName="histPlot")
        self.hist_plot_tab.setFixedSize(700, 400)
        hist_tab_layout.addWidget(self.hist_plot_tab)
        hist_tab_layout.addStretch()
        hist_tab.setLayout(hist_tab_layout)
        tab_widget.addTab(hist_tab, "SPD1 Histogram")

        hist2_tab = QWidget()
        hist2_tab_layout = QHBoxLayout()
        hist2_tab_layout.addStretch()
        self.hist2_plot_tab = pg.PlotWidget(title="Timestamp Histogram (SPD2)", objectName="hist2Plot")
        self.hist2_plot_tab.setFixedSize(700, 400)
        hist2_tab_layout.addWidget(self.hist2_plot_tab)
        hist2_tab_layout.addStretch()
        hist2_tab.setLayout(hist2_tab_layout)
        tab_widget.addTab(hist2_tab, "SPD2 Histogram")

        qber_tab = QWidget()
        qber_tab_layout = QHBoxLayout()
        qber_tab_layout.addStretch()
        self.qber_plot_tab = pg.PlotWidget(title="Quantum Bit Error Rate", objectName="qberPlot")
        self.qber_plot_tab.setFixedSize(700, 400)
        qber_tab_layout.addWidget(self.qber_plot_tab)
        qber_tab_layout.addStretch()
        qber_tab.setLayout(qber_tab_layout)
        tab_widget.addTab(qber_tab, "QBER")

        kbps_tab = QWidget()
        kbps_tab_layout = QHBoxLayout()
        kbps_tab_layout.addStretch()
        self.kbps_plot_tab = pg.PlotWidget(title="Throughput (kbps)", objectName="kbpsPlot")
        self.kbps_plot_tab.setFixedSize(700, 400)
        kbps_tab_layout.addWidget(self.kbps_plot_tab)
        kbps_tab_layout.addStretch()
        kbps_tab.setLayout(kbps_tab_layout)
        tab_widget.addTab(kbps_tab, "Throughput")

        visibility_tab = QWidget()
        visibility_tab_layout = QHBoxLayout()
        visibility_tab_layout.addStretch()
        self.visibility_plot_tab = pg.PlotWidget(title="Visibility Ratio", objectName="visibilityPlot")
        self.visibility_plot_tab.setFixedSize(700, 400)
        visibility_tab_layout.addWidget(self.visibility_plot_tab)
        visibility_tab_layout.addStretch()
        visibility_tab.setLayout(visibility_tab_layout)
        tab_widget.addTab(visibility_tab, "Visibility")

        spd1_tab = QWidget()
        spd1_tab_layout = QHBoxLayout()
        spd1_tab_layout.addStretch()
        self.spd1_plot_tab = pg.PlotWidget(title="SPD1 Decoy Randomness", objectName="spd1Plot")
        self.spd1_plot_tab.setFixedSize(700, 400)
        spd1_tab_layout.addWidget(self.spd1_plot_tab)
        spd1_tab_layout.addStretch()
        spd1_tab.setLayout(spd1_tab_layout)
        tab_widget.addTab(spd1_tab, "SPD1 Decoy")

        main_layout.addWidget(tab_widget)

        key_container = QWidget(objectName="keyContainer")
        key_layout = QHBoxLayout()
        key_layout.addStretch()
        self.key_display = QLabel("Key (None): None", objectName="keyDisplay")
        self.key_display.setToolTip("Full key available on hover")
        key_layout.addWidget(self.key_display)
        key_layout.addStretch()
        key_container.setLayout(key_layout)
        main_layout.addWidget(key_container)

        button_container = QWidget(objectName="buttonContainer")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.input_label = QLabel("Input String:", objectName="marqueeLabel")
        self.input_label.setVisible(self.mode == "console")
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Enter input string for QKD simulation")
        self.input_field.setMinimumWidth(200)
        self.input_field.setVisible(self.mode == "console")
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.mode_button = QPushButton(f"Mode: {self.mode.capitalize()}")
        self.mode_button.setObjectName("modeButton")
        self.start_button.clicked.connect(self.start_processor)
        self.stop_button.clicked.connect(self.stop_processor)
        self.resume_button.clicked.connect(self.resume_processor)
        self.mode_button.clicked.connect(self.toggle_mode)
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        button_layout.addWidget(self.input_label)
        button_layout.addWidget(self.input_field)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def toggle_mode(self):
        self.processor.stop()
        self.mode = "file" if self.mode == "console" else "console"
        self.file_position = 0
        self.current_session = -1
        input_string = self.input_field.text() or "default_input" if self.mode == "console" else None
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position, input_string=input_string)
        self.mode_button.setText(f"Mode: {self.mode.capitalize()}")
        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: None")
        self.resume_button.setEnabled(False)
        self.resume_button.setVisible(self.mode == "file")
        self.input_label.setVisible(self.mode == "console")
        self.input_field.setVisible(self.mode == "console")
        logging.info(f"Switched to {self.mode} mode")

    def setup_marquee(self):
        self.marquee_timer = QTimer(self)
        self.marquee_timer.setInterval(100)
        self.marquee_timer.timeout.connect(self.update_marquee)
        self.marquee_timer.start()

    def update_marquee(self):
        text = self.marquee_label.text()
        text = text[1:] + text[0]
        self.marquee_label.setText(text)

    def setup_plots(self):
        pg.setConfigOptions(antialias=True)

        def configure_line_plot(plot_widget, y_label, title, x_range=(0, 60), y_range=None):
            plot_widget.setLabel('bottom', 'Time (s)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', y_label, color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)
            if y_range:
                plot_widget.setYRange(*y_range)
            plot_widget.getAxis('bottom').setTicks([[(i, str(i)) for i in range(0, 61, 5)]])
            plot_widget.tooltip = pg.TextItem(text="", anchor=(0, 0), color='#E0F7FA')
            plot_widget.addItem(plot_widget.tooltip)
            plot_widget.tooltip.hide()
            plot_widget.getPlotItem().scene().sigMouseMoved.connect(lambda pos: self.on_mouse_moved(plot_widget, pos))

        def configure_histogram_plot(plot_widget, title, brush_color, x_range=(0, 4000)):
            plot_widget.setLabel('bottom', 'Time (ps)', color='#E0F7FA', size='12pt')
            plot_widget.setLabel('left', 'Count', color='#E0F7FA', size='12pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.getAxis('bottom').setTextPen('#E0F7FA')
            plot_widget.getAxis('left').setTextPen('#E0F7FA')
            plot_widget.setTitle(title, color='#E0F7FA', size='14pt')
            plot_widget.setXRange(*x_range)

        self.hist_data_all = np.zeros(40)
        self.hist_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_all, width=100, brush='#FF6F61')
        self.hist_plot_all.addItem(self.hist_bar_all)
        configure_histogram_plot(self.hist_plot_all, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_all = []
        bar_centers = np.arange(40)*100 + 50
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_all[i] + 0.5)
            self.hist_plot_all.addItem(label)
            self.hist_labels_all.append(label)

        self.hist2_data_all = np.zeros(40)
        self.hist2_bar_all = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_all, width=100, brush='#FFCA28')
        self.hist2_plot_all.addItem(self.hist2_bar_all)
        configure_histogram_plot(self.hist2_plot_all, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_all = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_all[i] + 0.5)
            self.hist2_plot_all.addItem(label)
            self.hist2_labels_all.append(label)

        self.hist_data_tab = np.zeros(40)
        self.hist_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist_data_tab, width=100, brush='#FF6F61')
        self.hist_plot_tab.addItem(self.hist_bar_tab)
        configure_histogram_plot(self.hist_plot_tab, "Timestamp Histogram (SPD1)", '#FF6F61')
        self.hist_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist_data_tab[i] + 0.5)
            self.hist_plot_tab.addItem(label)
            self.hist_labels_tab.append(label)

        self.hist2_data_tab = np.zeros(40)
        self.hist2_bar_tab = pg.BarGraphItem(x0=np.arange(40)*100, height=self.hist2_data_tab, width=100, brush='#FFCA28')
        self.hist2_plot_tab.addItem(self.hist2_bar_tab)
        configure_histogram_plot(self.hist2_plot_tab, "Timestamp Histogram (SPD2)", '#FFCA28')
        self.hist2_labels_tab = []
        for i in range(40):
            label = pg.TextItem(text="0", color='#E0F7FA', anchor=(0.5, 1.0))
            label.setPos(bar_centers[i], self.hist2_data_tab[i] + 0.5)
            self.hist2_plot_tab.addItem(label)
            self.hist2_labels_tab.append(label)

        self.qber_x_all = []
        self.qber_y_all = []
        self.qber_line_all = self.qber_plot_all.plot(self.qber_x_all, self.qber_y_all, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_all, 'QBER (%)', "Quantum Bit Error Rate")

        self.qber_x_tab = []
        self.qber_y_tab = []
        self.qber_line_tab = self.qber_plot_tab.plot(self.qber_x_tab, self.qber_y_tab, pen=pg.mkPen('#40C4FF', width=2), symbol='o', symbolBrush='#40C4FF', symbolSize=8)
        configure_line_plot(self.qber_plot_tab, 'QBER (%)', "Quantum Bit Error Rate")

        self.kbps_x_all = []
        self.kbps_y_all = []
        self.kbps_line_all = self.kbps_plot_all.plot(self.kbps_x_all, self.kbps_y_all, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_all, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.kbps_x_tab = []
        self.kbps_y_tab = []
        self.kbps_line_tab = self.kbps_plot_tab.plot(self.kbps_x_tab, self.kbps_y_tab, pen=pg.mkPen('#AB47BC', width=2), symbol='o', symbolBrush='#AB47BC', symbolSize=8)
        configure_line_plot(self.kbps_plot_tab, 'kbps', "Throughput (kbps)", y_range=(0, 10))

        self.visibility_x_all = []
        self.visibility_y_all = []
        self.visibility_line_all = self.visibility_plot_all.plot(self.visibility_x_all, self.visibility_y_all, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_all, 'Ratio', "Visibility Ratio")

        self.visibility_x_tab = []
        self.visibility_y_tab = []
        self.visibility_line_tab = self.visibility_plot_tab.plot(self.visibility_x_tab, self.visibility_y_tab, pen=pg.mkPen('#26A69A', width=2), symbol='o', symbolBrush='#26A69A', symbolSize=8)
        configure_line_plot(self.visibility_plot_tab, 'Ratio', "Visibility Ratio")

        self.spd1_x_all = []
        self.spd1_y_all = []
        self.spd1_line_all = self.spd1_plot_all.plot(self.spd1_x_all, self.spd1_y_all, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_all, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

        self.spd1_x_tab = []
        self.spd1_y_tab = []
        self.spd1_line_tab = self.spd1_plot_tab.plot(self.spd1_x_tab, self.spd1_y_tab, pen=pg.mkPen('#FF6F61', width=2), symbol='o', symbolBrush='#FF6F61', symbolSize=8)
        configure_line_plot(self.spd1_plot_tab, 'Value', "SPD1 Decoy Randomness", y_range=(0, 1))

    def on_mouse_moved(self, plot_widget, pos):
        vb = plot_widget.getViewBox()
        scene_pos = vb.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()

        if plot_widget == self.qber_plot_all:
            x_data, y_data = self.qber_x_all, self.qber_y_all
            y_label = "QBER (%)"
        elif plot_widget == self.qber_plot_tab:
            x_data, y_data = self.qber_x_tab, self.qber_y_tab
            y_label = "QBER (%)"
        elif plot_widget == self.kbps_plot_all:
            x_data, y_data = self.kbps_x_all, self.kbps_y_all
            y_label = "kbps"
        elif plot_widget == self.kbps_plot_tab:
            x_data, y_data = self.kbps_x_tab, self.kbps_y_tab
            y_label = "kbps"
        elif plot_widget == self.visibility_plot_all:
            x_data, y_data = self.visibility_x_all, self.visibility_y_all
            y_label = "Ratio"
        elif plot_widget == self.visibility_plot_tab:
            x_data, y_data = self.visibility_x_tab, self.visibility_y_tab
            y_label = "Ratio"
        elif plot_widget == self.spd1_plot_all:
            x_data, y_data = self.spd1_x_all, self.spd1_y_all
            y_label = "Value"
        elif plot_widget == self.spd1_plot_tab:
            x_data, y_data = self.spd1_x_tab, self.spd1_y_tab
            y_label = "Value"
        else:
            plot_widget.tooltip.hide()
            return

        if not x_data:
            plot_widget.tooltip.hide()
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)
        distances = np.sqrt((x_array - x) ** 2 + (y_array - y) ** 2)
        closest_idx = np.argmin(distances)
        if distances[closest_idx] < 0.5:
            x_val, y_val = x_data[closest_idx], y_data[closest_idx]
            plot_widget.tooltip.setText(f"Time: {x_val:.2f} s\n{y_label}: {y_val:.4f}")
            plot_widget.tooltip.setPos(x_val, y_val)
            plot_widget.tooltip.show()
        else:
            plot_widget.tooltip.hide()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_plots)

    def update_plots(self):
        try:
            for _ in range(50):
                data = self.data_queue.get_nowait()
                current_time = time.time() - self.start_time
                logging.debug(f"Processing data: {data}")

                x_min = max(0, current_time - 60)
                x_start = math.floor(x_min / 5) * 5
                x_ticks = [(i, f"{i:.0f}") for i in range(x_start, int(current_time) + 5, 5)]

                line_plots = [
                    (self.qber_plot_all, self.qber_x_all, self.qber_y_all, self.qber_line_all),
                    (self.qber_plot_tab, self.qber_x_tab, self.qber_y_tab, self.qber_line_tab),
                    (self.kbps_plot_all, self.kbps_x_all, self.kbps_y_all, self.kbps_line_all),
                    (self.kbps_plot_tab, self.kbps_x_tab, self.kbps_y_tab, self.kbps_line_tab),
                    (self.visibility_plot_all, self.visibility_x_all, self.visibility_y_all, self.visibility_line_all),
                    (self.visibility_plot_tab, self.visibility_x_tab, self.visibility_y_tab, self.visibility_line_tab),
                    (self.spd1_plot_all, self.spd1_x_all, self.spd1_y_all, self.spd1_line_all),
                    (self.spd1_plot_tab, self.spd1_x_tab, self.spd1_y_tab, self.spd1_line_tab)
                ]

                if data['type'] == 'session_number':
                    new_session = data['value']
                    if new_session != self.current_session:
                        expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                        if new_session % 2 == 0:
                            expected_types.add('key')
                        else:
                            expected_types.add('kbps_data')
                        missing_types = expected_types - self.session_data_types
                        if missing_types:
                            logging.info(f"Session {self.current_session} missing data types: {missing_types}")
                            if self.current_session == -1:
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        continue
                                    elif data_type == 'key':
                                        self.update_plot_data('key', "0" * 128, current_time, x_ticks, length=128)
                                        self.last_session_data['key'] = "0" * 128
                                        logging.info(f"Initialized missing {data_type} to '{'0' * 128}' for session {self.current_session}")
                                    else:
                                        self.update_plot_data(data_type, 0, current_time, x_ticks, kbps=(data_type == 'kbps_data'))
                                        self.last_session_data[data_type] = 0
                                        logging.info(f"Initialized missing {data_type} to 0 for session {self.current_session}")
                            else:
                                for data_type in missing_types:
                                    if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                        for value in self.last_session_data[data_type]:
                                            self.update_plot_data(data_type, value, current_time, x_ticks)
                                    elif self.last_session_data[data_type] is not None:
                                        if data_type == 'key':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, length=len(self.last_session_data[data_type]))
                                        elif data_type == 'kbps_data':
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks, kbps=True)
                                        else:
                                            self.update_plot_data(data_type, self.last_session_data[data_type], current_time, x_ticks)
                        self.current_session = new_session
                        self.session_data_types = set()
                        self.status_bar.showMessage(f"Mode: {self.mode.capitalize()} | Session: {self.current_session}")
                        self.last_session_data["timestamp_spd1"] = []
                        self.last_session_data["timestamp_spd2"] = []
                    continue

                self.session_data_types.add(data['type'])
                self.update_plot_data(data['type'], data.get('value', data.get('kbps')), current_time, x_ticks, length=data.get('length'), kbps='kbps' in data)

        except Empty:
            pass

    def update_plot_data(self, data_type, value, current_time, x_ticks, length=None, kbps=False):
        if data_type == 'timestamp_spd1':
            timestamp_ps = int(value)
            logging.debug(f"SPD1 timestamp: {timestamp_ps}")
            partition1 = min((timestamp_ps // 100) % 40, 39)
            self.hist_data_all[partition1] += 1
            self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
            self.hist_labels_all[partition1].setText(str(int(self.hist_data_all[partition1])))
            self.hist_labels_all[partition1].setPos(partition1*100 + 50, self.hist_data_all[partition1] + 0.5)
            self.hist_plot_all.setYRange(0, max(self.hist_data_all.max() * 1.2, 10))
            logging.debug(f"SPD1 histogram data: {self.hist_data_all}")

            self.hist_data_tab[partition1] += 1
            self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
            self.hist_labels_tab[partition1].setText(str(int(self.hist_data_tab[partition1])))
            self.hist_labels_tab[partition1].setPos(partition1*100 + 50, self.hist_data_tab[partition1] + 0.5)
            self.hist_plot_tab.setYRange(0, max(self.hist_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD1 tab histogram data: {self.hist_data_tab}")
            self.last_session_data["timestamp_spd1"].append(timestamp_ps)

        elif data_type == 'timestamp_spd2':
            timestamp_ps = int(value)
            logging.debug(f"SPD2 timestamp: {timestamp_ps}")
            partition2 = min((timestamp_ps // 100) % 40, 39)
            self.hist2_data_all[partition2] += 1
            self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
            self.hist2_labels_all[partition2].setText(str(int(self.hist2_data_all[partition2])))
            self.hist2_labels_all[partition2].setPos(partition2*100 + 50, self.hist2_data_all[partition2] + 0.5)
            self.hist2_plot_all.setYRange(0, max(self.hist2_data_all.max() * 1.2, 10))
            logging.debug(f"SPD2 histogram data: {self.hist2_data_all}")

            self.hist2_data_tab[partition2] += 1
            self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
            self.hist2_labels_tab[partition2].setText(str(int(self.hist2_data_tab[partition2])))
            self.hist2_labels_tab[partition2].setPos(partition2*100 + 50, self.hist2_data_tab[partition2] + 0.5)
            self.hist2_plot_tab.setYRange(0, max(self.hist2_data_tab.max() * 1.2, 10))
            logging.debug(f"SPD2 tab histogram data: {self.hist2_data_tab}")
            self.last_session_data["timestamp_spd2"].append(timestamp_ps)

        elif data_type == 'qber':
            qber_val = float(value)
            logging.debug(f"QBER: {qber_val}")
            self.qber_x_all.append(current_time)
            self.qber_y_all.append(qber_val)
            while self.qber_x_all and self.qber_x_all[0] < current_time - 60:
                self.qber_x_all.pop(0)
                self.qber_y_all.pop(0)
            self.qber_line_all.setData(self.qber_x_all, self.qber_y_all)
            self.qber_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_all.getAxis('bottom').setTicks([x_ticks])
            qber_lower = math.floor(qber_val) - 10
            qber_upper = math.floor(qber_val) + 10
            if qber_lower < 0:
                qber_lower = 0
                qber_upper = 20
            qber_ticks = list(range(int(qber_lower), int(qber_upper) + 1, 2))
            self.qber_plot_all.setYRange(qber_lower, qber_upper)
            self.qber_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])

            self.qber_x_tab.append(current_time)
            self.qber_y_tab.append(qber_val)
            while self.qber_x_tab and self.qber_x_tab[0] < current_time - 60:
                self.qber_x_tab.pop(0)
                self.qber_y_tab.pop(0)
            self.qber_line_tab.setData(self.qber_x_tab, self.qber_y_tab)
            self.qber_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.qber_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.qber_plot_tab.setYRange(qber_lower, qber_upper)
            self.qber_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in qber_ticks]])
            self.last_session_data["qber"] = qber_val

        elif data_type == 'kbps_data':
            kbps = float(value)
            logging.debug(f"KBPS: {kbps}")
            self.kbps_x_all.append(current_time)
            self.kbps_y_all.append(kbps)
            while self.kbps_x_all and self.kbps_x_all[0] < current_time - 60:
                self.kbps_x_all.pop(0)
                self.kbps_y_all.pop(0)
            self.kbps_line_all.setData(self.kbps_x_all, self.kbps_y_all)
            self.kbps_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.kbps_x_tab.append(current_time)
            self.kbps_y_tab.append(kbps)
            while self.kbps_x_tab and self.kbps_x_tab[0] < current_time - 60:
                self.kbps_x_tab.pop(0)
                self.kbps_y_tab.pop(0)
            self.kbps_line_tab.setData(self.kbps_x_tab, self.kbps_y_tab)
            self.kbps_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.kbps_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["kbps_data"] = kbps

        elif data_type == 'key':
            logging.debug(f"Key (length {length}): {value[:40]}...")
            self.key_display.setText(f"Key (Session {self.current_session}, Length {length}): {value[:40]}...")
            self.key_display.setToolTip(value)
            self.last_session_data["key"] = value

        elif data_type == 'visibility':
            vis_val = float(value)
            logging.debug(f"Visibility: {vis_val}")
            self.visibility_x_all.append(current_time)
            self.visibility_y_all.append(vis_val)
            while self.visibility_x_all and self.visibility_x_all[0] < current_time - 60:
                self.visibility_x_all.pop(0)
                self.visibility_y_all.pop(0)
            self.visibility_line_all.setData(self.visibility_x_all, self.visibility_y_all)
            self.visibility_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_all.getAxis('bottom').setTicks([x_ticks])
            vis_lower = math.floor(vis_val * 10) / 10 - 0.1
            vis_upper = math.floor(vis_val * 10) / 10 + 0.1
            if vis_lower < 0:
                vis_lower = 0
                vis_upper = 0.2
            vis_ticks = [vis_lower + i * 0.02 for i in range(int((vis_upper - vis_lower) / 0.02) + 1)]
            self.visibility_plot_all.setYRange(vis_lower, vis_upper)
            self.visibility_plot_all.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])

            self.visibility_x_tab.append(current_time)
            self.visibility_y_tab.append(vis_val)
            while self.visibility_x_tab and self.visibility_x_tab[0] < current_time - 60:
                self.visibility_x_tab.pop(0)
                self.visibility_y_tab.pop(0)
            self.visibility_line_tab.setData(self.visibility_x_tab, self.visibility_y_tab)
            self.visibility_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.visibility_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.visibility_plot_tab.setYRange(vis_lower, vis_upper)
            self.visibility_plot_tab.getAxis('left').setTicks([[(val, f"{val:.2f}") for val in vis_ticks]])
            self.last_session_data["visibility"] = vis_val

        elif data_type == 'spd1_decaystate':
            spd1_val = float(value)
            logging.debug(f"SPD1 Decay: {spd1_val}")
            self.spd1_x_all.append(current_time)
            self.spd1_y_all.append(spd1_val)
            while self.spd1_x_all and self.spd1_x_all[0] < current_time - 60:
                self.spd1_x_all.pop(0)
                self.spd1_y_all.pop(0)
            self.spd1_line_all.setData(self.spd1_x_all, self.spd1_y_all)
            self.spd1_plot_all.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_all.getAxis('bottom').setTicks([x_ticks])

            self.spd1_x_tab.append(current_time)
            self.spd1_y_tab.append(spd1_val)
            while self.spd1_x_tab and self.spd1_x_tab[0] < current_time - 60:
                self.spd1_x_tab.pop(0)
                self.spd1_y_tab.pop(0)
            self.spd1_line_tab.setData(self.spd1_x_tab, self.spd1_y_tab)
            self.spd1_plot_tab.setXRange(max(0, current_time - 60), current_time)
            self.spd1_plot_tab.getAxis('bottom').setTicks([x_ticks])
            self.last_session_data["spd1_decaystate"] = spd1_val

    def start_processor(self):
        logging.info("Starting processor")
        self.processor.stop()
        input_string = self.input_field.text() or "default_input" if self.mode == "console" else None
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=0, input_string=input_string)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.start_time = time.time()
        self.current_session = -1
        self.file_position = 0
        self.session_data_types = set()
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }
        self.key_display.setText(f"Key (None): None")
        self.hist_data_all.fill(0)
        self.hist_data_tab.fill(0)
        self.hist2_data_all.fill(0)
        self.hist2_data_tab.fill(0)
        self.hist_bar_all.setOpts(height=self.hist_data_all, brush='#FF6F61')
        self.hist_bar_tab.setOpts(height=self.hist_data_tab, brush='#FF6F61')
        self.hist2_bar_all.setOpts(height=self.hist2_data_all, brush='#FFCA28')
        self.hist2_bar_tab.setOpts(height=self.hist2_data_tab, brush='#FFCA28')
        self.qber_x_all.clear()
        self.qber_y_all.clear()
        self.qber_x_tab.clear()
        self.qber_y_tab.clear()
        self.kbps_x_all.clear()
        self.kbps_y_all.clear()
        self.kbps_x_tab.clear()
        self.kbps_y_tab.clear()
        self.visibility_x_all.clear()
        self.visibility_y_all.clear()
        self.visibility_x_tab.clear()
        self.visibility_y_tab.clear()
        self.spd1_x_all.clear()
        self.spd1_y_all.clear()
        self.spd1_x_tab.clear()
        self.spd1_y_tab.clear()
        self.qber_line_all.setData([], [])
        self.qber_line_tab.setData([], [])
        self.kbps_line_all.setData([], [])
        self.kbps_line_tab.setData([], [])
        self.visibility_line_all.setData([], [])
        self.visibility_line_tab.setData([], [])
        self.spd1_line_all.setData([], [])
        self.spd1_line_tab.setData([], [])
        self.timer.start()

    def stop_processor(self):
        logging.info("Stopping processor")
        self.processor.stop()
        if self.mode == "file":
            self.file_position = self.processor.get_file_position()
            logging.debug(f"Stopped with file_position: {self.file_position}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(self.mode == "file" and self.file_position > 0)
        self.mode_button.setEnabled(True)
        self.timer.stop()

    def resume_processor(self):
        if self.mode != "file":
            logging.warning("Resume is only available in file mode")
            return
        logging.info(f"Resuming processor at file position {self.file_position}, start_time={self.start_time}")
        self.processor.stop()
        self.processor = DataProcessor(self.data_queue, mode=self.mode, file_position=self.file_position, input_string=None)
        self.processor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.mode_button.setEnabled(False)
        self.timer.start()

    def closeEvent(self, event):
        logging.info("Closing window")
        self.processor.close()
        self.marquee_timer.stop()
        self.timer.stop()
        event.accept()