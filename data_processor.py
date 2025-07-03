#BELOW CODE HANDLES VARIABLE KEY SIZE
'''import subprocess
import os
from queue import Queue
import threading
import logging
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, data_queue: Queue, mode: str = "file", file_position: int = 0):
        self.data_queue = data_queue
        self.mode = mode
        self.process = None
        self.file = None
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.spd1_values_mode = False
        self.spd2_values_mode = False
        self.spd1_count = 0
        self.spd2_count = 0
        self.session_data_types = set()
        self.current_session = -1
        self.file_position = file_position
        self.c_program_path = os.path.join("build", "c_program.exe")
        self.output_file_path = os.path.join("build", "output.txt")

    def start(self):
        if not self.running:
            logging.info(f"Starting data processor in {self.mode} mode")
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.read_output)
            self.thread.daemon = True
            self.thread.start()

    def read_output(self):
        if self.mode == "console":
            try:
                self.process = subprocess.Popen(
                    self.c_program_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                while self.running and not self.stop_event.is_set():
                    line = self.process.stdout.readline().strip()
                    if not line and self.process.poll() is not None:
                        logging.info("Subprocess terminated")
                        self.running = False
                        break
                    if line:
                        logging.debug(f"Read line from console: {line}")
                        self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to start subprocess: {e}")
                self.running = False

        elif self.mode == "file":
            try:
                self.file = open(self.output_file_path, "r")
                logging.debug(f"Opened file at position {self.file_position}")
                if self.file_position > 0:
                    self.file.seek(self.file_position)
                    logging.debug(f"Seeking to file position {self.file_position}")
                while self.running and not self.stop_event.is_set():
                    line = self.file.readline().strip()
                    if not line:
                        if self.stop_event.is_set():
                            break
                        import time
                        time.sleep(0.5)
                        continue
                    logging.debug(f"Read line from file: {line}")
                    self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to read file: {e}")
                self.running = False
            finally:
                if self.file and not self.file.closed:
                    self.file.close()
                    self.file = None

    def parse_and_queue(self, line: str):
        try:
            if self.stop_event.is_set() and self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Stopped at file position {self.file_position}")
                self.file.close()
                self.file = None
                return

            if line.startswith("SESSION_NUMBER:"):
                new_session = int(line.split(':')[1])
                if new_session != self.current_session:
                    expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                    if new_session % 2 == 0:
                        expected_types.add('key')
                    else:
                        expected_types.add('kbps_data')
                    missing_types = expected_types - self.session_data_types
                    if missing_types and self.current_session != -1:
                        logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                    self.current_session = new_session
                    self.spd1_values_mode = False
                    self.spd2_values_mode = False
                    self.spd1_count = 0
                    self.spd2_count = 0
                    self.session_data_types = set()
                    self.data_queue.put({"type": "session_number", "value": new_session})
                logging.debug(f"Current file position after session: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD1_VALUES:":
                self.spd1_values_mode = True
                self.spd2_values_mode = False
                self.spd1_count = 0
                logging.debug(f"Current file position after SPD1_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD2_VALUES:":
                self.spd1_values_mode = False
                self.spd2_values_mode = True
                self.spd2_count = 0
                logging.debug(f"Current file position after SPD2_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd1_values_mode and self.spd1_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd1", "value": timestamp})
                self.spd1_count += 1
                self.session_data_types.add("timestamp_spd1")
                if self.spd1_count == 40:
                    logging.info(f"Completed queuing 40 SPD1 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD1: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd2_values_mode and self.spd2_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd2", "value": timestamp})
                self.spd2_count += 1
                self.session_data_types.add("timestamp_spd2")
                if self.spd2_count == 40:
                    logging.info(f"Completed queuing 40 SPD2 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD2: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("DECOY_STATE_RANDOMNESS_AT_SPD1:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "spd1_decaystate", "value": value})
                self.session_data_types.add("spd1_decaystate")
                logging.debug(f"Current file position after spd1_decaystate: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("VISIBILITY_RATIO_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "visibility", "value": value})
                self.session_data_types.add("visibility")
                logging.debug(f"Current file position after visibility: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("SPD1_QBER_VALUE_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "qber", "value": value})
                self.session_data_types.add("qber")
                logging.debug(f"Current file position after qber: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:"):
                logging.debug(f"Current file position after key_bits_length: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("KEY_BITS:"):
                key_match = re.match(r"KEY_BITS:([01]{128,})", line)
                if key_match:
                    key = key_match.group(1)
                    self.data_queue.put({"type": "key", "value": key, "length": len(key)})
                    self.session_data_types.add("key")
                    logging.debug(f"Queued key (length {len(key)}): {key[:40]}... for session {self.current_session}")
                    logging.debug(f"Current file position after key: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                else:
                    logging.error(f"Invalid key format: {line}")
                return

            if line.startswith("KEY_RATE_PER_SECOND_IS:"):
                kbps = float(line.split(':')[1])
                self.data_queue.put({"type": "kbps_data", "kbps": kbps})
                self.session_data_types.add("kbps_data")
                logging.debug(f"Queued kbps: {kbps} for session {self.current_session}")
                logging.debug(f"Current file position after kbps: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

        except Exception as e:
            logging.error(f"Error parsing line '{line}': {e}")

    def stop(self):
        if self.running:
            logging.info("Stopping data processor")
            self.running = False
            self.stop_event.set()
            if self.mode == "console" and self.process:
                self.process.kill()
                self.process = None
            elif self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Saved file position: {self.file_position}")
                self.file.close()
                self.file = None
            if self.thread:
                self.thread.join(timeout=0.1)
                self.thread = None

    def close(self):
        self.stop()
        if self.mode == "console" and self.process:
            logging.info("Closing data processor")
            self.process.stdout.close()
            self.process.stderr.close()
            self.process = None

    def get_file_position(self):
        return self.file_position'''
        
