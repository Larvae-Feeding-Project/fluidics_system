import sys
import time
import re
from pathlib import Path
import serial
import json
import threading

# Dict of all available commands
BRIDGE_COMMANDS = {
    "toggle": "TOGGLE",
    "forward": "DIR_FWD",
    "reverse": "DIR_REV",
    "speed": "SPEED:"
}


class FluidicsDriver:
    def __init__(self):
        """
        Control Unit constructor. opens local fluidics data or receives then from control system ( TO BE IMPLEMENTED)
        :return: Fluidics_module object ready for use
        """

        # Path to fluidics module directory
        base_dir = Path(__file__).resolve().parent
        data_path = base_dir / "fluidics_data.json"

        # Open fluidics data dict
        try:
            with open(data_path, "r") as file:
                self.fluidics_data = json.load(file)
            print("Fluidics data loaded successfully")
        except FileNotFoundError:
            print('No fluidics data file found')
        except Exception as e:
            print("Exception occurred, could not open data.json")

        # Threading Synchronization Objects
        self.command_lock = threading.Lock()  # Prevents overlapping commands
        self.ack_event = threading.Event()  # Signals when an ACK is received
        self.command_success = False  # Stores the result (True if ACK, False if NACK/Error)
        self.expected_ack = "OK"  # Change this to whatever your Arduino sends (e.g., "ACK", "DONE")

        try:
            print(f"Connecting to fluidics bridge on {self.fluidics_data["COMPORT"]}...")
            self.fluidics_bridge = serial.Serial(self.fluidics_data["COMPORT"], self.fluidics_data["BAUD_RATE"],
                                                 timeout=1)
            time.sleep(2)  # Arduino reset time

            print("\n--- Connection Established ---")
            print("Type commands directly (e.g., START, STOP, SPEED:5000, DIR_REV)")
            print("Type 'EXIT' or 'QUIT' to close the connection.\n")

            # Start the background listening thread
            self.listening_flag = True
            listener_thread = threading.Thread(target=self._listen_to_bridge, args=(self.fluidics_bridge,), daemon=True)
            listener_thread.start()

        except serial.SerialException as e:
            print(f"\nCould not open serial port: {e}")

        except Exception as e:
            print("Exception occurred, unknown error")

        time.sleep(1)


        self.ready = False

    def __del__(self):
        """
        Fluidics system destructor. Stops listening thread, then closes comport to fluidics_bridge
        :return: VOID
        """

        self.listening_flag = False
        self.fluidics_bridge.close()
        print("Fluidics system closed...")
        time.sleep(2)

    def output(self, amount):
        """
        Outputs the given amount of fluid. Requires the fill tube function to be used first
        :param amount: amount of food to output (im micro-liters)
        :return: boolean true for success, false otherwise
        """

    def flush(self):
        """
        Flushes the tube (used for cleaning). Will either use keypress to stop or a predefined amount
        :return: true when finished, false otherwise
        """

    def fill_tube(self):
        """
        Fills the tube before feeding (above empty container). Will use a predefined amount
        :return: true when finished, false otherwise
        """

    def _send_command(self, command, timeout=2.0):
        """
        Sends a command to the fluidics bridge and waits for an ACK.
        :param command: String of the command to be sent (from BRIDGE_COMMANDS)
        :param timeout: How long to wait for an ACK (in seconds) before failing
        :return: True if ACK received, False if timeout or error
        """
        if command not in BRIDGE_COMMANDS:
            print(f"Invalid command: {command}")
            return False

        # Lock ensures only one command is sent and waited for at a time
        with self.command_lock:
            # 1. Reset the event and success flag BEFORE sending
            self.ack_event.clear()
            self.command_success = False

            # 2. Send the command
            self.fluidics_bridge.write(f"{BRIDGE_COMMANDS[command]}\n".encode('utf-8'))

            # 3. Block execution here until ack_event.set() is called by the listener thread
            # wait() returns True if the event was set, and False if it timed out.
            event_not_timed_out = self.ack_event.wait(timeout)

            # Timeout response
            if not event_not_timed_out:
                print(f"[Timeout] No ACK received for command '{command}' within {timeout}s.")
                return False

            # Return Success or failure, evaluated in listener
            return self.command_success

    def _listen_to_bridge(self):
        """
        Runs in the background. Constantly checks for new data from the Arduino.
        If it detects an ACK/NACK, it signals the waiting _send_command thread.
        """
        while self.listening_flag:
            try:
                if self.fluidics_bridge.in_waiting > 0:
                    incoming_data = self.fluidics_bridge.readline().decode('utf-8', errors='ignore').strip()

                    if incoming_data:
                        # Print bridge message
                        print(f"\n[Arduino]: {incoming_data}")

                        # Incoming data analysis
                        if "ACK" in incoming_data:
                            self.command_success = True
                            self.ack_event.set()  # Wakes up _send_command

                        elif "Arduino Ready" in incoming_data:
                            continue

                        elif incoming_data == "ERR" in incoming_data:
                            self.command_success = False
                            self.ack_event.set()  # Wakes up _send_command, but registers as a failure

            except Exception as e:
                print(f"\n[Serial Read Error]: {e}\n")
                # print("EXITING LISTENING THREAD AND TERMINATING FLUIDICS SYSTEM") NEED TO THINK ABOUT THIS
                break

            # Prevent maxing out CPU
            time.sleep(0.01)

