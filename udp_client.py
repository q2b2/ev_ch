"""
UDP Client for receiving real-time data from the EV Charging Station.
This module handles receiving and parsing UDP packets from the hardware.
"""

import socket
import json
import threading
import time
import numpy as np
from collections import deque

class UDPClient:
    """
    A class to receive and parse UDP data packets from the EV Charging Station.
    
    This client listens on a specified IP and port for incoming UDP packets,
    parses them according to the expected format, and makes the data available
    to other components of the application.
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
        
        # Data storage
        self.latest_data = {}
        self.data_history = {}
        
        # For time series data, we'll use deques with a fixed maximum length
        self.time_history = deque(maxlen=history_length)
        
        # For waveform data
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
        
        # Initialize expected parameters
        self.expected_params = [
            'Grid_Voltage', 'Grid_Current', 'DCLink_Voltage', 
            'ElectricVehicle_Voltage', 'PhotoVoltaic_Voltage',
            'ElectricVehicle_Current', 'PhotoVoltaic_Current',
            'ElectricVehicle_Power', 'PhotoVoltaic_Power'
        ]
        
        # Initialize data history for each parameter
        for param in self.expected_params:
            self.data_history[param] = deque(maxlen=history_length)
            self.latest_data[param] = 0.0
    
    def start(self):
        """
        Start the UDP client and begin receiving data.
        
        This method creates a socket, binds it to the specified IP and port,
        and starts a background thread to receive and process incoming data.
        """
        if self.is_running:
            print("UDP client is already running")
            return
        
        try:
            # Create a UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Set a timeout so the socket doesn't block indefinitely
            self.socket.settimeout(1.0)
            
            # Bind the socket to the IP and port
            self.socket.bind((self.ip, self.port))
            
            print(f"UDP client listening on {self.ip}:{self.port}")
            
            # Set the running flag and start the receive thread
            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_data, daemon=True)
            self.receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting UDP client: {e}")
            self.stop()
            return False
    
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
        """Background thread method to continuously receive and process UDP packets."""
        start_time = time.time()
        
        while self.is_running:
            try:
                # Attempt to receive data (will timeout after 1 second if no data)
                data, addr = self.socket.recvfrom(self.buffer_size)
                
                # Add this debug print
                print(f"UDP packet received! Size: {len(data)} bytes from {addr}")
                
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
        
        This method parses the incoming data and updates the internal data structures.
        The actual parsing logic will depend on the data format agreed with your mentor.
        
        Parameters:
        -----------
        data : bytes
            The raw data received from the UDP socket.
        timestamp : float
            The timestamp when the data was received.
        """
        try:
            # Assuming data is in JSON format - adjust according to the actual format
            # This is the most common format, but your mentor should specify the exact format
            parsed_data = json.loads(data.decode('utf-8'))
            
            # Update latest data and history for each parameter
            for param in self.expected_params:
                if param in parsed_data:
                    value = float(parsed_data[param])
                    self.latest_data[param] = value
                    self.data_history[param].append(value)
            
            # Process waveform data (assuming they are included in the JSON)
            if 'waveforms' in parsed_data:
                waveforms = parsed_data['waveforms']
                
                # Process voltage waveforms
                if 'Grid_Voltage' in waveforms:
                    voltage = waveforms['Grid_Voltage']
                    if 'phaseA' in voltage:
                        self.waveform_data['Grid_Voltage']['phaseA'].append(voltage['phaseA'])
                    if 'phaseB' in voltage:
                        self.waveform_data['Grid_Voltage']['phaseB'].append(voltage['phaseB'])
                    if 'phaseC' in voltage:
                        self.waveform_data['Grid_Voltage']['phaseC'].append(voltage['phaseC'])
                
                # Process current waveforms
                if 'Grid_Current' in waveforms:
                    current = waveforms['Grid_Current']
                    if 'phaseA' in current:
                        self.waveform_data['Grid_Current']['phaseA'].append(current['phaseA'])
                    if 'phaseB' in current:
                        self.waveform_data['Grid_Current']['phaseB'].append(current['phaseB'])
                    if 'phaseC' in current:
                        self.waveform_data['Grid_Current']['phaseC'].append(current['phaseC'])
            
            # Alternative parsing for waveform data
            # If waveforms are not directly provided, we can generate them based on 
            # parameters like frequency and amplitude as shown in the mentor's JavaScript code
            if 'frequency' in parsed_data and 'voltage_amplitude' in parsed_data:
                self._generate_waveforms(parsed_data['frequency'], 
                                        parsed_data['voltage_amplitude'], 
                                        timestamp)
            
        except json.JSONDecodeError:
            print(f"Error decoding JSON data: {data}")
        except Exception as e:
            print(f"Error processing data: {e}")
    
    def _generate_waveforms(self, frequency, amplitude, timestamp):
        """
        Generate three-phase waveforms based on frequency and amplitude.
        Similar to the mentor's JavaScript code but adapted for Python.
        
        Parameters:
        -----------
        frequency : float
            The frequency of the waveforms in Hz.
        amplitude : float
            The amplitude of the waveforms.
        timestamp : float
            The current time value.
        """
        phase_shift = (2 * np.pi) / 3  # 120 degrees in radians
        
        # Calculate the point on the waveform at this timestamp
        x = timestamp * 2 * np.pi * frequency
        
        # Calculate values for the three phases
        phase_a = amplitude * np.sin(x)
        phase_b = amplitude * np.sin(x - phase_shift)
        phase_c = amplitude * np.sin(x + phase_shift)
        
        # Store the calculated values
        self.waveform_data['Grid_Voltage']['phaseA'].append(phase_a)
        self.waveform_data['Grid_Voltage']['phaseB'].append(phase_b)
        self.waveform_data['Grid_Voltage']['phaseC'].append(phase_c)
        
        # Also generate current waveforms with a different amplitude (for example)
        current_amplitude = amplitude / 10  # Just an example scaling factor
        
        self.waveform_data['Grid_Current']['phaseA'].append(current_amplitude * np.sin(x))
        self.waveform_data['Grid_Current']['phaseB'].append(current_amplitude * np.sin(x - phase_shift))
        self.waveform_data['Grid_Current']['phaseC'].append(current_amplitude * np.sin(x + phase_shift))
    
    def get_latest_data(self):
        """
        Get the most recent data point for all parameters.
        
        Returns:
        --------
        dict
            Dictionary containing the latest value for each parameter.
        """
        return self.latest_data.copy()
    
    def get_waveform_data(self, waveform_type, n_points=100):
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
    
    def get_parameter_history(self, parameter, n_points=100):
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
    
    def get_power_data(self, n_points=100):
        """
        Get power data for all power-related parameters.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to return.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, grid_power, pv_power, ev_power, battery_power).
        """
        # Get time data
        time_data = list(self.time_history)[-n_points:]
        
        # Calculate grid power - this is just an example, actual calculation may differ
        grid_power = []
        for i in range(min(len(time_data), len(self.data_history['Grid_Voltage']), len(self.data_history['Grid_Current']))):
            # P = V * I (simplified)
            idx = -n_points + i if i < n_points else i
            power = list(self.data_history['Grid_Voltage'])[idx] * list(self.data_history['Grid_Current'])[idx]
            grid_power.append(power)
        
        # Get PV and EV power data
        pv_power = list(self.data_history['PhotoVoltaic_Power'])[-n_points:]
        ev_power = list(self.data_history['ElectricVehicle_Power'])[-n_points:]
        
        # Battery power - this is often calculated rather than directly measured
        # For example: Battery power = Grid power + PV power - EV power
        battery_power = []
        min_length = min(len(grid_power), len(pv_power), len(ev_power))
        for i in range(min_length):
            battery_power.append(grid_power[i] + pv_power[i] - ev_power[i])
        
        # Convert to numpy arrays
        return (np.array(time_data), 
                np.array(grid_power if grid_power else [0]*len(time_data)), 
                np.array(pv_power if pv_power else [0]*len(time_data)), 
                np.array(ev_power if ev_power else [0]*len(time_data)), 
                np.array(battery_power if battery_power else [0]*len(time_data)))
    
    def is_connected(self):
        """
        Check if the UDP client is running and has received data.
        
        Returns:
        --------
        bool
            True if the client is running and has received data, False otherwise.
        """
        return self.is_running and len(self.time_history) > 0