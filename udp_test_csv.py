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

def send_test_packets(ip='127.0.0.1', port=5000, interval=0.1, duration=60):
    """
    Send test UDP packets to the specified IP and port.
    
    Parameters:
    -----------
    ip : str
        The IP address to send packets to.
    port : int
        The port to send packets to.
    interval : float
        Time between packets in seconds.
    duration : float
        Total duration to send packets for in seconds.
    """
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    start_time = time.time()
    packet_count = 0
    frequency = 50.0  # Hz
    
    print(f"Sending test UDP packets to {ip}:{port} for {duration} seconds...")
    print(f"Format: Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev")
    
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
            
            # Add a slow oscillation to simulate changing conditions
            oscillation = math.sin(current_time * 0.1) * 50
            Ppv += oscillation
            Pev -= oscillation
            
            # Format the data as a CSV string exactly as shown in the mentor's code
            data = f"{Vd:.2f},{Id:.2f},{Vdc:.2f},{Vev:.2f},{Vpv:.2f},{Iev:.2f},{Ipv:.2f},{Ppv:.2f},{Pev:.2f}"
            
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Test Tool for EV Charging Station Monitor")
    parser.add_argument("--ip", default="127.0.0.1", help="Target IP address")
    parser.add_argument("--port", type=int, default=5000, help="Target port")
    parser.add_argument("--interval", type=float, default=0.1, help="Packet interval in seconds (100ms default)")
    parser.add_argument("--duration", type=float, default=60, help="Test duration in seconds")
    args = parser.parse_args()
    
    send_test_packets(ip=args.ip, port=args.port, interval=args.interval, duration=args.duration)