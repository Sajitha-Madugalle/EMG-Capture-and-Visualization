import socket
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
from collections import deque

# --- CONFIGURATION ---
UDP_IP = "0.0.0.0" 
UDP_PORT = 8888
MAX_POINTS = 250000 # 0.5 seconds of data at 25 kSPS

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

# Buffer to hold plot data
data_buffer = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)

# Setup Plot
fig, ax = plt.subplots()
line, = ax.plot(data_buffer)

# Axis Configuration
# Range is -1024 to +1024 because we are subtracting signals
ax.set_ylim(-520, 520) 
ax.set_xlim(0, MAX_POINTS)
ax.set_title("Live Stream: Signal(A1) - Ref(A2)")
ax.set_ylabel("Differential Value")
ax.grid(True)

# Draw a red center line at 0
ax.axhline(y=0, color='r', linestyle='-', alpha=0.3)

def update_plot(frame):
    try:
        while True:
            # Receive Packet
            data, _ = sock.recvfrom(2048)
            
            # Calculate number of samples (2 bytes per sample)
            num_samples = len(data) // 2
            
            # Unpack Binary
            # '<' = Little Endian
            # 'h' = Signed Short (This is the key change for differential)
            fmt = '<' + 'h' * num_samples
            values = struct.unpack(fmt, data)
            
            data_buffer.extend(values)
            
    except BlockingIOError:
        pass # No data waiting
    except struct.error:
        print("Packet Error")

    line.set_ydata(data_buffer)
    return line,

# Animate
ani = animation.FuncAnimation(fig, update_plot, interval=20, blit=True)
print(f"Listening on port {UDP_PORT}...")
plt.show()