'''       
#BELOW IS FOR PLOTTING PREVIOUS SESSION DATA IF DATA IN CURRENT SESSION IS MISSING
import subprocess
import os
from queue import Queue
import threading
import logging
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, data_queue: Queue, mode: str = "file", file_position: int = 0):
        self.data_queue = data_queue
        self.mode = mode
        self.process = None
        self.file = None
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.spd1_values_mode = False
        self.spd2_values_mode = False
        self.spd1_count = 0
        self.spd2_count = 0
        self.session_data_types = set()
        self.current_session = -1
        self.file_position = file_position
        self.c_program_path = os.path.join("build", "c_program.exe")
        self.output_file_path = os.path.join("build", "output.txt")
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }

    def start(self):
        if not self.running:
            logging.info(f"Starting data processor in {self.mode} mode")
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.read_output)
            self.thread.daemon = True
            self.thread.start()

    def read_output(self):
        if self.mode == "console":
            try:
                self.process = subprocess.Popen(
                    self.c_program_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                while self.running and not self.stop_event.is_set():
                    line = self.process.stdout.readline().strip()
                    if not line and self.process.poll() is not None:
                        logging.info("Subprocess terminated")
                        self.running = False
                        break
                    if line:
                        logging.debug(f"Read line from console: {line}")
                        self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to start subprocess: {e}")
                self.running = False

        elif self.mode == "file":
            try:
                self.file = open(self.output_file_path, "r")
                logging.debug(f"Opened file at position {self.file_position}")
                if self.file_position > 0:
                    self.file.seek(self.file_position)
                    logging.debug(f"Seeking to file position {self.file_position}")
                while self.running and not self.stop_event.is_set():
                    line = self.file.readline().strip()
                    if not line:
                        if self.stop_event.is_set():
                            break
                        import time
                        time.sleep(0.5)
                        continue
                    logging.debug(f"Read line from file: {line}")
                    self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to read file: {e}")
                self.running = False
            finally:
                if self.file and not self.file.closed:
                    self.file.close()
                    self.file = None

    def parse_and_queue(self, line: str):
        try:
            if self.stop_event.is_set() and self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Stopped at file position {self.file_position}")
                self.file.close()
                self.file = None
                return

            if line.startswith("SESSION_NUMBER:"):
                new_session = int(line.split(':')[1])
                if new_session != self.current_session:
                    # Check for missing data in the previous session
                    expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                    if new_session % 2 == 0:
                        expected_types.add('key')
                    else:
                        expected_types.add('kbps_data')
                    missing_types = expected_types - self.session_data_types
                    if missing_types and self.current_session != -1:
                        logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                        # Queue last available data for missing types
                        for data_type in missing_types:
                            if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                for value in self.last_session_data[data_type]:
                                    self.data_queue.put({"type": data_type, "value": value})
                            elif self.last_session_data[data_type] is not None:
                                if data_type == 'key':
                                    self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type], "length": len(self.last_session_data[data_type])})
                                elif data_type == 'kbps_data':
                                    self.data_queue.put({"type": data_type, "kbps": self.last_session_data[data_type]})
                                else:
                                    self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type]})
                    # Reset for new session
                    self.current_session = new_session
                    self.spd1_values_mode = False
                    self.spd2_values_mode = False
                    self.spd1_count = 0
                    self.spd2_count = 0
                    self.session_data_types = set()
                    self.data_queue.put({"type": "session_number", "value": new_session})
                    # Store timestamps for the new session
                    self.last_session_data["timestamp_spd1"] = []
                    self.last_session_data["timestamp_spd2"] = []
                logging.debug(f"Current file position after session: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD1_VALUES:":
                self.spd1_values_mode = True
                self.spd2_values_mode = False
                self.spd1_count = 0
                logging.debug(f"Current file position after SPD1_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD2_VALUES:":
                self.spd1_values_mode = False
                self.spd2_values_mode = True
                self.spd2_count = 0
                logging.debug(f"Current file position after SPD2_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd1_values_mode and self.spd1_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd1", "value": timestamp})
                self.last_session_data["timestamp_spd1"].append(timestamp)
                self.spd1_count += 1
                self.session_data_types.add("timestamp_spd1")
                if self.spd1_count == 40:
                    logging.info(f"Completed queuing 40 SPD1 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD1: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd2_values_mode and self.spd2_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd2", "value": timestamp})
                self.last_session_data["timestamp_spd2"].append(timestamp)
                self.spd2_count += 1
                self.session_data_types.add("timestamp_spd2")
                if self.spd2_count == 40:
                    logging.info(f"Completed queuing 40 SPD2 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD2: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("DECOY_STATE_RANDOMNESS_AT_SPD1:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "spd1_decaystate", "value": value})
                self.last_session_data["spd1_decaystate"] = value
                self.session_data_types.add("spd1_decaystate")
                logging.debug(f"Current file position after spd1_decaystate: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("VISIBILITY_RATIO_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "visibility", "value": value})
                self.last_session_data["visibility"] = value
                self.session_data_types.add("visibility")
                logging.debug(f"Current file position after visibility: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("SPD1_QBER_VALUE_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "qber", "value": value})
                self.last_session_data["qber"] = value
                self.session_data_types.add("qber")
                logging.debug(f"Current file position after qber: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:"):
                logging.debug(f"Current file position after key_bits_length: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("KEY_BITS:"):
                key_match = re.match(r"KEY_BITS:([01]{128,})", line)
                if key_match:
                    key = key_match.group(1)
                    self.data_queue.put({"type": "key", "value": key, "length": len(key)})
                    self.last_session_data["key"] = key
                    self.session_data_types.add("key")
                    logging.debug(f"Queued key (length {len(key)}): {key[:40]}... for session {self.current_session}")
                    logging.debug(f"Current file position after key: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                else:
                    logging.error(f"Invalid key format: {line}")
                return

            if line.startswith("KEY_RATE_PER_SECOND_IS:"):
                kbps = float(line.split(':')[1])
                self.data_queue.put({"type": "kbps_data", "kbps": kbps})
                self.last_session_data["kbps_data"] = kbps
                self.session_data_types.add("kbps_data")
                logging.debug(f"Queued kbps: {kbps} for session {self.current_session}")
                logging.debug(f"Current file position after kbps: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

        except Exception as e:
            logging.error(f"Error parsing line '{line}': {e}")

    def stop(self):
        if self.running:
            logging.info("Stopping data processor")
            self.running = False
            self.stop_event.set()
            if self.mode == "console" and self.process:
                self.process.kill()
                self.process = None
            elif self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Saved file position: {self.file_position}")
                self.file.close()
                self.file = None
            if self.thread:
                self.thread.join(timeout=0.1)
                self.thread = None

    def close(self):
        self.stop()
        if self.mode == "console" and self.process:
            logging.info("Closing data processor")
            self.process.stdout.close()
            self.process.stderr.close()
            self.process = None

    def get_file_position(self):
        return self.file_position'''
        
        
        
