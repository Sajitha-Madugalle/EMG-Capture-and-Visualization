# EMG Capture and Visualization System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![C++](https://img.shields.io/badge/C%2B%2B-Arduino-blue)
![Altium](https://img.shields.io/badge/Hardware-Altium-orange)
![LTSpice](https://img.shields.io/badge/Simulation-LTSpice-red)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A complete Electromyography (EMG) acquisition and monitoring system featuring custom hardware design, high-speed signal conditioning, microcontroller firmware, and real-time visualization tools.

## 🚀 Project Overview

This project provides an end-to-end solution for capturing and analyzing EMG signals. It includes:
- **Analog Front-End**: A custom PCB designed with INA333 instrumentation amplifiers and LMP770x op-amps for precise signal conditioning.
- **High-Speed Acquisition**: An Adafruit M0 (SAMD21) microcontroller sampling at **25 kSPS** (40µs interval).
- **Wireless Transmission**: Real-time data streaming via UDP over WiFi.
- **Software Suite**: A Python-based PC application for real-time visualization, digital filtering (Notch, Bandpass), and data recording.

## 📂 Directory Structure

```
e:\Projects\EMG-Capture-and-Visualization\
├── 01 Simulations/       # Circuit simulations and Python signal processing demos
│   ├── LT Spice/         # LTSpice models (INA333, etc.) and behavioral simulations
│   └── Dataset/          # Test datasets
├── 02 Hardware/          # Hardware design files
│   └── PCB/              # Altium Designer Schematics (.SchDoc) and PCB Layouts (.PcbDoc)
├── 03 firmware/          # Microcontroller code and PC software
│   ├── adafruitM0/       # Arduino sketch for the Adafruit M0 Feather
│   └── Python/           # Real-time visualization application (PyQt6)
└── 04 3D Design/         # 3D models for enclosures and mechanical parts
```

## 🌟 Key Features

### Hardware
- **Precision Amplification**: Uses INA333 for low-noise instrumentation amplification.
- **Signal Conditioning**: Analog filtering and gain stages tailored for EMG signals.
- **Custom PCB**: Professionally designed using Altium Designer.

### Firmware (Adafruit M0)
- **High Sampling Rate**: Optimized ADC register settings for 25kHz sampling.
- **Efficient Transmission**: Packs 256 samples into binary UDP packets for low-latency wireless streaming.
- **Differential Reading**: Performs on-chip differential ADC readings (A1 - A2).

### Software (Python App)
- **Real-Time Oscilloscope**: Smooth visualization using `PyQtGraph` and `PyQt6`.
- **Digital Signal Processing**:
  - **Notch Filter**: Removes 50Hz/100Hz/150Hz mains hum.
  - **Bandpass Filter**: Configurable Butterworth filter (e.g., 25Hz - 150Hz).
- **Data Recording**: Save captured sessions to CSV for offline analysis.

## 🛠️ Getting Started

### Prerequisites
- **Hardware**: Assembled PCB, Adafruit M0 Feather (WiFi).
- **Software**: Python 3.x, Arduino IDE.

### 1. Firmware Setup
1. Open `03 firmware/adafruitM0/adafruitM0.ino` in Arduino IDE.
2. Install the **WiFi101** library.
3. Update the `ssid`, `pass`, and `remoteIp` (your PC's IP address) in the code.
4. Upload to the Adafruit M0 board.

### 2. Python Environment
Install the required Python libraries:
```bash
pip install numpy scipy pyqt6 pyqtgraph
```

### 3. Running the Visualization
Navigate to the Python directory and run the application:
```bash
cd "03 firmware/Python"
python app.py
```
1. Enter the **Port** (default: 8888).
2. Click **CONNECT** to start streaming.
3. Use the checkboxes to enable **Mains Hum** removal or **Bandpass** filtering.
4. Click **START CAPTURE** to record data to a CSV file.

## 📊 Simulation
The `01 Simulations` folder contains:
- **LTSpice**: Run `INA_behavioral.asc` to simulate the analog front-end behavior.
- **Python Demo**: Run `GUI.py` in `01 Simulations/LT Spice/` to see a simulation of noise addition and filtering on pre-recorded data.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
