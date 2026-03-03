"""Tests for the automatic reconnection to devices.

.. moduleauthor:: Harvey Lelliott (flip-dots) <harveylelliott@duck.com>

"""

import asyncio
from typing import Union

import pytest
from bleak import BLEDevice
from helpers import NEGOTIATION_RESPONSES, MockDevice

from SolixBLE import SolixBLEDevice, const

MOCK_DEVICE_NAME = "Mock Device"
MOCK_DEVICE_ADDRESS = "AA:BB:CC:DD:EE:FF"
MOCK_BLE_DEVICE = BLEDevice(MOCK_DEVICE_ADDRESS, MOCK_DEVICE_NAME, {})


@pytest.mark.asyncio
async def test_automatic_retry():
    """
    Test the automatic retrying of a lost connection.

    This test expects the module to connect the the mock device
    and then the mock device drops the connection and we expect
    the module to automatically reconnect and not run any callbacks.
    """

    async with MockDevice() as mock_bluetooth:

        device = SolixBLEDevice(MOCK_BLE_DEVICE)

        def my_callback(*args, **kwargs):
            """We do not expect this callback to be triggered."""
            assert False

        # We first expect a negotiation
        for expected, response in NEGOTIATION_RESPONSES.items():
            mock_bluetooth.expect_ordered(
                bytes.fromhex(expected),
                bytes.fromhex(response) if response is not None else None,
            )

        # We expect the negotiations to succeed
        assert await device.connect(), "Expected connect to return True"
        await asyncio.sleep(0.5)
        assert device.connected, "Expected connected to be True"
        assert device.negotiated, "Expected connected to be True"
        mock_bluetooth.check_assertions()

        # We then add our callback that should not be run as we should
        # silently reconnect
        device.add_callback(my_callback)

        for expected, response in NEGOTIATION_RESPONSES.items():
            mock_bluetooth.expect_ordered(
                bytes.fromhex(expected),
                bytes.fromhex(response) if response is not None else None,
            )

        # We then trigger a disconnect from the device
        mock_bluetooth.disconnect()
        await asyncio.sleep(0.5)
        assert not device.connected, "Expected connected to be False"
        assert not device.negotiated, "Expected connected to be False"

        # Set .is_connected to True
        mock_bluetooth.allow_connect()

        # We expect to have been automatically reconnected
        await asyncio.sleep(10)
        assert device.connected, "Expected connected to be True"
        assert device.negotiated, "Expected connected to be True"
        mock_bluetooth.check_assertions()
        mock_bluetooth.check_assertions()
        mock_bluetooth.check_assertions()
