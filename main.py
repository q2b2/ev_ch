# main.py
# Main application for the EV Charging Station Monitor

import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                            QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QTextBrowser, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QSize
import argparse

# Import custom modules
from data_simulator import DataSimulator
from data_logger import DataLogger
from config_manager import ConfigManager
from ui_components import GraphWidget, GaugeWidget, TableWidget, ButtonWidget, EnergyHubWidget, GaugeGridWidget

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
        self.timer.start(300) # Update interval in milliseconds (100ms = 10Hz)
        
        # Apply saved configurations
        self.apply_saved_layouts()
        
        # Flag to track if layout has changed
        self.layout_changed = False
    
    def setupUI(self):
        """Set up the main UI components"""
        # Set window properties
        self.setWindowTitle("EV Charging Station Monitor")
        self.setGeometry(100, 100, 1280, 800)
        
        # Create tab widget as central widget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        # Main tab for monitoring
        self.monitoring_tab = QWidget()
        self.tab_widget.addTab(self.monitoring_tab, "Monitoring")
        
        # About tab
        self.about_tab = QWidget()
        self.tab_widget.addTab(self.about_tab, "About")
        
        # Set the monitoring tab as our central widget for existing code
        self.central_widget = self.monitoring_tab
        
        # Create all UI elements on the monitoring tab
        self.setup_graphs()
        self.setup_tables()
        self.setup_gauges()
        self.setup_control_buttons()
        
        # Add the QEERI logo to the monitoring tab
        self.logo_label = QLabel(self.central_widget)
        self.logo_label.setGeometry(1611, 20, 300, 100)  # Large logo size
        logo_pixmap = QPixmap("QEERI_logo.png")
        self.logo_label.setPixmap(logo_pixmap.scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.show()
        
        # Setup the About tab
        self.setup_about_tab()
        
        # setup the energy hub widget
        self.setup_energy_hub()
    
    def setup_about_tab(self):
        """Set up the About tab with project information"""
        layout = QVBoxLayout(self.about_tab)
        
        # Add logo at the top
        logo_label = QLabel()
        logo_pixmap = QPixmap("QEERI_logo.png")
        logo_label.setPixmap(logo_pixmap.scaled(350, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Add text content
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
        about_text.setHtml("""
        <div style="text-align: center;">
            <h2>EV Charging Station Monitoring System</h2>
            <p>Version 1.0</p>
            <p>&copy; 2025 QEERI</p>
            <br>
            <h3>Developed by:</h3>
            <p>Eng. Abdulaziz Alswiti</p>
            <p>a.alswiti@hotmail.com</p>
            <br>
            <h3>Under the supervision of:</h3>
            <p>Dr. Ali Sharida</p>
            <br>
            <h3>About This Project:</h3>
            <p>This system provides real-time monitoring of an EV charging station, displaying voltage, current, and power measurements. 
            It can receive data from hardware via UDP communication and visualize the parameters through dynamic graphs and gauges.</p>
            <p>The system features:</p>
            <ul style="text-align: left; margin-left: 100px; margin-right: 100px;">
                <li>Three-phase voltage and current visualization</li>
                <li>Power flow monitoring between grid, PV, EV, and battery</li>
                <li>Real-time parameter display</li>
                <li>Data logging capabilities</li>
            </ul>
            <br>
            <p>Qatar Environment and Energy Research Institute (QEERI)</p>
            <p>Current Date: %s</p>
        </div>
        """ % (time.strftime("%Y-%m-%d")))  # Add current date
        
        # Set a nice font size
        about_text.setStyleSheet("font-size: 20px;")
        
        layout.addWidget(about_text)

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
        """
        Create and configure gauge widgets in a fixed grid layout.
        
        This method creates a single fixed widget that contains all gauges
        arranged in a 3x2 grid at position x=749, y=408 with size 581x290.
        """
        # Create the gauge grid container widget
        self.gauge_grid = GaugeGridWidget(self.central_widget, "gauge_grid")
        
        # Define gauge configurations - these determine the properties of each gauge
        gauge_configs = [
            {"title": "Frequency", "min": 45, "max": 55, "units": "Hz", "id": "frequency_gauge"},
            {"title": "Voltage RMS", "min": 0, "max": 250, "units": "V", "id": "voltage_gauge"},
            {"title": "THD", "min": 0, "max": 10, "units": "%", "id": "thd_gauge"},
            {"title": "Active Power", "min": -5000, "max": 3000, "units": "W", "id": "active_power_gauge"},
            {"title": "Reactive Power", "min": -2000, "max": 2000, "units": "VAr", "id": "reactive_power_gauge"},
            {"title": "Current RMS", "min": 0, "max": 20, "units": "A", "id": "current_gauge"}
        ]
        
        # Create gauges and add them to the grid
        # They will be automatically positioned in a 3x2 grid (top to bottom, left to right)
        self.gauges = []
        for config in gauge_configs:
            gauge = self.gauge_grid.add_gauge(
                config["title"], 
                config["min"], 
                config["max"],
                config["units"],
                config["id"]
            )
            self.gauges.append(gauge)  # Keep reference for updating values
        
        # Display the gauge grid
        self.gauge_grid.show()
        
        # Add to widgets dictionary - this enables saving/restoring layouts
        # Use a string ID for the entire grid rather than individual gauges
        self.widgets["gauge_grid"] = self.gauge_grid
    
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

    def setup_energy_hub(self):
        """Create and configure the Smart Energy Hub widget"""
        self.energy_hub = EnergyHubWidget(self.central_widget, "energy_hub")
        self.energy_hub.setGeometry(950, 310, 400, 300)  # Adjust position and size as needed
        self.energy_hub.show()
        self.widgets["energy_hub"] = self.energy_hub

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
        
        # Update Smart Energy Hub
        hub_data = self.data_simulator.get_hub_data()
        self.energy_hub.update_pv_status(hub_data["s1_status"])
        self.energy_hub.update_ev_status(hub_data["s2_status"])
        self.energy_hub.update_grid_status(hub_data["s3_status"])
        self.energy_hub.update_battery_status(hub_data["s4_status"])
        self.energy_hub.update_ev_soc(hub_data["ev_soc"])
        self.energy_hub.update_battery_soc(hub_data["battery_soc"])
        
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