'''      
import subprocess
import os
from queue import Queue
import threading
import logging
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, data_queue: Queue, mode: str = "file", file_position: int = 0):
        self.data_queue = data_queue
        self.mode = mode
        self.process = None
        self.file = None
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.spd1_values_mode = False
        self.spd2_values_mode = False
        self.spd1_count = 0
        self.spd2_count = 0
        self.session_data_types = set()
        self.current_session = -1
        self.file_position = file_position
        self.c_program_path = os.path.join("build", "c_program.exe")
        self.output_file_path = os.path.join("build", "output.txt")
        self.last_session_data = {
            "timestamp_spd1": [],
            "timestamp_spd2": [],
            "spd1_decaystate": None,
            "visibility": None,
            "qber": None,
            "key": None,
            "kbps_data": None
        }

    def start(self):
        if not self.running:
            logging.info(f"Starting data processor in {self.mode} mode")
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.read_output)
            self.thread.daemon = True
            self.thread.start()

    def read_output(self):
        if self.mode == "console":
            try:
                self.process = subprocess.Popen(
                    self.c_program_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                while self.running and not self.stop_event.is_set():
                    line = self.process.stdout.readline().strip()
                    if not line and self.process.poll() is not None:
                        logging.info("Subprocess terminated")
                        self.running = False
                        break
                    if line:
                        logging.debug(f"Read line from console: {line}")
                        self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to start subprocess: {e}")
                self.running = False

        elif self.mode == "file":
            try:
                self.file = open(self.output_file_path, "r")
                logging.debug(f"Opened file at position {self.file_position}")
                if self.file_position > 0:
                    self.file.seek(self.file_position)
                    logging.debug(f"Seeking to file position {self.file_position}")
                while self.running and not self.stop_event.is_set():
                    line = self.file.readline().strip()
                    if not line:
                        if self.stop_event.is_set():
                            break
                        import time
                        time.sleep(0.5)
                        continue
                    logging.debug(f"Read line from file: {line}")
                    self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to read file: {e}")
                self.running = False
            finally:
                if self.file and not self.file.closed:
                    self.file.close()
                    self.file = None

    def parse_and_queue(self, line: str):
        try:
            if self.stop_event.is_set() and self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Stopped at file position {self.file_position}")
                self.file.close()
                self.file = None
                return

            if line.startswith("SESSION_NUMBER:"):
                new_session = int(line.split(':')[1])
                if new_session != self.current_session:
                    # Check for missing data in the previous session
                    expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                    if new_session % 2 == 0:
                        expected_types.add('key')
                    else:
                        expected_types.add('kbps_data')
                    missing_types = expected_types - self.session_data_types
                    if missing_types:
                        logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                        for data_type in missing_types:
                            if self.current_session == -1:
                                # Initialize first session missing data (except timestamps) to 0
                                if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                    continue  # Keep timestamps as empty lists
                                elif data_type == 'key':
                                    self.data_queue.put({"type": "key", "value": "0" * 128, "length": 128})
                                    self.last_session_data["key"] = "0" * 128
                                    logging.info(f"Initialized missing {data_type} to '{'0' * 128}' for session {self.current_session}")
                                else:
                                    self.data_queue.put({"type": data_type, "value" if data_type != "kbps_data" else "kbps": 0})
                                    self.last_session_data[data_type] = 0
                                    logging.info(f"Initialized missing {data_type} to 0 for session {self.current_session}")
                            else:
                                # Reuse last session data for subsequent sessions
                                if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                    for value in self.last_session_data[data_type]:
                                        self.data_queue.put({"type": data_type, "value": value})
                                elif self.last_session_data[data_type] is not None:
                                    if data_type == 'key':
                                        self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type], "length": len(self.last_session_data[data_type])})
                                    elif data_type == 'kbps_data':
                                        self.data_queue.put({"type": data_type, "kbps": self.last_session_data[data_type]})
                                    else:
                                        self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type]})
                    # Reset for new session
                    self.current_session = new_session
                    self.spd1_values_mode = False
                    self.spd2_values_mode = False
                    self.spd1_count = 0
                    self.spd2_count = 0
                    self.session_data_types = set()
                    self.data_queue.put({"type": "session_number", "value": new_session})
                    # Store timestamps for the new session
                    self.last_session_data["timestamp_spd1"] = []
                    self.last_session_data["timestamp_spd2"] = []
                    logging.debug(f"Current file position after session: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD1_VALUES:":
                self.spd1_values_mode = True
                self.spd2_values_mode = False
                self.spd1_count = 0
                logging.debug(f"Current file position after SPD1_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD2_VALUES:":
                self.spd1_values_mode = False
                self.spd2_values_mode = True
                self.spd2_count = 0
                logging.debug(f"Current file position after SPD2_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd1_values_mode and self.spd1_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd1", "value": timestamp})
                self.last_session_data["timestamp_spd1"].append(timestamp)
                self.spd1_count += 1
                self.session_data_types.add("timestamp_spd1")
                if self.spd1_count == 40:
                    logging.info(f"Completed queuing 40 SPD1 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD1: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd2_values_mode and self.spd2_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd2", "value": timestamp})
                self.last_session_data["timestamp_spd2"].append(timestamp)
                self.spd2_count += 1
                self.session_data_types.add("timestamp_spd2")
                if self.spd2_count == 40:
                    logging.info(f"Completed queuing 40 SPD2 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD2: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("DECOY_STATE_RANDOMNESS_AT_SPD1:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "spd1_decaystate", "value": value})
                self.last_session_data["spd1_decaystate"] = value
                self.session_data_types.add("spd1_decaystate")
                logging.debug(f"Current file position after spd1_decaystate: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("VISIBILITY_RATIO_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "visibility", "value": value})
                self.last_session_data["visibility"] = value
                self.session_data_types.add("visibility")
                logging.debug(f"Current file position after visibility: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("SPD1_QBER_VALUE_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "qber", "value": value})
                self.last_session_data["qber"] = value
                self.session_data_types.add("qber")
                logging.debug(f"Current file position after qber: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:"):
                logging.debug(f"Current file position after key_bits_length: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("KEY_BITS:"):
                key_match = re.match(r"KEY_BITS:([01]{128,})", line)
                if key_match:
                    key = key_match.group(1)
                    self.data_queue.put({"type": "key", "value": key, "length": len(key)})
                    self.last_session_data["key"] = key
                    self.session_data_types.add("key")
                    logging.debug(f"Queued key (length {len(key)}): {key[:40]}... for session {self.current_session}")
                    logging.debug(f"Current file position after key: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                else:
                    logging.error(f"Invalid key format: {line}")
                return

            if line.startswith("KEY_RATE_PER_SECOND_IS:"):
                kbps = float(line.split(':')[1])
                self.data_queue.put({"type": "kbps_data", "kbps": kbps})
                self.last_session_data["kbps_data"] = kbps
                self.session_data_types.add("kbps_data")
                logging.debug(f"Queued kbps: {kbps} for session {self.current_session}")
                logging.debug(f"Current file position after kbps: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

        except Exception as e:
            logging.error(f"Error parsing line '{line}': {e}")

    def stop(self):
        if self.running:
            logging.info("Stopping data processor")
            self.running = False
            self.stop_event.set()
            if self.mode == "console" and self.process:
                self.process.kill()
                self.process = None
            elif self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Saved file position: {self.file_position}")
                self.file.close()
                self.file = None
            if self.thread:
                self.thread.join(timeout=0.1)
                self.thread = None

    def close(self):
        self.stop()
        if self.mode == "console" and self.process:
            logging.info("Closing data processor")
            self.process.stdout.close()
            self.process.stderr.close()
            self.process = None

    def get_file_position(self):
        return self.file_position'''
        
        
        

        
        
