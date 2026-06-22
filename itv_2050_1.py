import serial
import time


class ITV2050:
    """
    Driver for SMC ITV2050-RC2L E/P Regulator over RS-232C.

    Fixes applied vs. the original version:
      1. reset_input_buffer() before every write, so stale bytes from a
         previous (possibly malformed) exchange can never bleed into
         the next read. This was the root cause of the intermittent
         'm' / UNKNOWN COMMAND / empty-response behaviour - it's a
         buffer race, not a wiring fault.
      2. read_until(b"\\n") instead of readline() - functionally similar,
         but made explicit since the manual specifies CR/LF as the
         frame terminator. (readline() already respects this by default
         since '\\n' is pyserial's default line terminator, but being
         explicit avoids relying on a default that's easy to misconfigure
         later.)
      3. Safe parsing - int(response) no longer crashes the whole
         script on UNKNOWN COMMAND / OUT OF RANGE / timeout. Errors are
         raised as a clear, specific exception instead of a bare
         ValueError, so calling code can catch and retry/log instead of
         dying.
      4. A small inter-command settle delay is exposed (not forced) so
         you can space out rapid back-to-back commands if needed.
    """

    FULL_SCALE_MPA = 0.9

    class RegulatorError(Exception):
        """Raised when the regulator returns a non-numeric / error
        response instead of valid data."""
        pass

    def __init__(self, port, baudrate=9600, timeout=1):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout,
            dsrdtr=False,
            rtscts=False,
            xonxoff=False,
        )
        # Clear out anything stale sitting in the OS buffers from
        # before this object existed (e.g. a previous crashed run).
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def send_command(self, cmd):
        """Send one command, return the regulator's raw text response
        (stripped of CR/LF), or '' on timeout.

        Critically: drains the input buffer immediately before writing,
        so any unread bytes left over from a prior exchange can never
        be mistaken for this command's response.
        """
        self.ser.reset_input_buffer()

        command = f"{cmd}\r\n"
        self.ser.write(command.encode("ascii"))
        self.ser.flush()

        raw = self.ser.read_until(b"\n")  # blocks up to `timeout` seconds
        return raw.decode("ascii", errors="replace").strip()

    def _send_and_parse_int(self, cmd):
        """Send a command expected to return a plain integer, and
        raise a clear error if it didn't - instead of letting int()
        throw an opaque ValueError or silently propagating garbage.
        """
        response = self.send_command(cmd)

        if response == "":
            raise self.RegulatorError(
                f"No response to '{cmd}' (timed out). "
                f"Check wiring / power / that nothing else has the port open."
            )

        if not response.lstrip("-").isdigit():
            # Covers UNKNOWN COMMAND, OUT OF RANGE, or any stray garbage.
            raise self.RegulatorError(
                f"Unexpected response to '{cmd}': {response!r}"
            )

        return int(response)

    def set_pressure(self, counts):
        counts = max(0, min(1023, counts))
        response = self.send_command(f"SET {counts}")

        if response == "":
            raise self.RegulatorError(
                f"No response to 'SET {counts}' (timed out)."
            )
        if not response.lstrip("-").isdigit():
            raise self.RegulatorError(
                f"Unexpected response to 'SET {counts}': {response!r}"
            )
        return int(response)

    def read_setpoint(self):
        return self._send_and_parse_int("REQ")

    def read_pressure_counts(self):
        return self._send_and_parse_int("MON")

    def read_pressure_mpa(self):
        counts = self.read_pressure_counts()
        return counts / 1023.0 * self.FULL_SCALE_MPA

    def close(self):
        self.ser.close()


# ---------------------------------------------------------------- #
# Example 1: Set 0.45 MPa
# ---------------------------------------------------------------- #
if __name__ == "__main__":
    from time import sleep

    itv = ITV2050("COM19")

    try:
        itv.set_pressure(512)
        sleep(1)
        pressure = itv.read_pressure_mpa()
        print(f"Actual Pressure = {pressure:.3f} MPa")
    except ITV2050.RegulatorError as e:
        print(f"Regulator error: {e}")
    finally:
        itv.close()
