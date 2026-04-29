"""
Tests for the steps module - telemetry verification, bitmask operations, and file I/O.
"""

import json
import os
import sys
import tempfile
import pytest
from collections import OrderedDict
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ing_lib.steps import (
    apply_bit_mask, BitMaskError, InputError, ReturnOn,
    check_telemetry_query, confirm_numeric,
    evaluate_verify_condition,
    get_input_output_paths, read_input_file,
    write_output_file, write_series_file,
)


# ── apply_bit_mask ──────────────────────────────────────────────────

class TestApplyBitMask:
    """Nominal and off-nominal tests for apply_bit_mask."""

    def test_and_decimal(self):
        assert apply_bit_mask(0xFF, '0x0F', 'AND') == 0x0F

    def test_or_decimal(self):
        assert apply_bit_mask(0xF0, '0x0F', 'OR') == 0xFF

    def test_binary_mask(self):
        assert apply_bit_mask(0b1111, '0b1100', 'AND') == 0b1100

    def test_hex_mask(self):
        assert apply_bit_mask(255, '0xFF', 'AND') == 255

    def test_decimal_mask(self):
        assert apply_bit_mask(10, '3', 'AND') == (10 & 3)

    def test_non_integer_input_raises(self):
        with pytest.raises(BitMaskError):
            apply_bit_mask('abc', '0xFF', 'AND')

    def test_invalid_binary_mask_raises(self):
        with pytest.raises(BitMaskError):
            apply_bit_mask(10, '0bXXX', 'AND')

    def test_invalid_hex_mask_raises(self):
        with pytest.raises(BitMaskError):
            apply_bit_mask(10, '0xZZZ', 'AND')

    def test_invalid_decimal_mask_raises(self):
        with pytest.raises(BitMaskError):
            apply_bit_mask(10, 'not_a_number', 'AND')

    def test_unsupported_operation_raises(self):
        with pytest.raises(BitMaskError):
            apply_bit_mask(10, '5', 'XOR')

    def test_zero_values(self):
        assert apply_bit_mask(0, '0', 'AND') == 0
        assert apply_bit_mask(0, '0xFF', 'OR') == 0xFF


# ── confirm_numeric ─────────────────────────────────────────────────

class TestConfirmNumeric:
    def test_integer(self):
        assert confirm_numeric(42) is True

    def test_float(self):
        assert confirm_numeric(3.14) is True

    def test_numeric_string(self):
        assert confirm_numeric('123.45') is True

    def test_negative(self):
        assert confirm_numeric(-7) is True

    def test_non_numeric_string(self):
        assert confirm_numeric('hello') is False

    def test_none(self):
        assert confirm_numeric(None) is False

    def test_empty_string(self):
        assert confirm_numeric('') is False


# ── check_telemetry_query ───────────────────────────────────────────

