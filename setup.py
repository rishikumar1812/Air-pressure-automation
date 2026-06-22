"""
Minimal standalone serial test for SMC ITV2050-RC2L E/P Regulator.

Purpose: isolate the serial link from all GUI/dashboard code so we can
confirm communication works at the lowest level before integrating.

Per SMC manual (ITV2-OM00116):
    Baud      : 9600
    Data bits : 8
    Stop bits : 1
    Parity    : None
    End code  : CR LF  (\r\n)   <-- critical, easy to miss
    Charset   : ASCII

Commands:
    "REQ"    -> regulator replies with current SET value (nn)
    "MON"    -> regulator replies with current output PRESSURE value (nn)
    "SET nn" -> set output to nn (0-1023), regulator echoes nn or error
    "INC"    -> +2 to current setting
    "DEC"    -> -2 to current setting
"""

import serial
import serial.tools.list_ports
import time


# ---------------------------------------------------------------- #
# CONFIG - change PORT to match your setup, or use find_port()
# ---------------------------------------------------------------- #
PORT = "COM19"
BAUDRATE = 9600
TIMEOUT = 1.0   # seconds to wait for a response


def find_port():
    """List all available ports so you can confirm COM19 is really
    the regulator and not one of the other 3 DB9 channels."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No COM ports found at all. Check Device Manager.")
        return None

    print("Available ports:")
    for i, p in enumerate(ports):
        print(f"  {i + 1}: {p.device} - {p.description} "
              f"(hwid: {p.hwid})")
    return ports


def open_connection(port=PORT):
    """Open the serial port with explicit, conservative settings.

    NOTE: dsrdtr=False and rtscts=False are set explicitly so pyserial
    does NOT toggle DTR/RTS lines on open. Since only pins 2,3,4 are
    wired on your cable these shouldn't reach the regulator anyway,
    but disabling them removes one variable.
    """
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = BAUDRATE
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = TIMEOUT
    ser.write_timeout = TIMEOUT
    ser.dsrdtr = False
    ser.rtscts = False
    ser.xonxoff = False

    ser.open()

    # Drain anything stale sitting in the OS buffers before we start.
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    return ser


def send_command(ser, command, label=None):
    """Send a single command with the mandatory CR/LF terminator,
    then read back whatever the regulator sends within TIMEOUT.

    Returns the raw response bytes (may be empty on timeout).
    """
    label = label or command
    frame = (command.strip() + "\r\n").encode("ascii")

    print(f"\n--- {label} ---")
    print(f"  TX (raw bytes) : {frame!r}")

    ser.reset_input_buffer()  # clear any leftover noise before sending
    ser.write(frame)
    ser.flush()

    start = time.time()
    response = ser.read_until(b"\n")  # SMC end code is CR/LF
    elapsed = time.time() - start

    if response:
        print(f"  RX (raw bytes) : {response!r}")
        try:
            print(f"  RX (decoded)   : {response.decode('ascii').strip()!r}")
        except UnicodeDecodeError:
            print("  RX (decoded)   : <non-ASCII garbage received>")
    else:
        print(f"  RX             : NO RESPONSE (timed out after {elapsed:.2f}s)")

    return response


def run_basic_test(port=PORT):
    print("=" * 60)
    print("STEP 1: Listing ports (confirm COM number is correct)")
    print("=" * 60)
    find_port()

    print(f"\nOpening {port} at {BAUDRATE} baud...")
    ser = open_connection(port)
    print(f"Port open: {ser.is_open}")

    try:
        # REQ should ALWAYS work even with zero air supply connected,
        # since it just reads back the last SET value in memory.
        # If REQ fails, this is a pure comms problem, not an air/pressure
        # problem - test this FIRST, before connecting air.
        send_command(ser, "REQ", "Confirm current setting (REQ)")

        # MON requires the device to actually have a real pressure
        # reading. Without air supply, this may return 0, an error,
        # or nothing at all depending on firmware - that's expected
        # and not necessarily a fault. See edge cases below.
        send_command(ser, "MON", "Read live output pressure (MON)")

    finally:
        ser.close()
        print("\nPort closed.")


if __name__ == "__main__":
    run_basic_test()
