"""
UDP Test script for the EV Charging Station Monitor.
This script sends test UDP packets in CSV format to match the hardware's format:
Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev,Pbattery,Pg,Qg,PF,Fg,THD,s1,s2,s3,s4,SoC_battery,SoC_EV
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
        The target IP address to send UDP packets to.
    port : int
        The target port to send UDP packets to.
    interval : float
        Time interval between packets in seconds.
    duration : float
        Total duration to send packets for in seconds.
    """
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    start_time = time.time()
    packet_count = 0
    frequency = 50.0  # Hz
    
    # Initialize SoC values with realistic starting points
    SoC_battery = 60.0  # Initial battery SoC (%)
    SoC_EV = 45.0       # Initial EV SoC (%)
    
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
            
            # Determine power factor with realistic variations
            PF = 0.95 + random.uniform(-0.05, 0.05)  # Power Factor
            PF = min(1.0, max(0.8, PF))  # Constrain to realistic range
            
            # Battery power with realistic variations
            Pbattery = 500.0 + random.uniform(-100, 100)  # Battery Power (W)
            
            # Add a slow oscillation to simulate changing conditions
            oscillation = math.sin(current_time * 0.1) * 50
            Ppv += oscillation
            Pev -= oscillation
            
            # Grid power balances the system (conservation of energy)
            # P_grid + P_pv + P_ev + P_battery should be close to zero
            Pg = -1 * (Ppv + Pev + Pbattery) + random.uniform(-50, 50)  # With some noise
            
            # Calculate reactive power
            theta = math.acos(PF)  # Power factor angle
            Qg = Pg * math.tan(theta)  # Reactive power
            
            # Other electrical parameters
            Fg = frequency + random.uniform(-0.1, 0.1)  # Grid Frequency (Hz)
            THD = 3.0 + random.uniform(-0.5, 0.5)  # THD (%)
            
            # Status indicators (0=Off, 1=Standby, 2=Active, 3=Fault)
            s1 = 0 if Ppv > 1 else 0  # PV Status: Active if generating power
            s2 = 2 if abs(Pev) > 100 else 0  # EV Status: Active if charging/discharging
            s3 = 2  # Grid Status: Typically active
            s4 = 2 if abs(Pbattery) > 100 else 0  # Battery Status: Active if in use
            
            # Add small chance of fault for realism
            if random.random() < 0.005:  # 0.5% chance
                fault_component = random.randint(1, 4)
                if fault_component == 1: s1 = 3
                elif fault_component == 2: s2 = 3
                elif fault_component == 3: s3 = 3
                else: s4 = 3
            
            # Update SoC values based on power flow
            if Pev < 0:  # Charging
                SoC_EV += (abs(Pev) / 10000) * interval  # Increase SoC when charging
            else:  # Discharging or idle
                SoC_EV -= (Pev / 20000) * interval  # Slower discharge
            
            if Pbattery < 0:  # Battery discharging
                SoC_battery -= (abs(Pbattery) / 5000) * interval
            else:  # Battery charging
                SoC_battery += (Pbattery / 8000) * interval
            
            # Constrain SoC values
            SoC_battery = max(0, min(100, SoC_battery))
            SoC_EV = max(0, min(100, SoC_EV))
            
            # Format the data as a CSV string with all parameters
            data = f"{Vd:.2f},{Id:.2f},{Vdc:.2f},{Vev:.2f},{Vpv:.2f},{Iev:.2f},{Ipv:.2f},{Ppv:.2f},{Pev:.2f}," + \
                   f"{Pbattery:.2f},{Pg:.2f},{Qg:.2f},{PF:.2f},{Fg:.2f},{THD:.2f}," + \
                   f"{s1},{s2},{s3},{s4},{SoC_battery:.2f},{SoC_EV:.2f}"
            
            # Send the data
            sock.sendto(data.encode('utf-8'), (ip, port))
            
            packet_count += 1
            if packet_count % 100 == 0:
                print(f"Sent {packet_count} packets... Battery SoC: {SoC_battery:.1f}%, EV SoC: {SoC_EV:.1f}%")
            
            # Wait for the next interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        sock.close()
        elapsed_time = time.time() - start_time
        print(f"Sent {packet_count} packets in {elapsed_time:.2f} seconds")
        print(f"Final values - Battery SoC: {SoC_battery:.1f}%, EV SoC: {SoC_EV:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send test UDP packets for EV Charging Station')
    parser.add_argument('--ip', default='127.0.0.1', help='Target IP address')
    parser.add_argument('--port', type=int, default=5000, help='Target port')
    parser.add_argument('--interval', type=float, default=0.1, help='Packet interval in seconds')
    parser.add_argument('--duration', type=float, default=60, help='Test duration in seconds')
    args = parser.parse_args()
    
    send_test_packets(args.ip, args.port, args.interval, args.duration)