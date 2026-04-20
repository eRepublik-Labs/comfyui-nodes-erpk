# ABOUTME: Minimal test stub for comfy_api.latest, used when ComfyUI is not installed.
# ABOUTME: Provides IO types, Schema, ComfyNode, NodeOutput, and ComfyExtension for structural tests.

"""
Test stub for comfy_api.latest

Provides just enough of the V3 API surface for node structural tests
and execute-method validation. Does not replicate ComfyUI runtime behavior.

Usage in conftest.py:
    Installed as a fake 'comfy_api' package in sys.modules so that
    `from comfy_api.latest import IO, ComfyExtension` works in tests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# --- Base IO classes ---

class _IO_V3:
    """Base for all IO descriptors."""
    io_type = None  # Set by ComfyTypeIO subclasses


class Input(_IO_V3):
    def __init__(self, id: str, display_name=None, optional=False,
                 tooltip=None, lazy=None, extra_dict=None,
                 raw_link=None, advanced=None):
        self.id = id
        self.display_name = display_name
        self.optional = optional
        self.tooltip = tooltip
        self.lazy = lazy
        self.extra_dict = extra_dict if extra_dict is not None else {}
        self.rawLink = raw_link
        self.advanced = advanced

    @property
    def io_type(self):
        return self.Parent.io_type if hasattr(self, 'Parent') else None


class WidgetInput(Input):
    def __init__(self, id: str, display_name=None, optional=False,
                 tooltip=None, lazy=None, default=None,
                 socketless=None, widget_type=None, force_input=None,
                 extra_dict=None, raw_link=None, advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy,
                         extra_dict, raw_link, advanced)
        self.default = default
        self.socketless = socketless
        self.widget_type = widget_type
        self.force_input = force_input


class Output(_IO_V3):
    def __init__(self, id=None, display_name=None, tooltip=None,
                 is_output_list=False):
        self.id = id
        self.display_name = display_name if display_name else id
        self.tooltip = tooltip
        self.is_output_list = is_output_list

    @property
    def io_type(self):
        return self.Parent.io_type if hasattr(self, 'Parent') else None


# --- Number display enum ---

class NumberDisplay(str, Enum):
    number = "number"
    slider = "slider"


# --- ComfyTypeIO metaclass-like pattern ---

def _make_io_type(type_name, io_type_str, python_type, input_cls=None, output_cls=None):
    """Create a ComfyTypeIO-like class with nested Input/Output classes."""

    parent_class = type('_Parent', (), {'io_type': io_type_str})

    if input_cls is None:
        class DefaultInput(WidgetInput):
            Parent = parent_class
        input_cls = DefaultInput
    else:
        input_cls.Parent = parent_class

    if output_cls is None:
        class DefaultOutput(Output):
            Parent = parent_class
        output_cls = DefaultOutput
    else:
        output_cls.Parent = parent_class

    cls = type(type_name, (), {
        'Type': python_type,
        'io_type': io_type_str,
        'Input': input_cls,
        'Output': output_cls,
    })
    return cls


# --- Specific Input subclasses ---

class _StringInput(WidgetInput):
    def __init__(self, id, display_name=None, optional=False, tooltip=None,
                 lazy=None, multiline=False, placeholder=None, default=None,
                 dynamic_prompts=None, socketless=None, force_input=None,
                 extra_dict=None, raw_link=None, advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy, default,
                         socketless, None, force_input, extra_dict, raw_link, advanced)
        self.multiline = multiline
        self.placeholder = placeholder
        self.dynamic_prompts = dynamic_prompts


class _IntInput(WidgetInput):
    def __init__(self, id, display_name=None, optional=False, tooltip=None,
                 lazy=None, default=None, min=None, max=None, step=None,
                 control_after_generate=None, display_mode=None,
                 socketless=None, force_input=None, extra_dict=None,
                 raw_link=None, advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy, default,
                         socketless, None, force_input, extra_dict, raw_link, advanced)
        self.min = min
        self.max = max
        self.step = step
        self.control_after_generate = control_after_generate
        self.display_mode = display_mode


class _FloatInput(WidgetInput):
    def __init__(self, id, display_name=None, optional=False, tooltip=None,
                 lazy=None, default=None, min=None, max=None, step=None,
                 round=None, display_mode=None, socketless=None,
                 force_input=None, extra_dict=None, raw_link=None,
                 advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy, default,
                         socketless, None, force_input, extra_dict, raw_link, advanced)
        self.min = min
        self.max = max
        self.step = step
        self.round = round
        self.display_mode = display_mode


class _BooleanInput(WidgetInput):
    def __init__(self, id, display_name=None, optional=False, tooltip=None,
                 lazy=None, default=None, label_on=None, label_off=None,
                 socketless=None, force_input=None, extra_dict=None,
                 raw_link=None, advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy, default,
                         socketless, None, force_input, extra_dict, raw_link, advanced)
        self.label_on = label_on
        self.label_off = label_off


class _ComboInput(WidgetInput):
    def __init__(self, id, options=None, display_name=None, optional=False,
                 tooltip=None, lazy=None, default=None,
                 control_after_generate=None, socketless=None,
                 extra_dict=None, raw_link=None, advanced=None):
        super().__init__(id, display_name, optional, tooltip, lazy, default,
                         socketless, None, None, extra_dict, raw_link, advanced)
        self.options = options if options is not None else []
        self.multiselect = False
        self.control_after_generate = control_after_generate


class _ComboOutput(Output):
    def __init__(self, id=None, display_name=None, options=None,
                 tooltip=None, is_output_list=False):
        super().__init__(id, display_name, tooltip, is_output_list)
        self.options = options if options is not None else []


# --- Build the IO type classes ---

String = _make_io_type('String', 'STRING', str, _StringInput)
Int = _make_io_type('Int', 'INT', int, _IntInput)
Float = _make_io_type('Float', 'FLOAT', float, _FloatInput)
Boolean = _make_io_type('Boolean', 'BOOLEAN', bool, _BooleanInput)
Image = _make_io_type('Image', 'IMAGE', None)
Mask = _make_io_type('Mask', 'MASK', None)
Combo = _make_io_type('Combo', 'COMBO', str, _ComboInput, _ComboOutput)
AnyType = _make_io_type('AnyType', '*', object)


def Custom(io_type: str):
    """Create a ComfyTypeIO for a custom io_type string."""
    return _make_io_type(f'Custom_{io_type}', io_type, None)


# --- Schema ---

@dataclass
class Schema:
    node_id: str
    display_name: str = None
    category: str = "sd"
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    hidden: list = field(default_factory=list)
    description: str = ""
    search_aliases: list = field(default_factory=list)
    is_input_list: bool = False
    is_output_node: bool = False
    is_deprecated: bool = False
    is_experimental: bool = False
    not_idempotent: bool = False
    is_api_node: bool = False
    accept_all_inputs: bool = False


# --- NodeOutput ---

class NodeOutput:
    def __init__(self, *args: Any, ui=None, expand=None,
                 block_execution=None):
        self.args = args
        self.ui = ui
        self.expand = expand
        self.block_execution = block_execution

    @property
    def result(self):
        return self.args if len(self.args) > 0 else None

    def __getitem__(self, index):
        return self.args[index]

    def __len__(self):
        return len(self.args)


# --- ComfyNode ---

class ComfyNode(ABC):
    RELATIVE_PYTHON_MODULE = None
    SCHEMA = None

    @classmethod
    @abstractmethod
    def define_schema(cls) -> Schema:
        ...

    @classmethod
    @abstractmethod
    def execute(cls, **kwargs) -> NodeOutput:
        ...


# --- NodeReplace ---

class NodeReplace:
    """Defines a node replacement mapping from an old node ID to a new one."""
    def __init__(self,
        new_node_id: str,
        old_node_id: str,
        old_widget_ids: list = None,
        input_mapping: list = None,
        output_mapping: list = None,
    ):
        self.new_node_id = new_node_id
        self.old_node_id = old_node_id
        self.old_widget_ids = old_widget_ids
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping

    def as_dict(self):
        return {
            "new_node_id": self.new_node_id,
            "old_node_id": self.old_node_id,
            "old_widget_ids": self.old_widget_ids,
            "input_mapping": list(self.input_mapping) if self.input_mapping else None,
            "output_mapping": list(self.output_mapping) if self.output_mapping else None,
        }


# --- ComfyAPI ---

class _NodeReplacementAPI:
    """Test stub for ComfyAPI.node_replacement."""
    def __init__(self):
        self._registered: list[NodeReplace] = []

    async def register(self, node_replace: NodeReplace) -> None:
        self._registered.append(node_replace)

    def get_registered(self) -> list[NodeReplace]:
        return list(self._registered)

    def clear(self):
        self._registered.clear()


class ComfyAPI:
    """Test stub for comfy_api.latest.ComfyAPI."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.node_replacement = _NodeReplacementAPI()
        return cls._instance

    @classmethod
    def _reset(cls):
        """Reset singleton for test isolation."""
        if cls._instance is not None:
            cls._instance.node_replacement.clear()


# --- ComfyExtension ---

class ComfyExtension(ABC):
    async def on_load(self) -> None:
        pass

    @abstractmethod
    async def get_node_list(self) -> list:
        ...
