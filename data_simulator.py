"""
Data Simulator for the EV Charging Station Monitor.
This module provides simulated or real data for the UI components.
"""

import time
import numpy as np
import random
from udp_client import UDPClient

class DataSimulator:
    """
    A class that provides data for the UI components.
    
    This class can operate in two modes:
    1. Simulation mode: Generate random but realistic data
    2. Real-time mode: Get data from a UDP client connected to real hardware
    """
    
    def __init__(self, use_real_data=False, udp_ip="0.0.0.0", udp_port=5000):
        """
        Initialize the data simulator.
        
        Parameters:
        -----------
        use_real_data : bool
            If True, use real data from UDP. If False, generate simulated data.
        udp_ip : str
            IP address to listen on for UDP packets.
        udp_port : int
            Port to listen on for UDP packets.
        """
        self.time_start = time.time()
        
        # Data parameters (used for simulation mode)
        self.frequency = 50.0  # Hz
        self.voltage_amplitude = 220.0  # V (peak)
        self.current_amplitude = 10.0   # A (peak)
        
        # Power values
        self.pv_power = 2000  # W
        self.ev_power = -4000  # W (negative for consumption)
        self.battery_power = 0  # W
        self.v_dc = 80.19  # V
        
        # EV parameters
        self.ev_voltage = 58.66  # V
        self.ev_soc = 0  # %
        self.demand_response = True
        self.v2g = True  # Vehicle-to-Grid enabled
        
        # Grid parameters
        self.vg_rms = 155  # V
        self.ig_rms = 9  # A
        self.thd = 3  # % Total Harmonic Distortion
        self.power_factor = 0.99
        
        # Real-time data settings
        self.use_real_data = use_real_data
        self.udp_client = None
        
        # Initialize UDP client for real-time data if needed
        if self.use_real_data:
            self.udp_client = UDPClient(ip=udp_ip, port=udp_port)
            success = self.udp_client.start()
            if not success:
                print("Failed to start UDP client. Falling back to simulated data.")
                self.use_real_data = False
    
    def get_time_data(self, n_points=100):
        """
        Generate time data for x-axis.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to generate.
            
        Returns:
        --------
        ndarray
            Array of time values.
        """
        current_time = time.time() - self.time_start
        return np.linspace(current_time - 5, current_time, n_points)
    
    def get_voltage_data(self, n_points=100):
        """
        Get three-phase voltage data.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to get.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, va_data, vb_data, vc_data).
        """
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get real data from UDP client
            return self.udp_client.get_waveform_data('Grid_Voltage', n_points)
        else:
            # Generate simulated data
            t = self.get_time_data(n_points)
            phase_shift = (2 * np.pi) / 3  # 120 degrees
            
            # Create sine waves for each phase
            va = self.voltage_amplitude * np.sin(2 * np.pi * self.frequency * t)
            vb = self.voltage_amplitude * np.sin(2 * np.pi * self.frequency * t - phase_shift)
            vc = self.voltage_amplitude * np.sin(2 * np.pi * self.frequency * t + phase_shift)
            
            # Add some random noise to make it look more realistic
            noise = np.random.normal(0, 0.01 * self.voltage_amplitude, n_points)
            va += noise
            vb += noise
            vc += noise
            
            return t, va, vb, vc
    
    def get_current_data(self, n_points=100):
        """
        Get three-phase current data.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to get.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, ia_data, ib_data, ic_data).
        """
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get real data from UDP client
            return self.udp_client.get_waveform_data('Grid_Current', n_points)
        else:
            # Generate simulated data
            t = self.get_time_data(n_points)
            phase_shift = (2 * np.pi) / 3  # 120 degrees
            
            # Create sine waves for each phase with a slight power factor lag
            power_factor_angle = np.arccos(self.power_factor)
            ia = self.current_amplitude * np.sin(2 * np.pi * self.frequency * t - power_factor_angle)
            ib = self.current_amplitude * np.sin(2 * np.pi * self.frequency * t - phase_shift - power_factor_angle)
            ic = self.current_amplitude * np.sin(2 * np.pi * self.frequency * t + phase_shift - power_factor_angle)
            
            # Add some random noise to make it look more realistic
            noise = np.random.normal(0, 0.02 * self.current_amplitude, n_points)
            ia += noise
            ib += noise
            ic += noise
            
            return t, ia, ib, ic
    
    def get_power_data(self, n_points=100):
        """
        Get power data for grid, PV, EV, and battery.
        
        Parameters:
        -----------
        n_points : int
            Number of data points to get.
            
        Returns:
        --------
        tuple
            A tuple containing (time_data, p_grid, p_pv, p_ev, p_battery).
        """
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get real data from UDP client
            return self.udp_client.get_power_data(n_points)
        else:
            # Generate simulated data
            t = self.get_time_data(n_points)
            
            # Create slightly varying power values around the base values
            p_pv = self.pv_power + np.random.normal(0, 50, n_points)
            p_ev = self.ev_power + np.random.normal(0, 100, n_points)
            p_battery = self.battery_power + np.random.normal(0, 20, n_points)
            
            # Grid power = -(PV + EV + Battery)
            p_grid = -(p_pv + p_ev + p_battery)
            
            return t, p_grid, p_pv, p_ev, p_battery
    
    def get_table_data(self):
        """
        Get data for the tables in the UI.
        
        Returns:
        --------
        dict
            Dictionary containing data for all tables.
        """
        if self.use_real_data and self.udp_client:
            # Get latest data from UDP client
            latest_data = self.udp_client.get_latest_data()
            
            # Map UDP data to table data
            table_data = {
                "charging_setting": {
                    "PV power": latest_data.get('PhotoVoltaic_Power', self.pv_power),
                    "EV power": latest_data.get('ElectricVehicle_Power', self.ev_power),
                    "Battery power": self.battery_power,  # May need to be calculated
                    "V_dc": latest_data.get('DCLink_Voltage', self.v_dc)
                },
                "ev_charging_setting": {
                    "EV voltage": latest_data.get('ElectricVehicle_Voltage', self.ev_voltage),
                    "EV SoC": self.ev_soc,  # This might not come from UDP
                    "Demand Response": self.demand_response,
                    "V2G": self.v2g
                },
                "grid_settings": {
                    "Vg_rms": latest_data.get('Grid_Voltage', self.vg_rms),
                    "Ig_rms": latest_data.get('Grid_Current', self.ig_rms),
                    "Frequency": self.frequency,
                    "THD": self.thd,
                    "Power factor": self.power_factor
                }
            }
            
            return table_data
        else:
            # Return simulated data
            return {
                "charging_setting": {
                    "PV power": self.pv_power + random.uniform(-5, 5),
                    "EV power": self.ev_power + random.uniform(-10, 10),
                    "Battery power": self.battery_power + random.uniform(-2, 2),
                    "V_dc": self.v_dc + random.uniform(-0.1, 0.1)
                },
                "ev_charging_setting": {
                    "EV voltage": self.ev_voltage + random.uniform(-0.05, 0.05),
                    "EV SoC": self.ev_soc + (random.uniform(0, 0.01) if self.ev_soc < 100 else 0),
                    "Demand Response": self.demand_response,
                    "V2G": self.v2g
                },
                "grid_settings": {
                    "Vg_rms": self.vg_rms + random.uniform(-0.5, 0.5),
                    "Ig_rms": self.ig_rms + random.uniform(-0.1, 0.1),
                    "Frequency": self.frequency + random.uniform(-0.01, 0.01),
                    "THD": self.thd + random.uniform(-0.05, 0.05),
                    "Power factor": min(1.0, self.power_factor + random.uniform(-0.005, 0.005))
                }
            }
    
    def get_gauge_data(self):
        """
        Get data for the gauge widgets.
        
        Returns:
        --------
        dict
            Dictionary containing data for all gauges.
        """
        if self.use_real_data and self.udp_client:
            # Get latest data from UDP client
            latest_data = self.udp_client.get_latest_data()
            
            # Return gauge data based on UDP data
            return {
                "frequency": self.frequency,  # This might be calculated or set separately
                "voltage_rms": latest_data.get('Grid_Voltage', self.vg_rms),
                "current_rms": latest_data.get('Grid_Current', self.ig_rms),
                "thd": self.thd,
                "active_power": latest_data.get('Grid_Voltage', self.vg_rms) * latest_data.get('Grid_Current', self.ig_rms) * self.power_factor,
                "reactive_power": latest_data.get('Grid_Voltage', self.vg_rms) * latest_data.get('Grid_Current', self.ig_rms) * np.sin(np.arccos(self.power_factor))
            }
        else:
            # Return simulated gauge data
            active_power = self.vg_rms * self.ig_rms * self.power_factor
            reactive_power = self.vg_rms * self.ig_rms * np.sin(np.arccos(self.power_factor))
            
            return {
                "frequency": self.frequency + random.uniform(-0.02, 0.02),
                "voltage_rms": self.vg_rms + random.uniform(-1, 1),
                "current_rms": self.ig_rms + random.uniform(-0.2, 0.2),
                "thd": self.thd + random.uniform(-0.1, 0.1),
                "active_power": active_power + random.uniform(-20, 20),
                "reactive_power": reactive_power + random.uniform(-10, 10)
            }
    
    def update_parameters(self, parameter, value):
        """
        Update internal parameters based on user input.
        
        Parameters:
        -----------
        parameter : str
            The name of the parameter to update.
        value : float or bool
            The new value for the parameter.
        """
        # Map user-friendly parameter names to class attributes
        parameter_map = {
            "pv_power": "pv_power",
            "ev_power": "ev_power",
            "battery_power": "battery_power",
            "ev_voltage": "ev_voltage",
            "ev_soc": "ev_soc",
            "demand_response": "demand_response",
            "v2g": "v2g",
            "vg_rms": "vg_rms",
            "ig_rms": "ig_rms",
            "frequency": "frequency",
            "thd": "thd",
            "power_factor": "power_factor"
        }
        
        # If we're in real data mode, some parameters may not be updatable
        if self.use_real_data:
            print(f"Warning: Cannot update {parameter} in real-time data mode")
            return
            
        # Update the parameter if it's in our map
        if parameter in parameter_map:
            attr_name = parameter_map[parameter]
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)
                print(f"Updated {parameter} to {value}")
            else:
                print(f"Error: Attribute {attr_name} not found")
        else:
            print(f"Error: Unknown parameter {parameter}")
    
    def shutdown(self):
        """
        Perform any cleanup needed when the application is closing.
        """
        if self.use_real_data and self.udp_client:
            self.udp_client.stop()