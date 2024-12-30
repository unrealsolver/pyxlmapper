import pytest

from pyxlmapper.util import (
    class_name_from_str,
    camel_to_snake,
    normalize,
    dict_path_set,
)


@pytest.mark.parametrize(
    "value,expected",
    (
        ("Internal", "Internal"),
        ("Physical x1/x4", "PhysicalX1X4"),
        ("USB-C Total", "USBCTotal"),
        ("USB 2.0 header", "USB20Header"),
        ("VRM (VCore)", "VRMVCore"),
        ("4-pin  RGB 12V", "FourPinRGB12V"),
        ("23one", "Two3One"),
    ),
)
def test_class_name_from_str(value, expected):
    assert class_name_from_str(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    (
        ("Internal", "internal"),
        ("PhysicalX1X4", "physical_x1_x4"),
        ("USBCTotal", "usbc_total"),
        ("USB20Header", "usb20_header"),
    ),
)
def test_camel_to_snake(value, expected):
    assert camel_to_snake(value) == expected


def test_normalize():
    assert normalize(4) == 4
    assert normalize(" a b\nc ") == "a b c"


def test_dict_path_set_single():
    obj = {}
    dict_path_set(obj, ["a"], 1)
    assert obj == {"a": 1}


def test_dict_path_set_nested():
    obj = {}
    dict_path_set(obj, ["a", "b", "c"], 1)
    assert obj == {"a": {"b": {"c": 1}}}


def test_dict_path_set_merging():
    obj = {"a": {"b": {"d": 2}}}
    dict_path_set(obj, ["a", "b", "c"], 1)
    assert obj == {"a": {"b": {"c": 1, "d": 2}}}
