# ui_components.py
# This file contains custom UI components for the EV Charging Station monitor

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QLineEdit, QRadioButton, QButtonGroup, QFrame,
                            QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg
import numpy as np
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont

class DraggableWidget(QFrame):
    """Base class for all draggable and resizable widgets"""
    
    def __init__(self, parent=None, widget_id=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.drag_position = None
        self.setMouseTracking(True)
        
        # Set frame and background
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        # QSizePolicy to make widget resizable
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)
        
        # Resize parameters
        self.resize_border_width = 10     # Border width for resizing detection
        self.resizing = False             # Flag for resizing mode
        self.resize_edge = None           # Which edge is being resized
        self.start_geometry = None        # Starting geometry for resize operations
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if we're on an edge for resizing
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.start_geometry = self.geometry()
                self.setCursor(self._get_cursor_for_edge(edge))
            else:
                # Regular drag operation
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if not self.resizing:
            # Check if mouse is near border and set appropriate cursor
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.setCursor(self._get_cursor_for_edge(edge))
            else:
                self.setCursor(Qt.ArrowCursor)
            
            # Handle dragging
            if event.buttons() == Qt.LeftButton and self.drag_position:
                self.move(event.globalPos() - self.drag_position)
                # Notify parent of movement
                if hasattr(self.parent(), "widget_moved"):
                    self.parent().widget_moved()
                event.accept()
        else:
            # Handle resizing
            self._handle_resize(event.globalPos())
            # Notify parent of resize
            if hasattr(self.parent(), "widget_moved"):
                self.parent().widget_moved()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.resizing = False
        self.resize_edge = None
        self.start_geometry = None
        # Reset cursor
        self.setCursor(Qt.ArrowCursor)
    
    def _get_resize_edge(self, pos):
        """Determine if the position is on an edge for resizing"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        border = self.resize_border_width
        
        # Check corners first (they take priority)
        if x < border and y < border:
            return "top-left"
        elif x > w - border and y < border:
            return "top-right"
        elif x < border and y > h - border:
            return "bottom-left"
        elif x > w - border and y > h - border:
            return "bottom-right"
        
        # Then check edges
        elif x < border:
            return "left"
        elif x > w - border:
            return "right"
        elif y < border:
            return "top"
        elif y > h - border:
            return "bottom"
        
        return None
    
    def _get_cursor_for_edge(self, edge):
        """Return the appropriate cursor for the given edge"""
        if edge in ["top-left", "bottom-right"]:
            return Qt.SizeFDiagCursor
        elif edge in ["top-right", "bottom-left"]:
            return Qt.SizeBDiagCursor
        elif edge in ["left", "right"]:
            return Qt.SizeHorCursor
        elif edge in ["top", "bottom"]:
            return Qt.SizeVerCursor
        return Qt.ArrowCursor
    
    def _handle_resize(self, global_pos):
        """Handle resize operation based on the active edge"""
        if not self.resize_edge or not self.start_geometry:
            return
        
        # Convert global position to parent coordinates
        parent_pos = self.parent().mapFromGlobal(global_pos)
        
        # Get original geometry
        orig = self.start_geometry
        new_geom = orig  # Start with original
        min_width = self.minimumWidth()
        min_height = self.minimumHeight()
        
        # Calculate new geometry based on edge being dragged
        if "left" in self.resize_edge:
            # Left edge moving - adjust x position and width
            dx = parent_pos.x() - orig.x()
            new_width = max(min_width, orig.width() - dx)
            if new_width == min_width:
                dx = orig.width() - min_width
            new_geom.setX(orig.x() + dx)
            new_geom.setWidth(orig.width() - dx)
        
        if "right" in self.resize_edge:
            # Right edge moving - adjust width
            new_width = max(min_width, parent_pos.x() - orig.x())
            new_geom.setWidth(new_width)
        
        if "top" in self.resize_edge:
            # Top edge moving - adjust y position and height
            dy = parent_pos.y() - orig.y()
            new_height = max(min_height, orig.height() - dy)
            if new_height == min_height:
                dy = orig.height() - min_height
            new_geom.setY(orig.y() + dy)
            new_geom.setHeight(orig.height() - dy)
        
        if "bottom" in self.resize_edge:
            # Bottom edge moving - adjust height
            new_height = max(min_height, parent_pos.y() - orig.y())
            new_geom.setHeight(new_height)
        
        # Apply new geometry
        self.setGeometry(new_geom)
        
        # Force update of the widget contents
        self.update()


class GraphWidget(DraggableWidget):
    """Widget for displaying real-time graphs"""
    
    def __init__(self, parent=None, title="Graph", widget_id=None):
        super().__init__(parent, widget_id)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Create PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')  # White background
        self.plot_widget.showGrid(x=True, y=True)
        layout.addWidget(self.plot_widget)
        
        self.setLayout(layout)
        
        # Plot lines and legend setup - will be configured differently for each graph type
        self.lines = []
        self.colors = [(255, 0, 0), (0, 0, 255), (0, 200, 0), (150, 150, 0)]
        
    def setup_voltage_graph(self):
        """Configure widget for voltage graph"""
        self.title_label.setText("Grid Voltage")
        self.plot_widget.setTitle("3-Phase Voltage")
        self.plot_widget.setLabel('left', "Voltage", units='V')
        self.plot_widget.setLabel('bottom', "Time", units='s')
        self.plot_widget.setYRange(-250, 250)
        
        # Add plot lines for each phase
        for i, phase_name in enumerate(['Vg,a', 'Vg,b', 'Vg,c']):
            pen = pg.mkPen(color=self.colors[i], width=2)
            line = self.plot_widget.plot([], [], pen=pen, name=phase_name)
            self.lines.append(line)
        
        # Add legend with better visibility
        legend = self.plot_widget.addLegend(offset=(10, 10))  # Position in top-right
        legend.setBrush(pg.mkBrush(255, 255, 255, 220))  # Semi-transparent white background
        legend.setPen(pg.mkPen(0, 0, 0))  # Black border
    
    def setup_current_graph(self):
        """Configure widget for current graph"""
        self.title_label.setText("Grid Current")
        self.plot_widget.setTitle("3-Phase Current")
        self.plot_widget.setLabel('left', "Current", units='A')
        self.plot_widget.setLabel('bottom', "Time", units='s')
        self.plot_widget.setYRange(-10, 10)
        
        # Add plot lines for each phase
        for i, phase_name in enumerate(['Ig,a', 'Ig,b', 'Ig,c']):
            pen = pg.mkPen(color=self.colors[i], width=2)
            line = self.plot_widget.plot([], [], pen=pen, name=phase_name)
            self.lines.append(line)
        
        # Add legend with better visibility
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 220))
        legend.setPen(pg.mkPen(0, 0, 0))
    
    def setup_power_graph(self):
        """Configure widget for power graph"""
        self.title_label.setText("Power Distribution")
        self.plot_widget.setTitle("System Power")
        self.plot_widget.setLabel('left', "Power", units='W')
        self.plot_widget.setLabel('bottom', "Time", units='s')
        self.plot_widget.setYRange(-5000, 3000)
        
        # Add plot lines for each power source
        for i, power_name in enumerate(['P_grid', 'P_pv', 'P_ev', 'P_battery']):
            pen = pg.mkPen(color=self.colors[i], width=2)
            line = self.plot_widget.plot([], [], pen=pen, name=power_name)
            self.lines.append(line)
        
        # Add legend with better visibility
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 220))
        legend.setPen(pg.mkPen(0, 0, 0))
    
    def update_voltage_data(self, time_data, va_data, vb_data, vc_data):
        """Update the voltage graph with new data"""
        self.lines[0].setData(time_data, va_data)
        self.lines[1].setData(time_data, vb_data)
        self.lines[2].setData(time_data, vc_data)
    
    def update_current_data(self, time_data, ia_data, ib_data, ic_data):
        """Update the current graph with new data"""
        self.lines[0].setData(time_data, ia_data)
        self.lines[1].setData(time_data, ib_data)
        self.lines[2].setData(time_data, ic_data)
    
    def update_power_data(self, time_data, p_grid, p_pv, p_ev, p_battery):
        """Update the power graph with new data"""
        self.lines[0].setData(time_data, p_grid)
        self.lines[1].setData(time_data, p_pv)
        self.lines[2].setData(time_data, p_ev)
        self.lines[3].setData(time_data, p_battery)
        

class GaugeWidget(DraggableWidget):
    """Widget for displaying gauge measurements"""
    
    def __init__(self, parent=None, title="Gauge", min_value=0, max_value=100, 
                 units="", widget_id=None):
        super().__init__(parent, widget_id)
        
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.value = min_value
        self.units = units
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Value label will be updated with the current value
        self.value_label = QLabel(f"{self.value:.2f} {self.units}")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 16px; color: blue;")
        layout.addWidget(self.value_label)
        
        # The gauge will be drawn on the paintEvent
        self.gauge_area = QWidget()
        self.gauge_area.setMinimumSize(150, 150)
        layout.addWidget(self.gauge_area)
        
        # Colors for gauge
        self.background_color = QColor(240, 240, 240)
        self.arc_color = QColor(200, 200, 200)
        self.pointer_color = QColor(255, 0, 0)
        self.text_color = QColor(0, 0, 0)
    
    def set_value(self, value):
        """Set the gauge value and update display"""
        # Ensure value is within range
        self.value = max(self.min_value, min(value, self.max_value))
        self.value_label.setText(f"{self.value:.2f} {self.units}")
        self.gauge_area.update()  # Force repaint
    
    def paintEvent(self, event):
        """Draw the gauge"""
        super().paintEvent(event)
        
        # Get dimensions to draw in the gauge area
        gauge_rect = self.gauge_area.geometry()
        
        # Set up painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(gauge_rect, self.background_color)
        
        # Calculate center and radius
        center_x = gauge_rect.x() + gauge_rect.width() / 2
        center_y = gauge_rect.y() + gauge_rect.height() - 20
        radius = min(gauge_rect.width(), gauge_rect.height() * 2) / 2 - 10
        
        # Draw arc (270 degrees, from -225 to 45 degrees)
        start_angle = -225 * 16  # QPainter uses 1/16 degrees
        span_angle = 270 * 16
        
        # Draw background arc
        pen = QPen(self.arc_color, 10)
        painter.setPen(pen)
        painter.drawArc(int(center_x - radius), int(center_y - radius), 
                        int(radius * 2), int(radius * 2), start_angle, span_angle)
        
        # Calculate pointer angle
        angle_range = 270  # 270 degrees
        value_range = self.max_value - self.min_value
        angle = -225 + (self.value - self.min_value) / value_range * angle_range
        
        # Convert angle to radians
        radians = np.radians(angle)
        
        # Calculate pointer end point
        pointer_length = radius * 0.8
        end_x = center_x + pointer_length * np.cos(radians)
        end_y = center_y + pointer_length * np.sin(radians)
        
        # Draw pointer
        pen = QPen(self.pointer_color, 3)
        painter.setPen(pen)
        painter.drawLine(int(center_x), int(center_y), int(end_x), int(end_y))
        
        # Draw center circle
        painter.setBrush(QBrush(self.pointer_color))
        painter.drawEllipse(int(center_x - 5), int(center_y - 5), 10, 10)
        
        # Draw min and max labels
        painter.setPen(self.text_color)
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Min value text
        min_x = center_x + radius * 0.9 * np.cos(np.radians(-225))
        min_y = center_y + radius * 0.9 * np.sin(np.radians(-225))
        painter.drawText(int(min_x - 20), int(min_y + 10), 
                         f"{self.min_value}")
        
        # Max value text
        max_x = center_x + radius * 0.9 * np.cos(np.radians(45))
        max_y = center_y + radius * 0.9 * np.sin(np.radians(45))
        painter.drawText(int(max_x), int(max_y), 
                         f"{self.max_value}")
        
        # Draw ticks
        pen = QPen(self.text_color, 2)
        painter.setPen(pen)
        
        # Draw major ticks and labels
        num_major_ticks = 5
        for i in range(num_major_ticks + 1):
            tick_angle = -225 + i * (270 / num_major_ticks)
            tick_radians = np.radians(tick_angle)
            
            # Draw longer tick
            inner_x = center_x + (radius - 10) * np.cos(tick_radians)
            inner_y = center_y + (radius - 10) * np.sin(tick_radians)
            outer_x = center_x + radius * np.cos(tick_radians)
            outer_y = center_y + radius * np.sin(tick_radians)
            
            painter.drawLine(int(inner_x), int(inner_y), int(outer_x), int(outer_y))
            
            # Draw tick label
            tick_value = self.min_value + i * (self.max_value - self.min_value) / num_major_ticks
            label_x = center_x + (radius - 25) * np.cos(tick_radians)
            label_y = center_y + (radius - 25) * np.sin(tick_radians)
            
            if i > 0 and i < num_major_ticks:  # Skip min and max as we already drew them
                painter.drawText(int(label_x - 10), int(label_y + 5), f"{tick_value:.1f}")


class TableWidget(DraggableWidget):
    """Widget for displaying editable parameter tables"""
    
    save_clicked = pyqtSignal(str, dict)  # Signal to emit when save button is clicked
    
    def __init__(self, parent=None, title="Parameters", widget_id=None):
        super().__init__(parent, widget_id)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Add title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value", "Input"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.on_save_clicked)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)
        self.table_type = None  # Will be set during setup
        self.radio_groups = {}  # For radio button groups
    
    def setup_charging_setting_table(self):
        """Configure table for Charging Setting"""
        self.title_label.setText("Charging Setting")
        self.table_type = "charging_setting"
        
        # Define parameters
        parameters = [
            {"name": "PV power", "type": "number", "default": 2000},
            {"name": "EV power", "type": "number", "default": -4000},
            {"name": "Battery power", "type": "number", "default": 0},
            {"name": "V_dc", "type": "readonly", "default": 80.19}
        ]
        
        self.table.setRowCount(len(parameters))
        
        # Populate table
        for i, param in enumerate(parameters):
            # Parameter name
            self.table.setItem(i, 0, QTableWidgetItem(param["name"]))
            
            # Current value
            value_item = QTableWidgetItem(str(param["default"]))
            self.table.setItem(i, 1, value_item)
            
            # Input field
            if param["type"] == "readonly":
                input_widget = QLabel("--")
                input_widget.setAlignment(Qt.AlignCenter)
            else:
                input_widget = QLineEdit("0")
            
            self.table.setCellWidget(i, 2, input_widget)
        
        self.table.resizeColumnsToContents()
    
    def setup_ev_charging_setting_table(self):
        """Configure table for EV Charging Setting"""
        self.title_label.setText("EV Charging Setting")
        self.table_type = "ev_charging_setting"
        
        # Define parameters
        parameters = [
            {"name": "EV voltage", "type": "number", "default": 58.66},
            {"name": "EV SoC", "type": "number", "default": 0},
            {"name": "Demand Response", "type": "radio", "default": True},
            {"name": "V2G", "type": "radio", "default": True}
        ]
        
        self.table.setRowCount(len(parameters))
        
        # Populate table
        for i, param in enumerate(parameters):
            # Parameter name
            self.table.setItem(i, 0, QTableWidgetItem(param["name"]))
            
            # Current value
            if param["type"] == "radio":
                value = "On" if param["default"] else "Off"
            else:
                value = str(param["default"])
            self.table.setItem(i, 1, QTableWidgetItem(value))
            
            # Input field
            if param["type"] == "number":
                input_widget = QLineEdit("0")
                self.table.setCellWidget(i, 2, input_widget)
            elif param["type"] == "radio":
                radio_widget = QWidget()
                radio_layout = QHBoxLayout(radio_widget)
                
                # Create radio button group
                radio_on = QRadioButton("On")
                radio_off = QRadioButton("Off")
                
                # Set default selection
                if param["default"]:
                    radio_on.setChecked(True)
                else:
                    radio_off.setChecked(True)
                
                # Add to group and layout
                button_group = QButtonGroup(radio_widget)
                button_group.addButton(radio_on)
                button_group.addButton(radio_off)
                
                radio_layout.addWidget(radio_on)
                radio_layout.addWidget(radio_off)
                
                # Store reference to button group
                self.radio_groups[param["name"]] = button_group
                
                self.table.setCellWidget(i, 2, radio_widget)
        
        self.table.resizeColumnsToContents()
    
    def setup_grid_settings_table(self):
        """Configure table for Grid Settings"""
        self.title_label.setText("Grid Settings")
        self.table_type = "grid_settings"
        
        # Define parameters
        parameters = [
            {"name": "Vg_rms", "type": "number", "default": 155},
            {"name": "Ig_rms", "type": "number", "default": 9},
            {"name": "Frequency", "type": "number", "default": 50},
            {"name": "THD", "type": "number", "default": 3},
            {"name": "Power factor", "type": "number", "default": 0.99}
        ]
        
        self.table.setRowCount(len(parameters))
        
        # Populate table
        for i, param in enumerate(parameters):
            # Parameter name
            self.table.setItem(i, 0, QTableWidgetItem(param["name"]))
            
            # Current value
            self.table.setItem(i, 1, QTableWidgetItem(str(param["default"])))
            
            # Input field
            input_widget = QLineEdit("0")
            self.table.setCellWidget(i, 2, input_widget)
        
        self.table.resizeColumnsToContents()
    
    def update_values(self, data_dict):
        """Update the values column in the table"""
        if self.table_type == "charging_setting":
            value_keys = ["PV power", "EV power", "Battery power", "V_dc"]
        elif self.table_type == "ev_charging_setting":
            value_keys = ["EV voltage", "EV SoC", "Demand Response", "V2G"]
        elif self.table_type == "grid_settings":
            value_keys = ["Vg_rms", "Ig_rms", "Frequency", "THD", "Power factor"]
        else:
            return
        
        for row in range(self.table.rowCount()):
            param_name = self.table.item(row, 0).text()
            if param_name in data_dict:
                value = data_dict[param_name]
                if isinstance(value, bool):
                    value = "On" if value else "Off"
                self.table.item(row, 1).setText(str(value))
    
    def on_save_clicked(self):
        """Handle save button click - collect input values and emit signal"""
        input_values = {}
        
        for row in range(self.table.rowCount()):
            param_name = self.table.item(row, 0).text()
            cell_widget = self.table.cellWidget(row, 2)
            
            if isinstance(cell_widget, QLineEdit):
                # Handle number input
                try:
                    value = float(cell_widget.text())
                    input_values[param_name] = value
                except ValueError:
                    # Invalid input, ignore
                    pass
            elif param_name in self.radio_groups:
                # Handle radio button
                button_group = self.radio_groups[param_name]
                if button_group.buttons()[0].isChecked():  # First button is "On"
                    input_values[param_name] = True
                else:
                    input_values[param_name] = False
        
        # Emit signal with table type and values
        self.save_clicked.emit(self.table_type, input_values)


class ButtonWidget(DraggableWidget):
    """Widget for displaying and managing control buttons"""
    
    def __init__(self, parent=None, title="Controls", widget_id=None):
        super().__init__(parent, widget_id)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Add title label
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Container for buttons
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        layout.addWidget(self.buttons_container)
        
        self.setLayout(layout)
        self.buttons = []
    
    def add_button(self, text, color="default", callback=None):
        """Add a button to the container"""
        button = QPushButton(text)
        button.setFont(QFont("Arial", 12))
        
        # Apply styling based on color
        if color == "green":
            button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        elif color == "red":
            button.setStyleSheet("background-color: #F44336; color: white; padding: 8px;")
        elif color == "blue":
            button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        else:
            button.setStyleSheet("padding: 8px;")
        
        # Connect callback if provided
        if callback:
            button.clicked.connect(callback)
        
        # Add to layout and store reference
        self.buttons_layout.addWidget(button)
        self.buttons.append(button)
        
        return button
    
    def get_button(self, index):
        """Get button by index"""
        if 0 <= index < len(self.buttons):
            return self.buttons[index]
        return None