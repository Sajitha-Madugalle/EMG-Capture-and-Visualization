import sys
import time
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from scipy.signal import iirnotch, butter, filtfilt

class EMGRealTimePlot(QtWidgets.QMainWindow):
    def __init__(self, data, sample_interval=0.002, window_time=5.0):
        super().__init__()
        self.setWindowTitle("Real-Time EMG with Noise & Filters (PyQt5)")
        self.resize(1000, 500)

        # Parameters
        self.data = data
        self.sample_interval = sample_interval
        self.window_time = window_time
        self.fs = 1.0 / sample_interval  # Sampling frequency (500 Hz)
        self.start_time = time.time()
        self.data_index = 0

        # Buffers
        self.x_buffer = []
        self.y_buffer = []

        # ===== Plot Setup =====
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)
        self.plot_widget.setYRange(-0.02, 0.02)
        self.plot_widget.setLabel('left', 'Amplitude (V)')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.4)
        pg.setConfigOptions(useOpenGL=True)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='lime', width=2))

        # ===== Pre-compute Filters =====
        # Notch filters (50 Hz and 100 Hz)
        self.b_notch_50, self.a_notch_50 = iirnotch(50, Q=30, fs=self.fs)
        self.b_notch_100, self.a_notch_100 = iirnotch(100, Q=30, fs=self.fs)

        # Low-pass filter (Butterworth, cutoff below Nyquist = 200 Hz)
        self.b_low, self.a_low = butter(4, 200 / (0.5 * self.fs), btype='low', analog=False)

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(self.sample_interval * 1000))

    def add_noise(self, t, signal):
        """Add 50 Hz, 2 MHz, 3 MHz noise (1 mV amplitude each)."""
        A = 0.001
        noise_50Hz = A * np.sin(2 * np.pi * 50 * t)
        noise_2MHz = A * np.sin(2 * np.pi * 2_000_000 * t)
        noise_3MHz = A * np.sin(2 * np.pi * 3_000_000 * t)
        return signal + noise_50Hz + noise_2MHz + noise_3MHz

    def apply_filters(self, signal):
        """Apply notch filters (50,100 Hz) + low-pass (200 Hz)."""
        filtered = filtfilt(self.b_notch_50, self.a_notch_50, signal)
        filtered = filtfilt(self.b_notch_100, self.a_notch_100, filtered)
        filtered = filtfilt(self.b_low, self.a_low, filtered)
        return filtered

    def update_plot(self):
        now = time.time() - self.start_time

        while self.data_index < len(self.data) and self.data["time"].iloc[self.data_index] <= now:
            t = self.data["time"].iloc[self.data_index]
            raw_signal = self.data["signal"].iloc[self.data_index]
            noisy_signal = self.add_noise(t, raw_signal)
            self.x_buffer.append(t)
            self.y_buffer.append(noisy_signal)
            self.data_index += 1

        # Trim to 5 s window
        while self.x_buffer and (self.x_buffer[-1] - self.x_buffer[0]) > self.window_time:
            self.x_buffer.pop(0)
            self.y_buffer.pop(0)

        # Apply filters
        if len(self.y_buffer) > 10:
            y_filtered = self.apply_filters(np.array(self.y_buffer))
        else:
            y_filtered = np.array(self.y_buffer)

        if self.x_buffer:
            self.curve.setData(self.x_buffer, y_filtered)
            self.plot_widget.setXRange(self.x_buffer[0],
                                       self.x_buffer[0] + self.window_time,
                                       padding=0)

        if self.data_index >= len(self.data):
            self.timer.stop()
            print("Streaming complete.")

if __name__ == "__main__":
    data = pd.read_csv("EMGdata10s.txt", names=["time", "signal"])

    app = QtWidgets.QApplication(sys.argv)
    viewer = EMGRealTimePlot(data, sample_interval=0.002, window_time=5.0)
    viewer.show()
    sys.exit(app.exec_())
