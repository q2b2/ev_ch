"""
UDP Client for receiving real-time data from the EV Charging Station.
This module handles receiving and parsing UDP packets from the hardware.
"""

import socket
import threading
import time
import numpy as np
from collections import deque

class UDPClient:
    """
    A UDP client that receives and parses data from the EV Charging Station hardware.
    
    The data format is a CSV string with 21 values:
    Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev,Pbattery,Pg,Qg,PF,Fg,THD,s1,s2,s3,s4,SoC_battery,SoC_EV
    """
    
    def __init__(self, ip="0.0.0.0", port=5000, buffer_size=1024, history_length=1000):
        """
        Initialize the UDP client.
        
        Parameters:
        -----------
        ip : str
            The IP address to bind to. Default is '0.0.0.0' which binds to all available interfaces.
        port : int
            The port to listen on for incoming data.
        buffer_size : int
            Size of the receive buffer in bytes.
        history_length : int
            Number of historical data points to store for each parameter.
        """
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.history_length = history_length
        
        # Socket for receiving UDP packets
        self.socket = None
        
        # Flag to control the receive thread
        self.is_running = False
        self.receive_thread = None
        
        # Data storage - based on the CSV format from the mentor's code
        # The data order is: Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev
        self.latest_data = {
            'Grid_Voltage': 0.0,       # Vd
            'Grid_Current': 0.0,       # Id
            'DCLink_Voltage': 0.0,     # Vdc
            'ElectricVehicle_Voltage': 0.0, # Vev
            'PhotoVoltaic_Voltage': 0.0,    # Vpv
            'ElectricVehicle_Current': 0.0, # Iev
            'PhotoVoltaic_Current': 0.0,    # Ipv
            'PhotoVoltaic_Power': 0.0,      # Ppv
            'ElectricVehicle_Power': 0.0,   # Pev
            'Battery_Power': 0.0       # Calculated, not directly from device
        }
        
        # For time series data
        self.time_history = deque(maxlen=history_length)
        
        # History storage for each parameter
        self.data_history = {
            'Grid_Voltage': deque(maxlen=history_length),
            'Grid_Current': deque(maxlen=history_length),
            'DCLink_Voltage': deque(maxlen=history_length),
            'ElectricVehicle_Voltage': deque(maxlen=history_length),
            'PhotoVoltaic_Voltage': deque(maxlen=history_length),
            'ElectricVehicle_Current': deque(maxlen=history_length),
            'PhotoVoltaic_Current': deque(maxlen=history_length),
            'PhotoVoltaic_Power': deque(maxlen=history_length),
            'ElectricVehicle_Power': deque(maxlen=history_length),
            'Battery_Power': deque(maxlen=history_length),
            'Grid_Power': deque(maxlen=history_length),

            # ADD THESE NEW ENTRIES:
            'Grid_Reactive_Power': deque(maxlen=history_length),
            'Power_Factor': deque(maxlen=history_length),
            'Frequency': deque(maxlen=history_length),
            'THD': deque(maxlen=history_length),
            'Battery_SoC': deque(maxlen=history_length),
            'EV_SoC': deque(maxlen=history_length)
        }
        
        # For waveform data (will be generated from single values)
        self.waveform_data = {
            'Grid_Voltage': {
                'phaseA': deque(maxlen=history_length),
                'phaseB': deque(maxlen=history_length),
                'phaseC': deque(maxlen=history_length),
            },
            'Grid_Current': {
                'phaseA': deque(maxlen=history_length),
                'phaseB': deque(maxlen=history_length),
                'phaseC': deque(maxlen=history_length),
            }
        }
        
        # Waveform generation parameters
        self.frequency = 50.0  # Hz (grid frequency)
        self.phase_shift = (2 * np.pi) / 3  # 120 degrees in radians
        self.last_waveform_time = 0
    
    def start(self):
        """
        Start the UDP client and begin receiving data.
        
        This method creates a socket, binds it to the specified IP and port,
        and starts a background thread to receive and process incoming data.
        """
        if self.is_running:
            print("UDP client is already running")
            return
        
        # Try a few different ports if the first one fails
        ports_to_try = [self.port, 5001, 5002, 5003]
        success = False
        
        for port in ports_to_try:
            try:
                # Create a UDP socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                # Set socket options to reuse address (useful if the socket was recently closed)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Set a timeout so the socket doesn't block indefinitely
                self.socket.settimeout(1.0)
                
                # Bind the socket to the IP and port
                self.socket.bind((self.ip, port))
                
                print(f"UDP client listening on {self.ip}:{port}")
                self.port = port  # Update with the port that worked
                success = True
                break
                
            except Exception as e:
                print(f"Error binding to port {port}: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
        
        if not success:
            print("Failed to start UDP client - could not bind to any port")
            return False
            
        # Set the running flag and start the receive thread
        self.is_running = True
        self.receive_thread = threading.Thread(target=self._receive_data, daemon=True)
        self.receive_thread.start()
        
        return True
    
    def stop(self):
        """
        Stop the UDP client and clean up resources.
        """
        self.is_running = False
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        print("UDP client stopped")
    
    def _receive_data(self):
        """
        Background thread method to continuously receive and process UDP packets.
        The data is expected in CSV format as specified by the mentor's code.
        """
        start_time = time.time()
        packet_count = 0
        
        while self.is_running:
            try:
                # Attempt to receive data (will timeout after 1 second if no data)
                data, addr = self.socket.recvfrom(self.buffer_size)
                
                # Debug output to confirm receipt
                packet_count += 1
                if packet_count % 100 == 0:
                    print(f"UDP packets received: {packet_count}")
                
                # Record the current time for this data point
                current_time = time.time() - start_time
                self.time_history.append(current_time)
                
                # Process the received data
                self._process_data(data, current_time)
                
            except socket.timeout:
                # This is expected if no data is received within the timeout period
                pass
            except Exception as e:
                print(f"Error receiving data: {e}")
                time.sleep(0.1)  # Prevent tight loop if there's a persistent error
    
    def _process_data(self, data, timestamp):
        """
        Process received UDP data packet.
        
        The data is expected as a CSV string with values:
        Vd,Id,Vdc,Vev,Vpv,Iev,Ipv,Ppv,Pev,Pbattery,Pg,Qg,PF,Fg,THD,s1,s2,s3,s4,SoC_battery,SoC_EV
        
        Parameters:
        -----------
        data : bytes
            The raw data received from the UDP socket.
        timestamp : float
            The timestamp when the data was received.
        """
        try:
            # Decode the bytes to a string
            data_str = data.decode('utf-8').strip()
            
            # Split the CSV string into values
            values = data_str.split(',')
            
            # Ensure we have the expected number of values
            expected_values = 21  # Updated to match the new data format
            if len(values) != expected_values:
                print(f"Warning: Expected {expected_values} values, got {len(values)}")
                return
            
            # Parse the values into floats
            try:
                vd = float(values[0])         # Grid Voltage
                id_val = float(values[1])     # Grid Current
                vdc = float(values[2])        # DC Link Voltage
                vev = float(values[3])        # EV Voltage
                vpv = float(values[4])        # PV Voltage
                iev = float(values[5])        # EV Current
                ipv = float(values[6])        # PV Current
                ppv = float(values[7])        # PV Power
                pev = float(values[8])        # EV Power
                
                # New parameters from mentor:
                pbattery = float(values[9])   # Battery Power
                pgrid = float(values[10])     # Grid Power (now directly measured)
                qgrid = float(values[11])     # Grid Reactive Power
                power_factor = float(values[12])  # Power Factor
                frequency = float(values[13]) # Grid Frequency
                thd = float(values[14])       # Total Harmonic Distortion
                
                # Status indicators (int values 0-3)
                s1 = int(float(values[15]))   # PV panel status
                s2 = int(float(values[16]))   # EV status
                s3 = int(float(values[17]))   # Grid status
                s4 = int(float(values[18]))   # Battery status
                
                # State of charge values
                soc_battery = float(values[19])  # Battery SoC percentage
                soc_ev = float(values[20])       # EV SoC percentage
                
                # Ensure status values are within valid range (0-3)
                s1 = max(0, min(s1, 3))
                s2 = max(0, min(s2, 3))
                s3 = max(0, min(s3, 3))
                s4 = max(0, min(s4, 3))
                
            except ValueError as e:
                print(f"Error parsing data values: {e}")
                print(f"Raw data: {data_str}")
                return
                
            # Update latest data with all parameters
            self.latest_data['Grid_Voltage'] = vd
            self.latest_data['Grid_Current'] = id_val
            self.latest_data['DCLink_Voltage'] = vdc
            self.latest_data['ElectricVehicle_Voltage'] = vev
            self.latest_data['PhotoVoltaic_Voltage'] = vpv
            self.latest_data['ElectricVehicle_Current'] = iev
            self.latest_data['PhotoVoltaic_Current'] = ipv
            self.latest_data['PhotoVoltaic_Power'] = ppv
            self.latest_data['ElectricVehicle_Power'] = pev
            self.latest_data['Battery_Power'] = pbattery
            self.latest_data['Grid_Power'] = pgrid
            self.latest_data['Grid_Reactive_Power'] = qgrid
            self.latest_data['Power_Factor'] = power_factor
            self.latest_data['Frequency'] = frequency
            self.latest_data['THD'] = thd
            self.latest_data['S1_Status'] = s1
            self.latest_data['S2_Status'] = s2
            self.latest_data['S3_Status'] = s3
            self.latest_data['S4_Status'] = s4
            self.latest_data['Battery_SoC'] = soc_battery
            self.latest_data['EV_SoC'] = soc_ev
                
            # Update data history
            self.data_history['Grid_Voltage'].append(vd)
            self.data_history['Grid_Current'].append(id_val)
            self.data_history['DCLink_Voltage'].append(vdc)
            self.data_history['ElectricVehicle_Voltage'].append(vev)
            self.data_history['PhotoVoltaic_Voltage'].append(vpv)
            self.data_history['ElectricVehicle_Current'].append(iev)
            self.data_history['PhotoVoltaic_Current'].append(ipv)
            self.data_history['PhotoVoltaic_Power'].append(ppv)
            self.data_history['ElectricVehicle_Power'].append(pev)
            self.data_history['Battery_Power'].append(pbattery)
            self.data_history['Grid_Power'].append(pgrid)

            # ADD THESE NEW HISTORY UPDATES:
            self.data_history['Grid_Reactive_Power'].append(qgrid)
            self.data_history['Power_Factor'].append(power_factor)
            self.data_history['Frequency'].append(frequency)
            self.data_history['THD'].append(thd)
            self.data_history['Battery_SoC'].append(soc_battery)
            self.data_history['EV_SoC'].append(soc_ev)
            
            # Generate three-phase waveforms
            self._generate_waveforms(vd, id_val, timestamp)
            
        except Exception as e:
            print(f"Error processing data: {e}")
    
    def _generate_waveforms(self, voltage_amplitude, current_amplitude, timestamp):
        """
        Generate three-phase waveforms based on the single voltage and current values.
        
        Since the hardware provides only a single value (presumably the magnitude),
        we generate three-phase waveforms with the appropriate phase shifts.
        
        Parameters:
        -----------
        voltage_amplitude : float
            The voltage amplitude value from the hardware.
        current_amplitude : float
            The current amplitude value from the hardware.
        timestamp : float
            The current time value.
        """
        # Calculate the sine wave position based on time
        # Note: The frequency is assumed to be 50Hz
        # Scale the amplitude by sqrt(2) to convert from RMS to peak if needed
        # (depending on how the values are provided by the hardware)
        voltage_peak = voltage_amplitude * np.sqrt(2)  # Convert RMS to peak if needed
        current_peak = current_amplitude * np.sqrt(2)  # Convert RMS to peak if needed
        
        # Generate time-based angle for the sine waves
        angle = 2 * np.pi * self.latest_data.get('Frequency', self.frequency) * timestamp
        
        # Calculate values for the three voltage phases
        voltage_a = voltage_peak * np.sin(angle)
        voltage_b = voltage_peak * np.sin(angle - self.phase_shift)
        voltage_c = voltage_peak * np.sin(angle + self.phase_shift)
        
        # Calculate values for the three current phases
        # Add a small phase shift to simulate typical power factor
        # Get the actual power factor or use 0.95 as fallback
        actual_pf = self.latest_data.get('Power_Factor', 0.95)
        # Ensure power factor is in valid range (-1 to 1)
        actual_pf = max(-1.0, min(1.0, actual_pf))
        power_factor_angle = np.arccos(actual_pf)  # Assume power factor of 0.95 lagging
        current_a = current_peak * np.sin(angle - power_factor_angle)
        current_b = current_peak * np.sin(angle - self.phase_shift - power_factor_angle)
        current_c = current_peak * np.sin(angle + self.phase_shift - power_factor_angle)
        
        # Store the calculated values
        self.waveform_data['Grid_Voltage']['phaseA'].append(voltage_a)
        self.waveform_data['Grid_Voltage']['phaseB'].append(voltage_b)
        self.waveform_data['Grid_Voltage']['phaseC'].append(voltage_c)
        
        self.waveform_data['Grid_Current']['phaseA'].append(current_a)
        self.waveform_data['Grid_Current']['phaseB'].append(current_b)
        self.waveform_data['Grid_Current']['phaseC'].append(current_c)
    
    def get_latest_data(self):
        """
        Get the most recent data point for all parameters.
        
        Returns:
        --------
        dict
            Dictionary containing the latest value for each parameter.
        """
        return self.latest_data.copy()
    
    def get_waveform_data(self, waveform_type, n_points=300):
        """
        Get waveform data for voltage or current.
        
        Parameters:
        -----------
        waveform_type : str
            The type of waveform to get ('Grid_Voltage' or 'Grid_Current').
        n_points : int
            Number of data points to return.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, phase_a_data, phase_b_data, phase_c_data).
        """
        if waveform_type not in self.waveform_data:
            return np.array([]), np.array([]), np.array([]), np.array([])
        
        # Get the most recent n_points from the time history
        time_data = list(self.time_history)[-n_points:]
        
        # Get the most recent n_points for each phase
        phase_a = list(self.waveform_data[waveform_type]['phaseA'])[-n_points:]
        phase_b = list(self.waveform_data[waveform_type]['phaseB'])[-n_points:]
        phase_c = list(self.waveform_data[waveform_type]['phaseC'])[-n_points:]
        
        # Convert to numpy arrays (which is what the UI expects)
        return (np.array(time_data), np.array(phase_a), np.array(phase_b), np.array(phase_c))
    
    def get_parameter_history(self, parameter, n_points=300):
        """
        Get historical data for a specific parameter.
        
        Parameters:
        -----------
        parameter : str
            The name of the parameter to get history for.
        n_points : int
            Number of historical data points to return.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, parameter_data).
        """
        if parameter not in self.data_history:
            return np.array([]), np.array([])
        
        # Get the most recent n_points
        time_data = list(self.time_history)[-n_points:]
        param_data = list(self.data_history[parameter])[-n_points:]
        
        return np.array(time_data), np.array(param_data)
    
    def get_power_data(self, n_points=300):
        """
        Get power data for grid, PV, EV, and battery.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to return.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, grid_power, pv_power, ev_power, battery_power).
        """
        # Get the most recent n_points from time history
        time_data = list(self.time_history)[-n_points:]
        
        # Get power data
        grid_power = list(self.data_history['Grid_Power'])[-n_points:]
        pv_power = list(self.data_history['PhotoVoltaic_Power'])[-n_points:]
        ev_power = list(self.data_history['ElectricVehicle_Power'])[-n_points:]
        battery_power = list(self.data_history['Battery_Power'])[-n_points:]
        
        # Handle empty lists
        if not time_data:
            time_data = [0]
        if not grid_power:
            grid_power = [0] * len(time_data)
        if not pv_power:
            pv_power = [0] * len(time_data)
        if not ev_power:
            ev_power = [0] * len(time_data)
        if not battery_power:
            battery_power = [0] * len(time_data)
        
        # Convert to numpy arrays
        return (np.array(time_data), 
                np.array(grid_power), 
                np.array(pv_power), 
                np.array(ev_power), 
                np.array(battery_power))
    
    def is_connected(self):
        """
        Check if the UDP client is running and has received data.
        
        Returns:
        --------
        bool
            True if the client is running and has received data, False otherwise.
        """
        return self.is_running and len(self.time_history) > 0