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
│       ├── app.py        # Main GUI Application
│       └── EMG_game.py   # Flappy Bird Game
├── 04 3D Design/         # 3D models for enclosures and mechanical parts
└── 05 media/             # Project images and demos
```

## 🌟 Key Features

### Hardware
- **Precision Amplification**: Uses INA333 for low-noise instrumentation amplification.
- **Signal Conditioning**: Analog filtering and gain stages tailored for EMG signals.
- **Custom PCB**: Professionally designed using Altium Designer.
- **Wearable Design**:

<p align="center">
  <img src="05 media/device.jpeg" width="45%" alt="Device View" />
  <img src="05 media/fulldevice.png" width="14%" alt="Device on Arm" />
</p>
<p align="center">
  <em>Left: Final PCB Design | Right: Device attached to arm for data capture</em>
</p>

### Firmware (Adafruit M0)
- **High Sampling Rate**: Optimized ADC register settings for 25kHz sampling.
- **Efficient Transmission**: Packs 256 samples into binary UDP packets for low-latency wireless streaming.
- **Differential Reading**: Performs on-chip differential ADC readings (A1 - A2).

### Software (Python App)
The system includes a powerful Python-based GUI (`app.py`) for real-time analysis.

- **Real-Time Oscilloscope**: Smooth visualization using `PyQtGraph` and `PyQt6`.
- **Digital Signal Processing**:
  - **Notch Filter**: Removes 50Hz/100Hz/150Hz mains hum.
  - **Bandpass Filter**: Configurable Butterworth filter (e.g., 25Hz - 150Hz).
- **Data Recording**: Save captured sessions to CSV for offline analysis.

![Signal in GUI](05%20media/signal_in_gui.jpeg)
*Real-time EMG data visualization in the GUI*

### 🎮 Flappy Bird Game (HCI Demo)
To demonstrate **Human-Computer Interaction (HCI)** capabilities, the project includes a game controlled by muscle activity (`EMG_game.py`).

- **Control Scheme**: Muscle contractions (EMG signal crossing a threshold) trigger the bird to jump.
- **Visual Feedback**: Real-time EMG signal envelope is displayed at the bottom of the game window.
- **Engaging Interaction**: A fun and interactive way to visualize bio-potential signals and their control applications.

![Flappy Bird Game](05%20media/flappy_bird_game.jpeg)
*Flappy Bird game controlled by EMG signals*

### 🎥 Demo
Check out the system in action:

![Demo](05%20media/demo.mp4)

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
pip install numpy scipy pyqt6 pyqtgraph pygame
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

### 4. Playing the Game
To try the game demo:
```bash
cd "03 firmware/Python"
python EMG_game.py
```
- Flex your muscle to make the bird jump!
- Adjust gain with Up/Down arrow keys if needed.

## 📊 Simulation
The `01 Simulations` folder contains:
- **LTSpice**: Run `INA_behavioral.asc` to simulate the analog front-end behavior.
- **Python Demo**: Run `GUI.py` in `01 Simulations/LT Spice/` to see a simulation of noise addition and filtering on pre-recorded data.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
