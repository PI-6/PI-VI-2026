import pytest

from services import validators as v


@pytest.mark.parametrize("cpf", ["52998224725", "11144477735", "12345678909"])
def test_valid_cpf(cpf):
    assert v.is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", ["52998224724", "11111111111", "1234567890", ""])
def test_invalid_cpf(cpf):
    assert not v.is_valid_cpf(cpf)


def test_only_digits_removes_mask():
    assert v.only_digits("123.456.789-09") == "12345678909"
    assert v.only_digits("(19) 99999-0000") == "19999990000"
    assert v.only_digits(None) == ""


@pytest.mark.parametrize("email,expected", [
    ("ana@gmail.com", True),
    ("ana.souza@salaobelle.com.br", True),
    ("ana@", False),
    ("ana gmail.com", False),
    ("", False),
])
def test_email(email, expected):
    assert v.is_valid_email(email) is expected


def test_phone_accepts_landline_and_mobile():
    assert v.is_valid_phone("1932221111")
    assert v.is_valid_phone("19999990000")
    assert not v.is_valid_phone("999990000")


def test_parse_time():
    assert v.parse_time("09:30").hour == 9
    assert v.parse_time("25:00") is None
    assert v.parse_time(None) is None