import subprocess
import os
from queue import Queue
import threading
import logging
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, data_queue: Queue, mode: str = "file", file_position: int = 0, input_string: str = None):
        self.data_queue = data_queue
        self.mode = mode
        self.input_string = input_string
        self.process = None
        self.file = None
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.spd1_values_mode = False
        self.spd2_values_mode = False
        self.spd1_count = 0
        self.spd2_count = 0
        self.session_data_types = set()
        self.current_session = -1
        self.file_position = file_position
        self.c_program_path = os.path.join("build", "c_program.exe")
        self.output_file_path = os.path.join("build", "output.txt")
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

    def start(self):
        if not self.running:
            logging.info(f"Starting data processor in {self.mode} mode" + (f" with input string: {self.input_string}" if self.input_string else ""))
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.read_output)
            self.thread.daemon = True
            self.thread.start()

    def read_output(self):
        if self.mode == "console":
            try:
                cmd = [self.c_program_path]
                if self.input_string:
                    cmd.append(self.input_string)
                else:
                    cmd.append("default_input")
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                while self.running and not self.stop_event.is_set():
                    line = self.process.stdout.readline().strip()
                    if not line and self.process.poll() is not None:
                        logging.info("Subprocess terminated")
                        self.running = False
                        break
                    if line:
                        logging.debug(f"Read line from console: {line}")
                        self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to start subprocess: {e}")
                self.running = False

        elif self.mode == "file":
            try:
                self.file = open(self.output_file_path, "r")
                logging.debug(f"Opened file at position {self.file_position}")
                if self.file_position > 0:
                    self.file.seek(self.file_position)
                    logging.debug(f"Seeking to file position {self.file_position}")
                while self.running and not self.stop_event.is_set():
                    line = self.file.readline().strip()
                    if not line:
                        if self.stop_event.is_set():
                            break
                        import time
                        time.sleep(0.5)
                        continue
                    logging.debug(f"Read line from file: {line}")
                    self.parse_and_queue(line)
            except Exception as e:
                logging.error(f"Failed to read file: {e}")
                self.running = False
            finally:
                if self.file and not self.file.closed:
                    self.file.close()
                    self.file = None

    def parse_and_queue(self, line: str):
        try:
            if self.stop_event.is_set() and self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Stopped at file position {self.file_position}")
                self.file.close()
                self.file = None
                return

            if line.startswith("SESSION_NUMBER:"):
                new_session = int(line.split(':')[1])
                if new_session != self.current_session:
                    expected_types = {'timestamp_spd1', 'timestamp_spd2', 'spd1_decaystate', 'visibility', 'qber'}
                    if self.mode == "console":
                        expected_types.add('input_string')
                    if new_session % 2 == 0:
                        expected_types.add('key')
                    else:
                        expected_types.add('kbps_data')
                    missing_types = expected_types - self.session_data_types
                    if missing_types:
                        logging.warning(f"Session {self.current_session} missing data types: {missing_types}")
                        for data_type in missing_types:
                            if self.current_session == -1:
                                if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                    continue
                                elif data_type == 'key':
                                    self.data_queue.put({"type": "key", "value": "0" * 128, "length": 128})
                                    self.last_session_data["key"] = "0" * 128
                                    logging.info(f"Initialized missing {data_type} to '{'0' * 128}' for session {self.current_session}")
                                elif data_type == 'input_string' and self.mode == "console":
                                    self.data_queue.put({"type": "input_string", "value": "default_input"})
                                    self.last_session_data["input_string"] = "default_input"
                                    logging.info(f"Initialized missing {data_type} to 'default_input' for session {self.current_session}")
                                elif data_type != 'input_string':
                                    self.data_queue.put({"type": data_type, "value" if data_type != "kbps_data" else "kbps": 0})
                                    self.last_session_data[data_type] = 0
                                    logging.info(f"Initialized missing {data_type} to 0 for session {self.current_session}")
                            else:
                                if data_type in ['timestamp_spd1', 'timestamp_spd2']:
                                    for value in self.last_session_data[data_type]:
                                        self.data_queue.put({"type": data_type, "value": value})
                                elif self.last_session_data[data_type] is not None and data_type != 'input_string':
                                    if data_type == 'key':
                                        self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type], "length": len(self.last_session_data[data_type])})
                                    elif data_type == 'kbps_data':
                                        self.data_queue.put({"type": data_type, "kbps": self.last_session_data[data_type]})
                                    else:
                                        self.data_queue.put({"type": data_type, "value": self.last_session_data[data_type]})
                                elif data_type == 'input_string' and self.mode == "console" and self.last_session_data['input_string'] is not None:
                                    self.data_queue.put({"type": "input_string", "value": self.last_session_data['input_string']})
                    self.current_session = new_session
                    self.spd1_values_mode = False
                    self.spd2_values_mode = False
                    self.spd1_count = 0
                    self.spd2_count = 0
                    self.session_data_types = set()
                    self.data_queue.put({"type": "session_number", "value": new_session})
                    self.last_session_data["timestamp_spd1"] = []
                    self.last_session_data["timestamp_spd2"] = []
                    logging.debug(f"Current file position after session: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD1_VALUES:":
                self.spd1_values_mode = True
                self.spd2_values_mode = False
                self.spd1_count = 0
                logging.debug(f"Current file position after SPD1_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line == "SPD2_VALUES:":
                self.spd1_values_mode = False
                self.spd2_values_mode = True
                self.spd2_count = 0
                logging.debug(f"Current file position after SPD2_VALUES: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd1_values_mode and self.spd1_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd1", "value": timestamp})
                self.last_session_data["timestamp_spd1"].append(timestamp)
                self.spd1_count += 1
                self.session_data_types.add("timestamp_spd1")
                if self.spd1_count == 40:
                    logging.info(f"Completed queuing 40 SPD1 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD1: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if self.spd2_values_mode and self.spd2_count < 40:
                timestamp = int(line)
                self.data_queue.put({"type": "timestamp_spd2", "value": timestamp})
                self.last_session_data["timestamp_spd2"].append(timestamp)
                self.spd2_count += 1
                self.session_data_types.add("timestamp_spd2")
                if self.spd2_count == 40:
                    logging.info(f"Completed queuing 40 SPD2 timestamps for session {self.current_session}")
                logging.debug(f"Current file position after SPD2: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("DECOY_STATE_RANDOMNESS_AT_SPD1:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "spd1_decaystate", "value": value})
                self.last_session_data["spd1_decaystate"] = value
                self.session_data_types.add("spd1_decaystate")
                logging.debug(f"Current file position after spd1_decaystate: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("VISIBILITY_RATIO_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "visibility", "value": value})
                self.last_session_data["visibility"] = value
                self.session_data_types.add("visibility")
                logging.debug(f"Current file position after visibility: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("SPD1_QBER_VALUE_IS:"):
                value = float(line.split(':')[1])
                self.data_queue.put({"type": "qber", "value": value})
                self.last_session_data["qber"] = value
                self.session_data_types.add("qber")
                logging.debug(f"Current file position after qber: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:"):
                logging.debug(f"Current file position after key_bits_length: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("KEY_BITS:"):
                key_match = re.match(r"KEY_BITS:([01]{128,})", line)
                if key_match:
                    key = key_match.group(1)
                    self.data_queue.put({"type": "key", "value": key, "length": len(key)})
                    self.last_session_data["key"] = key
                    self.session_data_types.add("key")
                    logging.debug(f"Queued key (length {len(key)}): {key[:40]}... for session {self.current_session}")
                    logging.debug(f"Current file position after key: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                else:
                    logging.error(f"Invalid key format: {line}")
                return

            if line.startswith("KEY_RATE_PER_SECOND_IS:"):
                kbps = float(line.split(':')[1])
                self.data_queue.put({"type": "kbps_data", "kbps": kbps})
                self.last_session_data["kbps_data"] = kbps
                self.session_data_types.add("kbps_data")
                logging.debug(f"Queued kbps: {kbps} for session {self.current_session}")
                logging.debug(f"Current file position after kbps: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

            if line.startswith("INPUT_STRING:") and self.mode == "console":
                input_str = line.split(':', 1)[1]
                self.data_queue.put({"type": "input_string", "value": input_str})
                self.last_session_data["input_string"] = input_str
                self.session_data_types.add("input_string")
                logging.debug(f"Queued input string: {input_str} for session {self.current_session}")
                logging.debug(f"Current file position after input_string: {self.file.tell() if self.mode == 'file' and self.file and not self.file.closed else 'N/A'}")
                return

        except Exception as e:
            logging.error(f"Error parsing line '{line}': {e}")

    def stop(self):
        if self.running:
            logging.info("Stopping data processor")
            self.running = False
            self.stop_event.set()
            if self.mode == "console" and self.process:
                self.process.kill()
                self.process = None
            elif self.mode == "file" and self.file and not self.file.closed:
                self.file_position = self.file.tell()
                logging.debug(f"Saved file position: {self.file_position}")
                self.file.close()
                self.file = None
            if self.thread:
                self.thread.join(timeout=0.1)
                self.thread = None

    def get_file_position(self):
        return self.file_position

    def close(self):
        self.stop()
        if self.mode == "console" and self.process:
            logging.info("Closing data processor")
            self.process.stdout.close()
            self.process.stderr.close()
            self.process = None