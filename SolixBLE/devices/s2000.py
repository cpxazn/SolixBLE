"""S2000 / AS220 power station model.

.. moduleauthor:: Harvey Lelliott (flip-dots) <harveylelliott@duck.com>

"""

from ..device import SolixBLEDevice
from ..states import ChargingStatus, PortStatus

#: Command sent after connecting to start the telemetry stream. The S2000 uses
#: the newer Gen 2 telemetry flow and does not stream until subscribed.
CMD_SUBSCRIBE = "4100"
SUBSCRIBE_PAYLOAD = "a10121"

CMD_AC_OUTPUT = "4101"

PAYLOAD_ON = "a10121a2020101"
PAYLOAD_OFF = "a10121a2020100"


class S2000(SolixBLEDevice):
    """
    S2000 Power Station.

    Use this class to connect, monitor and control an S2000 power station. This
    model is also known as the AS220. It uses the newer Gen 2 encrypted,
    fragmented telemetry flow (``c421``/``c900``) and requires a subscribe
    command after connecting.
    """

    _EXPECTED_TELEMETRY_LENGTH: int = 253

    #: The S2000 pushes telemetry on the same command codes as Gen 2 models.
    _TELEMETRY_COMMANDS: tuple[str, ...] = ("c421", "c900")

    async def _post_connect(self) -> None:
        """Subscribe to telemetry once connected."""
        await self._send_command(
            cmd=bytes.fromhex(CMD_SUBSCRIBE),
            payload=bytes.fromhex(SUBSCRIBE_PAYLOAD),
        )

    async def turn_ac_on(self) -> None:
        """Turn the AC output on.

        :raises ConnectionError: If not connected to device.
        :raises BleakError: If command transmission fails.
        """
        await self._send_command(
            cmd=bytes.fromhex(CMD_AC_OUTPUT), payload=bytes.fromhex(PAYLOAD_ON)
        )

    async def turn_ac_off(self) -> None:
        """Turn the AC output off.

        :raises ConnectionError: If not connected to device.
        :raises BleakError: If command transmission fails.
        """
        await self._send_command(
            cmd=bytes.fromhex(CMD_AC_OUTPUT), payload=bytes.fromhex(PAYLOAD_OFF)
        )

    @property
    def serial_number(self) -> str:
        """Device serial number.

        :returns: Device serial number or default str value.
        """
        return self._parse_string("a2", begin=3, end=20)

    @property
    def part_number(self) -> str:
        """Device part number.

        :returns: Device part number or default str value.
        """
        return self._parse_string("a2", begin=22, end=27)

    @property
    def temperature(self) -> int:
        """Temperature of the unit (C).

        :returns: Temperature of the unit in degrees C.
        """
        return self._parse_int("a5", begin=1, end=2, signed=True)

    @property
    def charging_status(self) -> ChargingStatus:
        """Battery charging/discharging status.

        Observed values are ``0`` idle, ``1`` discharging, and ``2`` charging.

        :returns: Charging status.
        """
        return ChargingStatus(self._parse_int("a5", begin=2, end=3))

    @property
    def battery_percentage(self) -> int:
        """Battery Percentage.

        :returns: Percentage charge of battery or default int value.
        """
        return self._parse_int("a5", begin=3, end=4)

    @property
    def battery_health(self) -> int:
        """Battery health.

        :returns: Percentage battery health or default int value.
        """
        return self._parse_int("a5", begin=4, end=5)

    @property
    def power_in(self) -> int:
        """Total Power In (watts).

        :returns: Total power in or default int value.
        """
        return self.ac_power_in + self.solar_power_in

    @property
    def power_out(self) -> int:
        """Total Power Out (watts).

        :returns: Total power out or default int value.
        """
        return self._parse_int("a6", begin=1, end=3)

    @property
    def ac_power_in(self) -> int:
        """AC Power In (watts).

        :returns: Total AC power in or default int value.
        """
        return self._parse_int("a6", begin=3, end=5)

    @property
    def ac_output(self) -> PortStatus:
        """AC Port Status.

        PortStatus.NOT_CONNECTED signifies off. PortStatus.OUTPUT signifies on.

        :returns: Status of the AC port.
        """
        return PortStatus(self._parse_int("a7", begin=1, end=2))

    @property
    def ac_power_out(self) -> int:
        """AC Power Out (watts).

        :returns: Total AC power out or default int value.
        """
        return self._parse_int("a7", begin=2, end=4)

    @property
    def solar_port(self) -> PortStatus:
        """Solar Port Status.

        :returns: Status of the solar port.
        """
        return PortStatus.from_input_only(self._parse_int("a8", begin=1, end=2))

    @property
    def solar_power_in(self) -> int:
        """Solar/DC Power In (watts).

        .. note:: Offset inferred from the Gen 2 packet shape, not yet confirmed
           with a live solar input capture.

        :returns: Solar/DC power in or default int value.
        """
        return self._parse_int("a8", begin=2)

    @property
    def usb_output(self) -> PortStatus:
        """USB output status.

        The S2000 reports its USB ports as an aggregate output rather than as
        individual USB-C/USB-A telemetry values.

        :returns: Status of the aggregate USB output.
        """
        return PortStatus(self._parse_int("aa", begin=1, end=2))

    @property
    def usb_power(self) -> int:
        """Aggregate USB Power Out (watts).

        :returns: Aggregate USB power out or default int value.
        """
        return self._parse_int("aa", begin=2)

    @property
    def max_battery_percentage(self) -> int:
        """Maximum charge percentage.

        :returns: Battery charge percentage upper limit or default int value.
        """
        return self._parse_int("d9", begin=4, end=5)

    @property
    def min_battery_percentage(self) -> int:
        """Minimum discharge percentage.

        :returns: Battery discharge percentage lower limit or default int value.
        """
        return self._parse_int("d9", begin=5, end=6)
