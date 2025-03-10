"""
UDP Test script for the EV Charging Station Monitor.
This script sends test UDP packets to simulate the hardware.
"""

import socket
import time
import json
import math
import random

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
    
    try:
        while time.time() - start_time < duration:
            # Current time for waveform calculation
            current_time = time.time() - start_time
            
            # Calculate instantaneous waveform values
            phase_shift = (2 * math.pi) / 3  # 120 degrees
            x = current_time * 2 * math.pi * frequency
            
            voltage_amplitude = 220.0 + random.uniform(-2, 2)
            current_amplitude = 10.0 + random.uniform(-0.5, 0.5)
            
            # Generate sample data packet
            data = {
                # Basic parameters
                'Grid_Voltage': voltage_amplitude * 0.707,  # RMS
                'Grid_Current': current_amplitude * 0.707,  # RMS
                'DCLink_Voltage': 80.0 + random.uniform(-1, 1),
                'ElectricVehicle_Voltage': 58.0 + random.uniform(-0.5, 0.5),
                'PhotoVoltaic_Voltage': 65.0 + random.uniform(-0.5, 0.5),
                'ElectricVehicle_Current': 50.0 + random.uniform(-1, 1),
                'PhotoVoltaic_Current': 30.0 + random.uniform(-0.5, 0.5),
                'ElectricVehicle_Power': -4000.0 + random.uniform(-100, 100),
                'PhotoVoltaic_Power': 2000.0 + random.uniform(-50, 50),
                
                # Waveform data
                'waveforms': {
                    'Grid_Voltage': {
                        'phaseA': voltage_amplitude * math.sin(x),
                        'phaseB': voltage_amplitude * math.sin(x - phase_shift),
                        'phaseC': voltage_amplitude * math.sin(x + phase_shift)
                    },
                    'Grid_Current': {
                        'phaseA': current_amplitude * math.sin(x - 0.1),  # Slight phase lag
                        'phaseB': current_amplitude * math.sin(x - phase_shift - 0.1),
                        'phaseC': current_amplitude * math.sin(x + phase_shift - 0.1)
                    }
                },
                
                # Extra parameters for waveform generation
                'frequency': frequency + random.uniform(-0.01, 0.01),
                'voltage_amplitude': voltage_amplitude,
                'current_amplitude': current_amplitude
            }
            
            # Convert to JSON and send
            json_data = json.dumps(data).encode('utf-8')
            sock.sendto(json_data, (ip, port))
            
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
    import argparse
    
    parser = argparse.ArgumentParser(description="UDP Test Tool for EV Charging Station Monitor")
    parser.add_argument("--ip", default="127.0.0.1", help="Target IP address")
    parser.add_argument("--port", type=int, default=5000, help="Target port")
    parser.add_argument("--interval", type=float, default=0.1, help="Packet interval in seconds")
    parser.add_argument("--duration", type=float, default=60, help="Test duration in seconds")
    args = parser.parse_args()
    
    send_test_packets(ip=args.ip, port=args.port, interval=args.interval, duration=args.duration)