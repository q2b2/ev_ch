# data_simulator.py
# This file contains functions to simulate real-time data for the EV charging system

import numpy as np
import time
from datetime import datetime

class DataSimulator:
    def __init__(self):
        # Initialize time and phase variables
        self.time_start = time.time()
        self.phase_a = 0
        self.phase_b = 2 * np.pi / 3  # 120 degrees phase shift
        self.phase_c = 4 * np.pi / 3  # 240 degrees phase shift
        
        # Initialize parameters with default values
        self.vg_rms = 155
        self.ig_rms = 9
        self.frequency = 50
        self.thd = 3
        self.power_factor = 0.99
        self.pv_power = 2000
        self.ev_power = -4000
        self.battery_power = 0
        self.v_dc = 80.19
        self.ev_voltage = 58.66
        self.ev_soc = 0
        self.demand_response = True
        self.v2g = True
        
        # For reactive power calculation
        self.apparent_power = self.vg_rms * self.ig_rms * 3  # 3-phase
        self.active_power = self.apparent_power * self.power_factor
        self.reactive_power = np.sqrt(self.apparent_power**2 - self.active_power**2)
    
    def update_parameters(self, parameter_name, value):
        """Update parameters based on user input"""
        if hasattr(self, parameter_name):
            setattr(self, parameter_name, value)
            
            # Update dependent parameters
            if parameter_name in ['vg_rms', 'ig_rms', 'power_factor']:
                self.apparent_power = self.vg_rms * self.ig_rms * 3  # 3-phase
                self.active_power = self.apparent_power * self.power_factor
                self.reactive_power = np.sqrt(self.apparent_power**2 - self.active_power**2)
        
    def get_time_data(self, n_points=8):
        """Generate time data for x-axis"""
        current_time = time.time() - self.time_start
        return np.linspace(current_time - 8, current_time, n_points)  # 8 seconds of history
    
    def get_voltage_data(self, n_points=8):
        """Generate three-phase voltage data"""
        t = self.get_time_data(n_points)
        amplitude = self.vg_rms * np.sqrt(2)  # Peak voltage from RMS
        omega = 2 * np.pi * self.frequency
        
        # Add small random noise for realism
        noise = np.random.normal(0, amplitude * 0.02, n_points)
        
        # Calculate three-phase voltages with 120° phase shifts
        va = amplitude * np.sin(omega * t + self.phase_a) + noise
        vb = amplitude * np.sin(omega * t + self.phase_b) + noise
        vc = amplitude * np.sin(omega * t + self.phase_c) + noise
        
        return t, va, vb, vc
    
    def get_current_data(self, n_points=8):
        """Generate three-phase current data"""
        t = self.get_time_data(n_points)
        amplitude = self.ig_rms * np.sqrt(2)  # Peak current from RMS
        omega = 2 * np.pi * self.frequency
        
        # Add small random noise for realism
        noise = np.random.normal(0, amplitude * 0.02, n_points)
        
        # Phase shift for power factor
        phi = np.arccos(self.power_factor)
        
        # Calculate three-phase currents with 120° phase shifts
        ia = amplitude * np.sin(omega * t + self.phase_a - phi) + noise
        ib = amplitude * np.sin(omega * t + self.phase_b - phi) + noise
        ic = amplitude * np.sin(omega * t + self.phase_c - phi) + noise
        
        return t, ia, ib, ic
    
    def get_power_data(self, n_points=8):
        """Generate power data for PV, EV, Grid, and Battery"""
        t = self.get_time_data(n_points)
        
        # Add small fluctuations for realism
        grid_power = np.ones(n_points) * self.pv_power + np.random.normal(0, 20, n_points)
        pv_power = np.ones(n_points) * self.pv_power + np.random.normal(0, 50, n_points)
        ev_power = np.ones(n_points) * self.ev_power + np.random.normal(0, 40, n_points)
        battery_power = np.ones(n_points) * self.battery_power + np.random.normal(0, 10, n_points)
        
        return t, grid_power, pv_power, ev_power, battery_power
    
    def get_gauge_data(self):
        """Return current values for gauges with small random fluctuations"""
        return {
            'frequency': self.frequency + np.random.normal(0, 0.05),
            'voltage_rms': self.vg_rms + np.random.normal(0, 1),
            'thd': self.thd + np.random.normal(0, 0.2),
            'active_power': self.active_power + np.random.normal(0, 50),
            'reactive_power': self.reactive_power + np.random.normal(0, 20),
            'current_rms': self.ig_rms + np.random.normal(0, 0.1)
        }
    
    def get_table_data(self):
        """Return current values for tables"""
        return {
            'charging_setting': {
                'PV power': self.pv_power,
                'EV power': self.ev_power,
                'Battery power': self.battery_power,
                'V_dc': self.v_dc
            },
            'ev_charging_setting': {
                'EV voltage': self.ev_voltage,
                'EV SoC': self.ev_soc,
                'Demand Response': self.demand_response,
                'V2G': self.v2g
            },
            'grid_settings': {
                'Vg_rms': self.vg_rms,
                'Ig_rms': self.ig_rms,
                'Frequency': self.frequency,
                'THD': self.thd,
                'Power factor': self.power_factor
            }
        }