class TestCheckTelemetryQuery:
    """Nominal and off-nominal tests for check_telemetry_query."""

    def _base_predict(self, **overrides):
        d = {
            'verify_wait': 'WAIT',
            'dn_eu': 'DN',
            'verification_condition': 'GREATER_THAN',
            'verification_values': ['12'],
        }
        d.update(overrides)
        return d

    def test_valid_greater_than(self):
        q = {'CH-1': self._base_predict()}
        check_telemetry_query(q)

    def test_valid_record(self):
        q = {'CH-1': self._base_predict(verification_condition='RECORD', verification_values=[])}
        check_telemetry_query(q)

    def test_valid_not_present(self):
        q = {'CH-1': self._base_predict(verification_condition='NOT_PRESENT', verification_values=[])}
        check_telemetry_query(q)

    def test_valid_inclusive_range(self):
        q = {'CH-1': self._base_predict(verification_condition='INCLUSIVE_RANGE', verification_values=['1', '10'])}
        check_telemetry_query(q)

    def test_valid_exclusive_range(self):
        q = {'CH-1': self._base_predict(verification_condition='EXCLUSIVE_RANGE', verification_values=['1', '10'])}
        check_telemetry_query(q)

    def test_record_with_values_raises(self):
        q = {'CH-1': self._base_predict(verification_condition='RECORD', verification_values=['x'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_greater_than_wrong_count_raises(self):
        q = {'CH-1': self._base_predict(verification_values=['1', '2'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_range_wrong_count_raises(self):
        q = {'CH-1': self._base_predict(verification_condition='INCLUSIVE_RANGE', verification_values=['1'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_unknown_condition_raises(self):
        q = {'CH-1': self._base_predict(verification_condition='MAGIC')}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_invalid_dn_eu_raises(self):
        q = {'CH-1': self._base_predict(dn_eu='RAW')}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_invalid_verify_wait_raises(self):
        q = {'CH-1': self._base_predict(verify_wait='POLL')}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_invalid_bit_op_raises(self):
        q = {'CH-1': self._base_predict(bit_op='XOR', bit_mask='0xFF', verification_values=['12'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_bit_op_without_mask_raises(self):
        q = {'CH-1': self._base_predict(bit_op='AND', bit_mask=None, verification_values=['12'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_bit_mask_without_op_raises(self):
        q = {'CH-1': self._base_predict(bit_mask='0xFF')}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_non_numeric_verification_with_bitmask_raises(self):
        q = {'CH-1': self._base_predict(bit_op='AND', bit_mask='0xFF', verification_values=['abc'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_non_numeric_prior_value_raises(self):
        q = {'CH-1': self._base_predict(prior_value='abc')}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_non_numeric_verification_with_prior_raises(self):
        q = {'CH-1': self._base_predict(prior_value=5, verification_values=['abc'])}
        with pytest.raises(InputError):
            check_telemetry_query(q)

    def test_valid_with_bitmask(self):
        q = {'CH-1': self._base_predict(bit_op='AND', bit_mask='0xFF', verification_values=['12'])}
        check_telemetry_query(q)

    def test_valid_with_prior_value(self):
        q = {'CH-1': self._base_predict(prior_value=5, verification_values=['12'])}
        check_telemetry_query(q)


# ── evaluate_verify_condition ───────────────────────────────────────

class TestEvaluateVerifyCondition:
    """Test telemetry value evaluation against predicts."""

    def _predicts(self, **overrides):
        d = {
            'verify_wait': 'WAIT',
            'dn_eu': 'DN',
            'verification_condition': 'GREATER_THAN',
            'verification_values': [10],
        }
        d.update(overrides)
        return d

    def _channel(self, dn=20, eu=20.0, **extra):
        c = {'dn': dn, 'eu': eu}
        c.update(extra)
        return c

    def test_no_channels_timeout_not_present_pass(self):
        r = evaluate_verify_condition(None, 'CH-1', self._predicts(verification_condition='NOT_PRESENT', verification_values=[]), True)
        assert r['verification_status'] == 'PASS'

    def test_no_channels_timeout_other_fail(self):
        r = evaluate_verify_condition(None, 'CH-1', self._predicts(), True)
        assert r['verification_status'] == 'FAIL'

    def test_no_channels_no_timeout_returns_none(self):
        r = evaluate_verify_condition(None, 'CH-1', self._predicts(), False)
        assert r['verification_status'] is None

    def test_greater_than_pass(self):
        r = evaluate_verify_condition([self._channel(dn=15)], 'CH-1', self._predicts(), False)
        assert r['verification_status'] == 'PASS'

    def test_greater_than_fail(self):
        r = evaluate_verify_condition([self._channel(dn=5)], 'CH-1', self._predicts(), False)
        assert r['verification_status'] == 'FAIL'

    def test_less_than_pass(self):
        r = evaluate_verify_condition([self._channel(dn=5)], 'CH-1', self._predicts(verification_condition='LESS_THAN'), False)
        assert r['verification_status'] == 'PASS'

    def test_equal_pass(self):
        r = evaluate_verify_condition([self._channel(dn=10)], 'CH-1', self._predicts(verification_condition='EQUAL', verification_values=[10]), False)
        assert r['verification_status'] == 'PASS'

    def test_not_equal_pass(self):
        r = evaluate_verify_condition([self._channel(dn=11)], 'CH-1', self._predicts(verification_condition='NOT_EQUAL', verification_values=[10]), False)
        assert r['verification_status'] == 'PASS'

    def test_gte_pass(self):
        r = evaluate_verify_condition([self._channel(dn=10)], 'CH-1', self._predicts(verification_condition='GREATER_THAN_OR_EQUAL', verification_values=[10]), False)
        assert r['verification_status'] == 'PASS'

    def test_lte_pass(self):
        r = evaluate_verify_condition([self._channel(dn=10)], 'CH-1', self._predicts(verification_condition='LESS_THAN_OR_EQUAL', verification_values=[10]), False)
        assert r['verification_status'] == 'PASS'

    def test_inclusive_range_pass(self):
        r = evaluate_verify_condition([self._channel(dn=5)], 'CH-1', self._predicts(verification_condition='INCLUSIVE_RANGE', verification_values=[1, 10]), False)
        assert r['verification_status'] == 'PASS'

    def test_inclusive_range_fail(self):
        r = evaluate_verify_condition([self._channel(dn=11)], 'CH-1', self._predicts(verification_condition='INCLUSIVE_RANGE', verification_values=[1, 10]), False)
        assert r['verification_status'] == 'FAIL'

    def test_exclusive_range_pass(self):
        r = evaluate_verify_condition([self._channel(dn=5)], 'CH-1', self._predicts(verification_condition='EXCLUSIVE_RANGE', verification_values=[1, 10]), False)
        assert r['verification_status'] == 'PASS'

    def test_exclusive_range_boundary_fail(self):
        r = evaluate_verify_condition([self._channel(dn=10)], 'CH-1', self._predicts(verification_condition='EXCLUSIVE_RANGE', verification_values=[1, 10]), False)
        assert r['verification_status'] == 'FAIL'

    def test_record_always_passes(self):
        r = evaluate_verify_condition([self._channel(dn=999)], 'CH-1', self._predicts(verification_condition='RECORD', verification_values=[]), False)
        assert r['verification_status'] == 'PASS'

    def test_not_present_with_data_fail(self):
        r = evaluate_verify_condition([self._channel()], 'CH-1', self._predicts(verification_condition='NOT_PRESENT', verification_values=[]), False)
        assert r['verification_status'] == 'FAIL'

    def test_eu_channel(self):
        r = evaluate_verify_condition([self._channel(eu=15.0)], 'CH-1', self._predicts(dn_eu='EU', verification_values=[10]), False)
        assert r['verification_status'] == 'PASS'
        assert r['actual_value'] == 15.0

    def test_eu_status_channel(self):
        ch = self._channel(dn=0, eu=0)
        ch['channelType'] = 'STATUS'
        ch['status'] = 'ON'
        r = evaluate_verify_condition([ch], 'CH-1', self._predicts(dn_eu='EU', verification_condition='EQUAL', verification_values=['ON']), False)
        assert r['actual_value'] == 'ON'
        assert r['verification_status'] == 'PASS'

    def test_bitmask_applied(self):
        r = evaluate_verify_condition(
            [self._channel(dn=0xFF)], 'CH-1',
            self._predicts(bit_mask='0x0F', bit_op='AND', verification_values=[0x0F]),
            False
        )
        assert r['actual_value'] == 0x0F

    def test_prior_value_subtracted(self):
        r = evaluate_verify_condition(
            [self._channel(dn=20)], 'CH-1',
            self._predicts(prior_value=5, verification_values=[10]),
            False
        )
        assert r['actual_value'] == 15
        assert r['verification_status'] == 'PASS'


# ── File I/O functions ──────────────────────────────────────────────

class TestFileIO:
    """Tests for read_input_file, write_output_file, write_series_file."""

    def test_read_input_file_success(self):
        data = {'key': 'value', 'num': 42}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = read_input_file(path)
            assert result['key'] == 'value'
            assert isinstance(result, OrderedDict)
        finally:
            os.unlink(path)

    def test_read_input_file_not_found(self):
        with pytest.raises(InputError):
            read_input_file('/nonexistent/path.json')

    def test_read_input_file_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json {{{')
            path = f.name
        try:
            with pytest.raises(InputError):
                read_input_file(path)
        finally:
            os.unlink(path)

    def test_write_output_file_success(self):
        data = {'result': 'PASS', 'value': 42}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            write_output_file(data, path)
            with open(path) as fh:
                written = json.load(fh)
            assert written == data
        finally:
            os.unlink(path)

    def test_write_output_file_bad_path(self):
        with pytest.raises(InputError):
            write_output_file({'a': 1}, '/nonexistent/dir/out.json')

    def test_write_output_file_non_serializable(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            with pytest.raises(InputError):
                write_output_file({'func': lambda x: x}, path)
        finally:
            os.unlink(path)

    def test_write_series_file_success(self):
        data = {'series': [1, 2, 3]}
        with tempfile.TemporaryDirectory() as d:
            write_series_file(data, d)
            with open(os.path.join(d, 'series.json')) as fh:
                assert json.load(fh) == data

    def test_write_series_file_bad_dir(self):
        with pytest.raises(InputError):
            write_series_file({'a': 1}, '/nonexistent/dir')

    def test_write_series_file_non_serializable(self):
        with tempfile.TemporaryDirectory() as d:
            with pytest.raises(InputError):
                write_series_file({'func': set()}, d)


class TestGetInputOutputPaths:
    """Tests for get_input_output_paths."""

    def test_success(self):
        with patch.object(sys, 'argv', ['script', 'input.json', 'output.json']):
            inp, out = get_input_output_paths('err')
            assert inp.endswith('input.json')
            assert out.endswith('output.json')

    def test_insufficient_args_raises(self):
        with patch.object(sys, 'argv', ['script']):
            with pytest.raises(InputError):
                get_input_output_paths('Need two args')
