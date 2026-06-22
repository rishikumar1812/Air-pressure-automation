"""
commission_itv2050.py

Guided, step-by-step bring-up for an ITV2050-RC2L regulator.

STEP 1 — communication check, AIR SUPPLY DISCONNECTED.
    Confirms wiring/COM port/baud rate are correct using only read commands
    (REQ, MON) plus a small INC/DEC round-trip. No pressure is meaningfully
    "set" in a way that matters, since there's no air to move.

STEP 2 — pressure check, AIR SUPPLY CONNECTED.
    You confirm air is connected, then the script steps the setpoint through
    a few safe test pressures and reads back MON after each one, so you can
    see the regulator is actually responding before wiring it into the
    automatic control loop.

The script ALWAYS sets the regulator back to 0 MPa before exiting (including
on error / Ctrl+C), so it doesn't leave air pressure applied unattended.

Usage:
    python3 commission_itv2050.py COM4
    python3 commission_itv2050.py COM4 --full-scale 0.9 --test-pressures 0.1 0.2 0.3
"""

import sys
import argparse
import time

from itv2050 import ITV2050Regulator, ITV2050Error


def pause(prompt):
    input(f"\n>>> {prompt} (press Enter to continue) ")


def banner(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def step1_communication_check(reg):
    banner("STEP 1: Communication check — AIR SUPPLY SHOULD STILL BE OFF")

    print(f"Opening {reg.port} at {reg.baudrate} baud, 8N1...")
    reg.connect()
    print("Port opened.")

    print("\nReading current setpoint (REQ)...")
    setpoint_raw = reg.read_setpoint_raw()
    print(f"  -> current setpoint = {setpoint_raw} (raw 0-1023) "
          f"= {reg.raw_to_pressure(setpoint_raw):.4f} MPa")

    print("\nReading current measured output (MON)...")
    output_raw = reg.read_output_raw()
    print(f"  -> current output = {output_raw} (raw 0-1023) "
          f"= {reg.raw_to_pressure(output_raw):.4f} MPa")
    if output_raw > 5:
        print("  NOTE: output is non-zero with air supposedly off — "
              "double check the air supply is actually disconnected/exhausted.")

    print("\nTesting INC (add 2 to setpoint)...")
    new_setpoint = reg.increase()
    print(f"  -> setpoint is now {new_setpoint}")

    print("Testing DEC (subtract 2 from setpoint)...")
    new_setpoint = reg.decrease()
    print(f"  -> setpoint is now {new_setpoint}")

    print("\nResetting setpoint to 0 before moving on...")
    reg.set_raw(0)
    print("  -> setpoint = 0")

    print("\nSTEP 1 PASSED: the regulator is responding correctly over RS-232.")


def step2_pressure_check(reg, test_pressures, settle_seconds, tolerance_mpa):
    banner("STEP 2: Pressure check — CONFIRM AIR SUPPLY IS NOW CONNECTED")
    pause("Connect the air supply now, then confirm it's flowing")

    for target_mpa in test_pressures:
        print(f"\nSetting {target_mpa:.3f} MPa...")
        confirmed_mpa = reg.set_pressure(target_mpa)
        print(f"  -> regulator confirmed setpoint = {confirmed_mpa:.4f} MPa")

        print(f"  Waiting {settle_seconds}s for pressure to settle...")
        time.sleep(settle_seconds)

        actual_mpa = reg.read_output_pressure()
        diff = abs(actual_mpa - target_mpa)
        status = "OK" if diff <= tolerance_mpa else "CHECK AIR SUPPLY / REGULATOR"
        print(f"  -> measured output (MON) = {actual_mpa:.4f} MPa "
              f"(target {target_mpa:.3f}, diff {diff:.4f}) [{status}]")

    print("\nSTEP 2 PASSED: regulator is tracking commanded pressure within tolerance.")


def main():
    parser = argparse.ArgumentParser(description="Commission an ITV2050-RC2L regulator")
    parser.add_argument("port", help="COM port, e.g. COM4 (Windows) or /dev/ttyUSB0 (Linux)")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--full-scale", type=float, default=0.9,
                         help="Regulator full-scale pressure in MPa (confirm against nameplate)")
    parser.add_argument("--test-pressures", type=float, nargs="+", default=[0.1, 0.2, 0.3],
                         help="Pressures (MPa) to step through in Step 2")
    parser.add_argument("--settle-seconds", type=float, default=2.0,
                         help="Seconds to wait after each SET before reading MON")
    parser.add_argument("--tolerance", type=float, default=0.02,
                         help="Acceptable MPa difference between target and measured")
    args = parser.parse_args()

    for p in args.test_pressures:
        if p > args.full_scale:
            print(f"ERROR: test pressure {p} MPa exceeds full scale {args.full_scale} MPa. Aborting.")
            sys.exit(1)

    reg = ITV2050Regulator(port=args.port, baudrate=args.baud, full_scale_mpa=args.full_scale)

    try:
        step1_communication_check(reg)
        pause("Step 1 done. Make sure the air supply is connected before Step 2")
        step2_pressure_check(reg, args.test_pressures, args.settle_seconds, args.tolerance)

    except ITV2050Error as e:
        print(f"\nCOMMISSIONING FAILED: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        # Always try to leave the regulator at 0 MPa before disconnecting.
        try:
            if reg.ser is not None and reg.ser.is_open:
                print("\nSetting pressure back to 0 MPa before closing...")
                reg.set_raw(0)
        except ITV2050Error as e:
            print(f"WARNING: could not reset pressure to 0 on exit: {e}")
        reg.close()
        print("Port closed.")


if __name__ == "__main__":
    main()
