"""
Parameter form manager for PyQt6 GUI.

REUSES the Textual TUI parameter form generation logic for consistent UX.
This is a PyQt6 adapter that uses the actual working Textual TUI services.
"""

import dataclasses
import logging
from typing import Any, Dict, get_origin, get_args, Union, Optional
from pathlib import Path
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QFrame
)
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtCore import Qt, pyqtSignal

from openhcs.pyqt_gui.shared.color_scheme import PyQt6ColorScheme

# No-scroll widget classes to prevent accidental value changes
class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

# REUSE the actual working Textual TUI services
from openhcs.textual_tui.widgets.shared.signature_analyzer import SignatureAnalyzer
from openhcs.textual_tui.widgets.shared.parameter_form_manager import ParameterFormManager as TextualParameterFormManager
from openhcs.textual_tui.widgets.shared.typed_widget_factory import TypedWidgetFactory

# Import PyQt6 help components (using same pattern as Textual TUI)
from openhcs.pyqt_gui.widgets.shared.clickable_help_components import LabelWithHelp, GroupBoxWithHelp

logger = logging.getLogger(__name__)


class ParameterFormManager(QWidget):
    """
    PyQt6 adapter for Textual TUI ParameterFormManager.

    REUSES the actual working Textual TUI parameter form logic by creating
    a PyQt6 UI that mirrors the Textual TUI behavior exactly.
    """

    parameter_changed = pyqtSignal(str, object)  # param_name, value

    def __init__(self, parameters: Dict[str, Any], parameter_types: Dict[str, type],
                 field_id: str, parameter_info: Dict = None, parent=None, use_scroll_area: bool = True,
                 function_target=None, color_scheme: Optional[PyQt6ColorScheme] = None):
        super().__init__(parent)

        # Initialize color scheme
        self.color_scheme = color_scheme or PyQt6ColorScheme()

        # Store function target for docstring fallback
        self._function_target = function_target

        # Create the actual Textual TUI form manager (reuse the working logic)
        self.textual_form_manager = TextualParameterFormManager(
            parameters, parameter_types, field_id, parameter_info
        )

        # Store field_id for PyQt6 widget creation
        self.field_id = field_id

        # Control whether to use scroll area (disable for nested dataclasses)
        self.use_scroll_area = use_scroll_area

        # Track PyQt6 widgets for value updates
        self.widgets = {}
        self.nested_managers = {}

        self.setup_ui()
    
    def setup_ui(self):
        """Setup the parameter form UI using Textual TUI logic."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Build form fields using Textual TUI parameter types and logic
        for param_name, param_type in self.textual_form_manager.parameter_types.items():
            current_value = self.textual_form_manager.parameters[param_name]

            # Handle nested dataclasses (reuse Textual TUI logic)
            if dataclasses.is_dataclass(param_type):
                field_widget = self._create_nested_dataclass_field(param_name, param_type, current_value)
            else:
                field_widget = self._create_regular_parameter_field(param_name, param_type, current_value)

            if field_widget:
                content_layout.addWidget(field_widget)

        # Only use scroll area if requested (not for nested dataclasses)
        if self.use_scroll_area:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setWidget(content_widget)
            layout.addWidget(scroll_area)
        else:
            # Add content widget directly without scroll area
            layout.addWidget(content_widget)
    
    def _create_nested_dataclass_field(self, param_name: str, param_type: type, current_value: Any) -> QWidget:
        """Create a collapsible group for nested dataclass with help functionality."""
        # Use GroupBoxWithHelp to show dataclass documentation
        group_box = GroupBoxWithHelp(
            title=f"{param_name.replace('_', ' ').title()}",
            help_target=param_type,  # Show help for the dataclass type
            color_scheme=self.color_scheme
        )

        # Use the content layout from GroupBoxWithHelp
        layout = group_box.content_layout
        
        # Analyze nested dataclass
        nested_param_info = SignatureAnalyzer.analyze(param_type)
        
        # Get current values from nested dataclass instance
        nested_parameters = {}
        nested_parameter_types = {}
        
        for nested_name, nested_info in nested_param_info.items():
            nested_current_value = getattr(current_value, nested_name, nested_info.default_value) if current_value else nested_info.default_value
            nested_parameters[nested_name] = nested_current_value
            nested_parameter_types[nested_name] = nested_info.param_type
        
        # Create nested form manager without scroll area (dataclasses should show in full)
        nested_manager = ParameterFormManager(
            nested_parameters,
            nested_parameter_types,
            f"{self.field_id}_{param_name}",
            nested_param_info,
            use_scroll_area=False  # Disable scroll area for nested dataclasses
        )
        
        # Connect nested parameter changes
        nested_manager.parameter_changed.connect(
            lambda name, value, parent_name=param_name: self._handle_nested_parameter_change(parent_name, name, value)
        )
        
        self.nested_managers[param_name] = nested_manager
        layout.addWidget(nested_manager)
        
        return group_box
    
    def _create_regular_parameter_field(self, param_name: str, param_type: type, current_value: Any) -> QWidget:
        """Create a field for regular (non-dataclass) parameter."""
        container = QFrame()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Parameter label with help (reuses Textual TUI parameter info)
        param_info = self.textual_form_manager.parameter_info.get(param_name) if hasattr(self.textual_form_manager, 'parameter_info') else None
        param_description = param_info.description if param_info else f"Parameter: {param_name}"

        label_with_help = LabelWithHelp(
            text=f"{param_name.replace('_', ' ').title()}:",
            param_name=param_name,
            param_description=param_description,
            param_type=param_type,
            color_scheme=self.color_scheme
        )
        label_with_help.setMinimumWidth(150)
        layout.addWidget(label_with_help)

        # Create appropriate widget based on type
        widget = self._create_typed_widget(param_name, param_type, current_value)
        if widget:
            self.widgets[param_name] = widget
            layout.addWidget(widget)

            # Add reset button
            reset_btn = QPushButton("Reset")
            reset_btn.setMaximumWidth(60)
            reset_btn.clicked.connect(lambda: self._reset_parameter(param_name))
            layout.addWidget(reset_btn)
        
        return container
    
    def _create_typed_widget(self, param_name: str, param_type: type, current_value: Any) -> QWidget:
        """Create appropriate widget based on parameter type."""
        # Handle Optional types
        origin = get_origin(param_type)
        if origin is Union:
            args = get_args(param_type)
            if len(args) == 2 and type(None) in args:
                # This is Optional[T]
                param_type = args[0] if args[1] is type(None) else args[1]
        
        # Handle different types
        if param_type == bool:
            widget = QCheckBox()
            widget.setChecked(bool(current_value) if current_value is not None else False)
            widget.stateChanged.connect(lambda state: self._emit_parameter_change(param_name, widget.isChecked()))
            return widget
            
        elif param_type == int:
            widget = NoScrollSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(current_value) if current_value is not None else 0)
            widget.valueChanged.connect(lambda value: self._emit_parameter_change(param_name, value))
            return widget

        elif param_type == float:
            widget = NoScrollDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(6)
            widget.setValue(float(current_value) if current_value is not None else 0.0)
            widget.valueChanged.connect(lambda value: self._emit_parameter_change(param_name, value))
            return widget
            
        elif param_type == str or param_type == Path:
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda text: self._emit_parameter_change(param_name, text))
            return widget
            
        elif hasattr(param_type, '__bases__') and Enum in param_type.__bases__:
            # Enum type (use exact same logic as Textual TUI)
            widget = NoScrollComboBox()
            for enum_value in param_type:
                # Use enum.value for display and enum object for data (like Textual TUI)
                widget.addItem(enum_value.value.upper(), enum_value)

            # Set current value
            if current_value is not None:
                index = widget.findData(current_value)
                if index >= 0:
                    widget.setCurrentIndex(index)

            widget.currentIndexChanged.connect(
                lambda index: self._emit_parameter_change(param_name, widget.itemData(index))
            )
            return widget

        elif TypedWidgetFactory._is_list_of_enums(param_type):
            # Handle List[Enum] types (like List[VariableComponents]) - mirrors Textual TUI
            enum_type = TypedWidgetFactory._get_enum_from_list(param_type)
            widget = QComboBox()
            for enum_value in enum_type:
                widget.addItem(enum_value.value.upper(), enum_value)

            # For list of enums, current_value might be a list, so get first item or None
            display_value = None
            if current_value and isinstance(current_value, list) and len(current_value) > 0:
                display_value = current_value[0]

            if display_value is not None:
                index = widget.findData(display_value)
                if index >= 0:
                    widget.setCurrentIndex(index)

            widget.currentIndexChanged.connect(
                lambda index: self._emit_parameter_change(param_name, [widget.itemData(index)])
            )
            return widget
        
        else:
            # Fallback to string input
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda text: self._emit_parameter_change(param_name, text))
            return widget
    
    def _emit_parameter_change(self, param_name: str, value: Any):
        """Emit parameter change signal."""
        # Update the Textual TUI form manager (which holds the actual parameters)
        self.textual_form_manager.update_parameter(param_name, value)
        self.parameter_changed.emit(param_name, value)
    
    def _handle_nested_parameter_change(self, parent_name: str, nested_name: str, value: Any):
        """Handle parameter change in nested dataclass."""
        if parent_name in self.nested_managers:
            # Update nested manager's parameters
            nested_manager = self.nested_managers[parent_name]
            nested_manager.textual_form_manager.update_parameter(nested_name, value)

            # Rebuild nested dataclass instance
            nested_type = self.textual_form_manager.parameter_types[parent_name]
            nested_values = nested_manager.get_current_values()
            new_instance = nested_type(**nested_values)

            # Update parent parameter in textual form manager
            self.textual_form_manager.update_parameter(parent_name, new_instance)

            # Emit change for parent parameter
            self.parameter_changed.emit(parent_name, new_instance)
    
    def _reset_parameter(self, param_name: str):
        """Reset parameter to default value."""
        # Use textual form manager's parameter info and reset functionality
        if hasattr(self.textual_form_manager, 'parameter_info') and param_name in self.textual_form_manager.parameter_info:
            default_value = self.textual_form_manager.parameter_info[param_name].default_value

            # Update textual form manager
            self.textual_form_manager.update_parameter(param_name, default_value)

            # Update widget
            if param_name in self.widgets:
                widget = self.widgets[param_name]
                self._update_widget_value(widget, default_value)

            self.parameter_changed.emit(param_name, default_value)
    
    def _update_widget_value(self, widget: QWidget, value: Any):
        """Update widget value without triggering signals."""
        if isinstance(widget, QCheckBox):
            widget.blockSignals(True)
            widget.setChecked(bool(value) if value is not None else False)
            widget.blockSignals(False)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.blockSignals(True)
            widget.setValue(value if value is not None else 0)
            widget.blockSignals(False)
        elif isinstance(widget, QLineEdit):
            widget.blockSignals(True)
            widget.setText(str(value) if value is not None else "")
            widget.blockSignals(False)
        elif isinstance(widget, QComboBox):
            widget.blockSignals(True)
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            widget.blockSignals(False)
    
    def get_current_values(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return self.parameters.copy()
    
    def update_parameter(self, param_name: str, value: Any):
        """Update parameter value programmatically."""
        self.textual_form_manager.update_parameter(param_name, value)
        if param_name in self.widgets:
            self._update_widget_value(self.widgets[param_name], value)

    def get_current_values(self) -> Dict[str, Any]:
        """Get current parameter values (mirrors Textual TUI)."""
        return self.textual_form_manager.parameters.copy()
