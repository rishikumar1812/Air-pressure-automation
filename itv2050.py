"""
itv2050.py

RS-232C driver for the SMC ITV2050-RC2L electro-pneumatic regulator.

Protocol summary (from the SMC ITV2050-RC2L RS-232C operation manual):

    Serial settings : 9600 baud, 8 data bits, 1 stop bit, no parity, no flow control
    Character code  : ASCII
    Frame format    : "<COMMAND> <value>\r\n"  (single space between command and value)
    End code        : CR LF

    Commands:
        SET nn   -> set output pressure. nn is an integer 0-1023.
                    Response: "nn"               (confirmed value, 0-1023)
                              "OUT OF RANGE"      if 1023 < nn <= 9999
                              "UNKNOWN COMMAND"   if nn outside 0-9999
        INC      -> add 2 to the current setting. Response: "mm" (new setting).
                    Clamped to 1023 if current >= 1021.
        DEC      -> subtract 2 from the current setting. Response: "mm" (new setting).
                    Clamped to 0 if current <= 2.
        REQ      -> request the current *setting* data. Response: "nn"
        MON      -> request the actual *measured output* pressure. Response: "nn"

    The 0-1023 setting value is linear against 0%-100% of the unit's full-scale (F.S.)
    pressure rating:
        nn = (desired_pressure / F.S.) * 1023

    IMPORTANT: F.S. depends on your exact ITV2050-RC2L configuration/nameplate.
    The standard ITV2050-RC2L pressure range is 0.9 MPa - confirm against your unit
    before relying on this in production. Override via the `full_scale_mpa` constructor
    argument if your unit differs.
"""

import time
import serial


class ITV2050Error(Exception):
    """Raised for communication errors or error responses from the regulator."""


class ITV2050Regulator:

    def __init__(self, port, baudrate=9600, timeout=1.0, full_scale_mpa=0.9):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.full_scale_mpa = full_scale_mpa
        self.ser = None

    # ---------------------------------------------------------------- #
    # connection management
    # ---------------------------------------------------------------- #

    def connect(self):
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        time.sleep(0.1)  # let the port settle after opening
        return self

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ---------------------------------------------------------------- #
    # low-level command/response
    # ---------------------------------------------------------------- #

    def _send(self, command):
        if self.ser is None or not self.ser.is_open:
            raise ITV2050Error("Serial port is not open. Call connect() first.")

        frame = (command + "\r\n").encode("ascii")

        self.ser.reset_input_buffer()
        self.ser.write(frame)

        raw = self.ser.readline()
        if not raw:
            raise ITV2050Error(
                f"No response from regulator on {self.port} for command {command!r} "
                f"(timeout={self.timeout}s). Check wiring/COM port/baud rate."
            )

        try:
            text = raw.decode("ascii").strip()
        except UnicodeDecodeError:
            raise ITV2050Error(
                f"Got non-ASCII bytes back for command {command!r}: {raw!r}. "
                f"This usually means a baud-rate mismatch or noisy wiring, not a "
                f"Python encoding bug — the regulator only ever speaks ASCII."
            )

        if text == "OUT OF RANGE":
            raise ITV2050Error(f"Setting data out of range for command {command!r}.")
        if text == "UNKNOWN COMMAND":
            raise ITV2050Error(f"Regulator rejected command {command!r} as unknown.")
        if text == "":
            raise ITV2050Error(
                f"Empty response for command {command!r}. Raw bytes were {raw!r}."
            )

        return text

    def _parse_int(self, text, command):
        """
        Convert a response string to int, with a clear error (not a raw
        ValueError/TypeError) if it's missing, None, or not actually numeric.
        """
        if text is None:
            raise ITV2050Error(f"Got no usable response (None) for command {command!r}.")
        try:
            return int(text)
        except (ValueError, TypeError):
            raise ITV2050Error(
                f"Response {text!r} for command {command!r} isn't a valid integer. "
                f"Likely a partial/garbled frame — check baud rate and CR/LF framing."
            )

    # ---------------------------------------------------------------- #
    # pressure <-> raw setting conversion
    # ---------------------------------------------------------------- #

    def pressure_to_raw(self, pressure_mpa):
        pressure_mpa = max(0.0, min(self.full_scale_mpa, pressure_mpa))
        raw = round((pressure_mpa / self.full_scale_mpa) * 1023)
        return max(0, min(1023, raw))

    def raw_to_pressure(self, raw):
        return (raw / 1023.0) * self.full_scale_mpa

    # ---------------------------------------------------------------- #
    # public commands
    # ---------------------------------------------------------------- #

    def set_pressure(self, pressure_mpa):
        """Set output pressure in MPa. Returns the regulator-confirmed value in MPa."""
        raw = self.pressure_to_raw(pressure_mpa)
        confirmed_raw = self._parse_int(self._send(f"SET {raw}"), f"SET {raw}")
        return self.raw_to_pressure(confirmed_raw)

    def set_raw(self, raw):
        """Set output pressure using the raw 0-1023 setting value directly."""
        raw = max(0, min(1023, int(raw)))
        return self._parse_int(self._send(f"SET {raw}"), f"SET {raw}")

    def increase(self):
        """Step the setting up by 2 (~0.2% F.S.). Returns new raw setting (0-1023)."""
        return self._parse_int(self._send("INC"), "INC")

    def decrease(self):
        """Step the setting down by 2. Returns new raw setting (0-1023)."""
        return self._parse_int(self._send("DEC"), "DEC")

    def read_setpoint_raw(self):
        """Read back the commanded setting data (0-1023)."""
        return self._parse_int(self._send("REQ"), "REQ")

    def read_setpoint_pressure(self):
        return self.raw_to_pressure(self.read_setpoint_raw())

    def read_output_raw(self):
        """Read the actual measured output pressure (0-1023)."""
        return self._parse_int(self._send("MON"), "MON")

    def read_output_pressure(self):
        return self.raw_to_pressure(self.read_output_raw())
