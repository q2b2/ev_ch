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
        
        # Battery parameters - ADD THIS LINE HERE
        self.battery_soc = 50.0  # Initial battery SoC at 50%

        # Grid parameters
        self.vg_rms = 155  # V
        self.ig_rms = 9  # A
        self.thd = 3  # % Total Harmonic Distortion
        self.power_factor = 0.99
        
        # Grid power parameters as mentioned by mentor
        self.p_grid = np.sqrt(3)*self.vg_rms * self.ig_rms * self.power_factor  # Active power
        self.q_grid = self.vg_rms * self.ig_rms * np.sin(np.arccos(self.power_factor))  # Reactive power
        # S_grid = sqrt(P_grid^2 + Q_grid^2) - this is calculated when needed
        
        # Real-time data settings
        self.use_real_data = use_real_data
        self.udp_client = None
        
        # Parameter update tracking
        self.update_parameter_applied = False
        self.last_updated_parameters = {}  # Store manually updated parameters
        
        # Initialize UDP client for real-time data if needed
        if self.use_real_data:
            print("Initializing UDP client for real data...")
            self.udp_client = UDPClient(ip=udp_ip, port=udp_port)
            success = self.udp_client.start()
            if not success:
                print("Failed to start UDP client. Falling back to simulated data.")
                self.use_real_data = False
                self.udp_client = None
            else:
                print("UDP client started successfully.")
    
    def get_time_data(self, n_points=300):
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
        return np.linspace(current_time - 0.1, current_time, n_points)
    
    def get_voltage_data(self, n_points=None):
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
        if self.use_real_data and self.udp_client:
            # Pass None to get all available data
            return self.udp_client.get_waveform_data('Grid_Voltage', n_points=None)
        else:
            # Default to 300 points for simulation if n_points is None
            sim_n_points = 300 if n_points is None else n_points

            # Generate simulated data
            t = self.get_time_data(sim_n_points)
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
    
    def get_current_data(self, n_points=None):
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
        if self.use_real_data and self.udp_client:
            # Pass None to get all available data
            return self.udp_client.get_waveform_data('Grid_Current', n_points=None)
        else:
            # Default to 300 points for simulation if n_points is None
            sim_n_points = 300 if n_points is None else n_points
            # Generate simulated data
            t = self.get_time_data(sim_n_points)
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
    
    def get_power_data(self, n_points=None):
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
        if self.use_real_data and self.udp_client:
            # Pass None to get all available data
            return self.udp_client.get_power_data(n_points=None)
        else:
            # Default to 300 points for simulation if n_points is None
            sim_n_points = 300 if n_points is None else n_points
            # Generate simulated data
            t = self.get_time_data(sim_n_points)
            
            # Create slightly varying power values around the base values
            p_pv = np.array([self.pv_power + random.uniform(-50, 50) for _ in range(sim_n_points)])
            p_ev = np.array([self.ev_power + random.uniform(-100, 100) for _ in range(sim_n_points)])
            p_battery = np.array([self.battery_power + random.uniform(-20, 20) for _ in range(sim_n_points)])
            
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
        # Create the base table data structure
        table_data = {
            "charging_setting": {
                "PV power": 0,
                "EV power": 0, 
                "Battery power": 0,
                "V_dc": 0
            },
            "ev_charging_setting": {
                "EV voltage": 0, 
                "EV SoC": 0,
                "Demand Response": True,
                "V2G": True
            },
            "grid_settings": {
                "Vg_rms": 0, 
                "Ig_rms": 0,
                "Frequency": 0,
                "THD": 0,
                "Power factor": 0
            }
        }
        
        # Get data based on mode (real or simulated)
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get latest data from UDP client
            latest_data = self.udp_client.get_latest_data()
            
            # Map UDP data to table data 
            table_data["charging_setting"]["PV power"] = latest_data.get('PhotoVoltaic_Power', 0)
            table_data["charging_setting"]["EV power"] = latest_data.get('ElectricVehicle_Power', 0)
            table_data["charging_setting"]["Battery power"] = latest_data.get('Battery_Power', 0)
            table_data["charging_setting"]["V_dc"] = latest_data.get('DCLink_Voltage', 0)
            
            table_data["ev_charging_setting"]["EV voltage"] = latest_data.get('ElectricVehicle_Voltage', 0)
            table_data["ev_charging_setting"]["EV SoC"] = latest_data.get('EV_SoC', 0)
            # These values may not come from UDP, use stored values
            table_data["ev_charging_setting"]["Demand Response"] = self.demand_response
            table_data["ev_charging_setting"]["V2G"] = self.v2g
            
            # Grid settings come directly from UDP data
            table_data["grid_settings"]["Vg_rms"] = latest_data.get('Grid_Voltage', 0)
            table_data["grid_settings"]["Ig_rms"] = latest_data.get('Grid_Current', 0)
            table_data["grid_settings"]["Frequency"] = latest_data.get('Frequency', 50)
            table_data["grid_settings"]["THD"] = latest_data.get('THD', 0)
            table_data["grid_settings"]["Power factor"] = latest_data.get('Power_Factor', 0.95)
        else:
            # If a parameter was manually updated, use it
            if self.update_parameter_applied:
                # For charging settings
                if "PV power" in self.last_updated_parameters:
                    table_data["charging_setting"]["PV power"] = self.pv_power
                else:
                    table_data["charging_setting"]["PV power"] = self.pv_power + random.uniform(-5, 5)
                
                if "EV power" in self.last_updated_parameters:
                    table_data["charging_setting"]["EV power"] = self.ev_power
                else:
                    table_data["charging_setting"]["EV power"] = self.ev_power + random.uniform(-10, 10)
                
                if "Battery power" in self.last_updated_parameters:
                    table_data["charging_setting"]["Battery power"] = self.battery_power
                else:
                    table_data["charging_setting"]["Battery power"] = self.battery_power + random.uniform(-2, 2)
                
                table_data["charging_setting"]["V_dc"] = self.v_dc + random.uniform(-0.1, 0.1)
                
                # For EV charging settings
                if "EV voltage" in self.last_updated_parameters:
                    table_data["ev_charging_setting"]["EV voltage"] = self.ev_voltage
                else:
                    table_data["ev_charging_setting"]["EV voltage"] = self.ev_voltage + random.uniform(-0.05, 0.05)
                
                if "EV SoC" in self.last_updated_parameters:
                    table_data["ev_charging_setting"]["EV SoC"] = self.ev_soc
                else:
                    table_data["ev_charging_setting"]["EV SoC"] = self.ev_soc + (random.uniform(0, 0.01) if self.ev_soc < 100 else 0)
                
                table_data["ev_charging_setting"]["Demand Response"] = self.demand_response
                table_data["ev_charging_setting"]["V2G"] = self.v2g
                
                # For grid settings
                if "Vg_rms" in self.last_updated_parameters:
                    table_data["grid_settings"]["Vg_rms"] = self.vg_rms
                else:
                    table_data["grid_settings"]["Vg_rms"] = self.vg_rms + random.uniform(-0.5, 0.5)
                
                if "Ig_rms" in self.last_updated_parameters:
                    table_data["grid_settings"]["Ig_rms"] = self.ig_rms
                else:
                    table_data["grid_settings"]["Ig_rms"] = self.ig_rms + random.uniform(-0.1, 0.1)
                
                if "Frequency" in self.last_updated_parameters:
                    table_data["grid_settings"]["Frequency"] = self.frequency
                else:
                    table_data["grid_settings"]["Frequency"] = self.frequency + random.uniform(-0.01, 0.01)
                
                if "THD" in self.last_updated_parameters:
                    table_data["grid_settings"]["THD"] = self.thd
                else:
                    table_data["grid_settings"]["THD"] = self.thd + random.uniform(-0.05, 0.05)
                
                if "Power factor" in self.last_updated_parameters:
                    table_data["grid_settings"]["Power factor"] = self.power_factor
                else:
                    table_data["grid_settings"]["Power factor"] = min(1.0, self.power_factor + random.uniform(-0.005, 0.005))
                
                # Reset the update flag after one use
                self.update_parameter_applied = False
                
            else:
                # No manual updates, use simulated data with random variations
                table_data["charging_setting"]["PV power"] = self.pv_power + random.uniform(-5, 5)
                table_data["charging_setting"]["EV power"] = self.ev_power + random.uniform(-10, 10)
                table_data["charging_setting"]["Battery power"] = self.battery_power + random.uniform(-2, 2)
                table_data["charging_setting"]["V_dc"] = self.v_dc + random.uniform(-0.1, 0.1)
                
                table_data["ev_charging_setting"]["EV voltage"] = self.ev_voltage + random.uniform(-0.05, 0.05)
                table_data["ev_charging_setting"]["EV SoC"] = self.ev_soc + (random.uniform(0, 0.01) if self.ev_soc < 100 else 0)
                table_data["ev_charging_setting"]["Demand Response"] = self.demand_response
                table_data["ev_charging_setting"]["V2G"] = self.v2g
                
                table_data["grid_settings"]["Vg_rms"] = self.vg_rms + random.uniform(-0.5, 0.5)
                table_data["grid_settings"]["Ig_rms"] = self.ig_rms + random.uniform(-0.1, 0.1)
                table_data["grid_settings"]["Frequency"] = self.frequency + random.uniform(-0.01, 0.01)
                table_data["grid_settings"]["THD"] = self.thd + random.uniform(-0.05, 0.05)
                table_data["grid_settings"]["Power factor"] = min(1.0, self.power_factor + random.uniform(-0.005, 0.005))
        
        return table_data
    
    def get_gauge_data(self):
        """
        Get data for the gauge widgets.
        
        Returns:
        --------
        dict
            Dictionary containing data for all gauges.
        """
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get latest data from UDP client
            latest_data = self.udp_client.get_latest_data()
            
            # Using mentor's formula: S_grid = sqrt(P_grid^2 + Q_grid^2)
            # P_grid and Q_grid are directly provided in the UDP data
            p_grid = latest_data.get('Grid_Power', 0)  
            q_grid = latest_data.get('Grid_Reactive_Power', 0)
            
            # Return gauge data based on UDP data
            return {
                "frequency": latest_data.get('Frequency', 50),
                "voltage_rms": latest_data.get('Grid_Voltage', 0),
                "current_rms": latest_data.get('Grid_Current', 0),
                "thd": latest_data.get('THD', 0),
                "active_power": p_grid,
                "reactive_power": q_grid
            }
        else:
            # Calculate or use stored values for active and reactive power
            # Using the power triangle relationship and power factor
            active_power = self.vg_rms * self.ig_rms * self.power_factor
            reactive_power = self.vg_rms * self.ig_rms * np.sin(np.arccos(self.power_factor))
            
            # Return simulated gauge data
            return {
                "frequency": self.frequency + random.uniform(-0.02, 0.02),
                "voltage_rms": self.vg_rms + random.uniform(-1, 1),
                "current_rms": self.ig_rms + random.uniform(-0.2, 0.2),
                "thd": self.thd + random.uniform(-0.1, 0.1),
                "active_power": active_power + random.uniform(-20, 20),
                "reactive_power": reactive_power + random.uniform(-10, 10)
            }
    
    def get_hub_data(self):
        """
        Get data for the Smart Energy Hub.
        
        Returns:
        --------
        dict
            Dictionary containing hub component status values.
        """
        if self.use_real_data and self.udp_client and self.udp_client.is_connected():
            # Get real data from UDP client
            latest_data = self.udp_client.get_latest_data()
            
            return {
                "s1_status": latest_data.get('S1_Status', 0),
                "s2_status": latest_data.get('S2_Status', 0),
                "s3_status": latest_data.get('S3_Status', 0),
                "s4_status": latest_data.get('S4_Status', 0),
                "ev_soc": latest_data.get('EV_SoC', self.ev_soc),
                "battery_soc": latest_data.get('Battery_SoC', self.battery_soc),
            }
        else:
            # Use consistent SoC values from stored parameters
            return {
                "s1_status": random.randint(2, 2),
                "s2_status": random.randint(0, 0),
                "s3_status": random.randint(0, 0),
                "s4_status": random.randint(2, 2),
                "ev_soc": self.ev_soc,  # Use exact same stored value
                "battery_soc": self.battery_soc  # Use exact same stored value
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
            "battery_soc": "battery_soc",  # Added this mapping
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
                
                # Record that this parameter was manually updated
                self.update_parameter_applied = True
                self.last_updated_parameters[parameter] = value
                
                # Special handling for EV SoC
                if parameter == "ev_soc":
                    # Ensure EV SoC stays within valid range
                    self.ev_soc = min(100.0, max(0.0, value))
                
                # Special handling for Battery SoC
                if parameter == "battery_soc":
                    # Ensure Battery SoC stays within valid range
                    self.battery_soc = min(100.0, max(0.0, value))
                
                # If we're updating power-related parameters, recalculate grid power
                if parameter in ["vg_rms", "ig_rms", "power_factor"]:
                    # Update grid power parameters
                    self.p_grid = np.sqrt(3)* self.vg_rms * self.ig_rms * self.power_factor
                    self.q_grid = self.vg_rms * self.ig_rms * np.sin(np.arccos(self.power_factor))
                
                print(f"Updated {parameter} to {value}")
            else:
                print(f"Error: Attribute {attr_name} not found")
        else:
            print(f"Error: Unknown parameter {parameter}")
    
    def apply_parameter_updates(self):
        """
        Force application of parameter updates.
        This ensures that manually updated parameters are applied immediately.
        """
        self.update_parameter_applied = True
    
    def shutdown(self):
        """
        Perform any cleanup needed when the application is closing.
        """
        if self.use_real_data and self.udp_client:
            print("Shutting down UDP client...")
            self.udp_client.stop()