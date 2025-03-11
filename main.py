# main.py
# Main application for the EV Charging Station Monitor

import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QVBoxLayout, QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
import argparse

# Import custom modules
from data_simulator import DataSimulator
from data_logger import DataLogger
from config_manager import ConfigManager
from ui_components import GraphWidget, GaugeWidget, TableWidget, ButtonWidget

class EVChargingMonitor(QMainWindow):
    """Main application window for EV Charging Station Monitor"""
    
        # In the __init__ method of EVChargingMonitor class, update to use UDP client:
    def __init__(self, use_real_data=False, udp_ip="0.0.0.0", udp_port=5000):
        super().__init__()
        
        # Initialize components with real data option
        self.data_simulator = DataSimulator(use_real_data=use_real_data, 
                                        udp_ip=udp_ip, 
                                        udp_port=udp_port)
        self.data_logger = DataLogger()
        self.config_manager = ConfigManager()
        
        # Dictionary to track widgets for layout management
        self.widgets = {}
        
        # Set up the UI
        self.setupUI()
        
        # Set up update timer (50ms update rate = 20 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)
        
        # Apply saved configurations
        self.apply_saved_layouts()
        
        # Flag to track if layout has changed
        self.layout_changed = False
    
    def setupUI(self):
        """Set up the main UI components"""
        # Set window properties
        self.setWindowTitle("EV Charging Station Monitor")
        self.setGeometry(100, 100, 1280, 800)
        
        # Central widget - use a single widget for everything
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Don't set any layout - we're using absolute positioning
        # (Removing the line that was causing the error)
        
        # Create all UI elements - everything directly on the central widget
        self.setup_graphs()
        self.setup_tables()
        self.setup_gauges()
        self.setup_control_buttons()
        
        # Create a QLabel for the logo
        self.logo_label = QLabel(self.central_widget)
        self.logo_label.setGeometry(850, 10, 150, 50)  # Adjust position and size as needed
        logo_pixmap = QPixmap("QEERI_logo.png")
        self.logo_label.setPixmap(logo_pixmap.scaled(150, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.show()
    
    def setup_graphs(self):
        """Create and configure graph widgets"""
        # Voltage graph
        self.voltage_graph = GraphWidget(self.central_widget, "Voltage Graph", "voltage_graph")
        self.voltage_graph.setGeometry(20, 20, 400, 280)
        self.voltage_graph.setup_voltage_graph()
        self.voltage_graph.show()
        self.widgets["voltage_graph"] = self.voltage_graph
        
        # Current graph
        self.current_graph = GraphWidget(self.central_widget, "Current Graph", "current_graph")
        self.current_graph.setGeometry(430, 20, 400, 280)
        self.current_graph.setup_current_graph()
        self.current_graph.show()
        self.widgets["current_graph"] = self.current_graph
        
        # Power graph
        self.power_graph = GraphWidget(self.central_widget, "Power Graph", "power_graph")
        self.power_graph.setGeometry(840, 20, 400, 280)
        self.power_graph.setup_power_graph()
        self.power_graph.show()
        self.widgets["power_graph"] = self.power_graph
    
    def setup_tables(self):
        """Create and configure table widgets"""
        # Charging Setting table
        self.charging_setting_table = TableWidget(self.central_widget, "Charging Setting", "charging_table")
        self.charging_setting_table.setGeometry(20, 310, 300, 200)
        self.charging_setting_table.setup_charging_setting_table()
        self.charging_setting_table.save_clicked.connect(self.on_table_save)
        self.charging_setting_table.show()
        self.widgets["charging_table"] = self.charging_setting_table
        
        # EV Charging Setting table
        self.ev_charging_table = TableWidget(self.central_widget, "EV Charging Setting", "ev_charging_table")
        self.ev_charging_table.setGeometry(330, 310, 300, 200)
        self.ev_charging_table.setup_ev_charging_setting_table()
        self.ev_charging_table.save_clicked.connect(self.on_table_save)
        self.ev_charging_table.show()
        self.widgets["ev_charging_table"] = self.ev_charging_table
        
        # Grid Settings table
        self.grid_settings_table = TableWidget(self.central_widget, "Grid Settings", "grid_settings_table")
        self.grid_settings_table.setGeometry(640, 310, 300, 250)
        self.grid_settings_table.setup_grid_settings_table()
        self.grid_settings_table.save_clicked.connect(self.on_table_save)
        self.grid_settings_table.show()
        self.widgets["grid_settings_table"] = self.grid_settings_table
    
    def setup_gauges(self):
        """Create and configure gauge widgets"""
        # Create gauges
        gauge_configs = [
            {"title": "Frequency", "min": 45, "max": 55, "units": "Hz", "id": "frequency_gauge"},
            {"title": "Voltage RMS", "min": 0, "max": 250, "units": "V", "id": "voltage_gauge"},
            {"title": "THD", "min": 0, "max": 10, "units": "%", "id": "thd_gauge"},
            {"title": "Active Power", "min": -5000, "max": 3000, "units": "W", "id": "active_power_gauge"},
            {"title": "Reactive Power", "min": -2000, "max": 2000, "units": "VAr", "id": "reactive_power_gauge"},
            {"title": "Current RMS", "min": 0, "max": 20, "units": "A", "id": "current_gauge"}
        ]
        
        # Create gauges with initial positions
        self.gauges = []
        
        for i, config in enumerate(gauge_configs):
            # Position gauges in a grid (3x2)
            col = i % 3
            row = i // 3
            x = 20 + col * 220
            y = 520 + row * 220
            
            gauge = GaugeWidget(
                self.central_widget, 
                config["title"], 
                config["min"], 
                config["max"],
                config["units"],
                config["id"]
            )
            
            gauge.setGeometry(x, y, 100, 100)
            gauge.show()
            
            self.gauges.append(gauge)
            self.widgets[config["id"]] = gauge
    
    def setup_control_buttons(self):
        """Create control buttons for logging"""
        # Create button container as a draggable widget
        self.button_widget = ButtonWidget(self.central_widget, "Controls", "control_buttons")
        self.button_widget.setGeometry(680, 520, 300, 200)
        
        # Add buttons to the widget
        self.button_widget.add_button("Start Logging", "green", self.start_logging)
        self.button_widget.add_button("Stop Logging", "red", self.stop_logging)
        self.button_widget.add_button("Save Layout", "blue", self.save_layout)
        
        # Set initial state
        self.button_widget.get_button(1).setEnabled(False)  # Stop button initially disabled
        
        self.button_widget.show()
        self.widgets["control_buttons"] = self.button_widget
    
    def update_data(self):
        """Update all UI components with new data from the simulator"""
        # Update voltage graph
        time_data, va_data, vb_data, vc_data = self.data_simulator.get_voltage_data()
        self.voltage_graph.update_voltage_data(time_data, va_data, vb_data, vc_data)
        
        # Update current graph
        time_data, ia_data, ib_data, ic_data = self.data_simulator.get_current_data()
        self.current_graph.update_current_data(time_data, ia_data, ib_data, ic_data)
        
        # Update power graph
        time_data, p_grid, p_pv, p_ev, p_battery = self.data_simulator.get_power_data()
        self.power_graph.update_power_data(time_data, p_grid, p_pv, p_ev, p_battery)
        
        # Update tables
        table_data = self.data_simulator.get_table_data()
        self.charging_setting_table.update_values(table_data["charging_setting"])
        self.ev_charging_table.update_values(table_data["ev_charging_setting"])
        self.grid_settings_table.update_values(table_data["grid_settings"])
        
        # Update gauges
        gauge_data = self.data_simulator.get_gauge_data()
        self.gauges[0].set_value(gauge_data["frequency"])
        self.gauges[1].set_value(gauge_data["voltage_rms"])
        self.gauges[2].set_value(gauge_data["thd"])
        self.gauges[3].set_value(gauge_data["active_power"])
        self.gauges[4].set_value(gauge_data["reactive_power"])
        self.gauges[5].set_value(gauge_data["current_rms"])
        
        # If logging is active, log the data
        if self.data_logger.is_logging:
            self.data_logger.log_data(self.data_simulator)
    
    def on_table_save(self, table_type, input_values):
        """Handle save button click from tables"""
        print(f"Saving values from {table_type}: {input_values}")
        
        # Update simulator with new values
        for param_name, value in input_values.items():
            # Map param_name to simulator attribute name (lowercase with underscores)
            attr_name = param_name.lower().replace(" ", "_")
            self.data_simulator.update_parameters(attr_name, value)
    
    def start_logging(self):
        """Start data logging"""
        self.data_logger.start_logging()
        self.button_widget.get_button(0).setEnabled(False)  # Start button
        self.button_widget.get_button(1).setEnabled(True)   # Stop button
    
    def stop_logging(self):
        """Stop data logging"""
        log_file = self.data_logger.stop_logging()
        self.button_widget.get_button(0).setEnabled(True)   # Start button
        self.button_widget.get_button(1).setEnabled(False)  # Stop button
        
        print(f"Data logged to: {log_file}")
    
    def save_layout(self):
        """Save the current layout configuration"""
        self.config_manager.save_all_configs(self.widgets)
        self.layout_changed = False
        print("Layout configuration saved")
    
    def widget_moved(self):
        """Called when a widget is moved or resized"""
        self.layout_changed = True
    
    def apply_saved_layouts(self):
        """Apply saved layout configurations to widgets"""
        configs = self.config_manager.load_all_configs()
        
        # If no saved configs, use default layout
        if not configs:
            return
            
        # Apply configs to widgets
        for widget_id, widget in self.widgets.items():
            if widget_id in configs:
                self.config_manager.apply_config_to_widget(widget, widget_id, configs)
    
    # Add this to the closeEvent method to ensure clean shutdown:
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop logging if active
        if self.data_logger.is_logging:
            self.data_logger.stop_logging()
        
        # Clean shutdown of data simulator
        self.data_simulator.shutdown()
        
        # Don't automatically save layout on close
        event.accept()

# Update the main block to add command line arguments:
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='EV Charging Station Monitor')
    parser.add_argument('--real-data', action='store_true', help='Use real data from UDP')
    parser.add_argument('--udp-ip', type=str, default='0.0.0.0', help='UDP IP address')
    parser.add_argument('--udp-port', type=int, default=5000, help='UDP port')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = EVChargingMonitor(use_real_data=args.real_data, 
                              udp_ip=args.udp_ip, 
                              udp_port=args.udp_port)
    window.show()
    sys.exit(app.exec_())