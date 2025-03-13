"""
UDP Test script for the EV Charging Station Monitor.
This script sends test UDP packets in CSV format to match the hardware's format:
Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev
"""

import socket
import time
import math
import random
import argparse

# Update the send_test_packets function in udp_test_csv.py:

def send_test_packets(ip='127.0.0.1', port=5000, interval=0.1, duration=60):
    """
    Send test UDP packets to the specified IP and port.
    
    Updated to include new parameters from mentor.
    """
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    start_time = time.time()
    packet_count = 0
    frequency = 50.0  # Hz
    
    print(f"Sending test UDP packets to {ip}:{port} for {duration} seconds...")
    print(f"Format: Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev,Pbattery,Pg,Qg,PF,Fg,THD,s1,s2,s3,s4,SoC_battery,SoC_EV")
    
    try:
        while time.time() - start_time < duration:
            # Current time for waveform calculation
            current_time = time.time() - start_time
            
            # Base values with some randomness
            Vd = 220.0 + random.uniform(-5, 5)      # Grid Voltage (V)
            Id = 10.0 + random.uniform(-1, 1)       # Grid Current (A)
            Vdc = 400.0 + random.uniform(-3, 3)     # DC Link Voltage (V)
            Vev = 350.0 + random.uniform(-2, 2)     # EV Voltage (V)
            Vpv = 380.0 + random.uniform(-3, 3)     # PV Voltage (V)
            Iev = 15.0 + random.uniform(-0.5, 0.5)  # EV Current (A)
            Ipv = 8.0 + random.uniform(-0.4, 0.4)   # PV Current (A)
            
            # Calculate powers
            Ppv = Vpv * Ipv  # PV Power (W)
            Pev = Vev * Iev * -1  # EV Power (W) - negative for consumption
            
            # New parameters
            Pbattery = 500.0 + random.uniform(-100, 100)  # Battery Power (W)
            Pg = Vd * Id  # Grid Power (W)
            Qg = 500.0 + random.uniform(-50, 50)  # Reactive Power (VAr)
            PF = 0.95 + random.uniform(-0.05, 0.05)  # Power Factor
            Fg = frequency + random.uniform(-0.1, 0.1)  # Grid Frequency (Hz)
            THD = 3.0 + random.uniform(-0.5, 0.5)  # THD (%)
            
            # Status indicators (0-3)
            s1 = random.randint(0, 3)  # PV Status
            s2 = random.randint(0, 3)  # EV Status
            s3 = random.randint(0, 3)  # Grid Status
            s4 = random.randint(0, 3)  # Battery Status
            
            # State of Charge values
            SoC_battery = 60.0 + random.uniform(-5, 5)  # Battery SoC (%)
            SoC_EV = 45.0 + random.uniform(-2, 2)  # EV SoC (%)
            
            # Add a slow oscillation to simulate changing conditions
            oscillation = math.sin(current_time * 0.1) * 50
            Ppv += oscillation
            Pev -= oscillation
            
            # Format the data as a CSV string with all parameters
            data = f"{Vd:.2f},{Id:.2f},{Vdc:.2f},{Vev:.2f},{Vpv:.2f},{Iev:.2f},{Ipv:.2f},{Ppv:.2f},{Pev:.2f}," + \
                   f"{Pbattery:.2f},{Pg:.2f},{Qg:.2f},{PF:.2f},{Fg:.2f},{THD:.2f}," + \
                   f"{s1},{s2},{s3},{s4},{SoC_battery:.2f},{SoC_EV:.2f}"
            
            # Send the data
            sock.sendto(data.encode('utf-8'), (ip, port))
            
            packet_count += 1
            if packet_count % 100 == 0:
                print(f"Sent {packet_count} packets...")
            
            # Wait for the next interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        sock.close()
        elapsed_time = time.time() - start_time
        print(f"Sent {packet_count} packets in {elapsed_time:.2f} seconds")