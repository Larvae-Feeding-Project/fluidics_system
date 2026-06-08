import sys
import time
from pathlib import Path
import serial
import json
import threading
from fluidics_system.fluidics_enums import *

# Dict of all available commands
BRIDGE_COMMANDS = {
    "toggle": "TOGGLE",
    "forward": "DIR_FWD",
    "reverse": "DIR_REV",
    "speed": "SPEED:",
    "estop": "ESTOP"
}

# Presets - PLACEHOLDERS until field validation
FLUSH_AMOUNT = 10000.0
FLUSH_SPEED = 6000.0
FEED_SPEED = 50.0
TUBE_VOLUME = 100000.0  # Placeholder


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

        # Establish connection and set initial states
        self._connect_and_start(is_reconnect=False)

    def _connect_and_start(self, is_reconnect=False):
        """
        Handles establishing the serial connection, starting the listener thread,
        and synchronizing the initial hardware state.
        """
        # Print texts depending on first connection or reconnection
        action_text = "Reconnecting to" if is_reconnect else "Connecting to"
        success_text = "reestablished" if is_reconnect else "established"

        try:
            print(f"{action_text} fluidics bridge on {self.fluidics_data['COMPORT']}...")
            self.fluidics_bridge = serial.Serial(
                self.fluidics_data["COMPORT"],
                self.fluidics_data["BAUD_RATE"],
                timeout=1
            )
            time.sleep(2)  # Wait for serial initialization / Arduino reset
            print(f"\nFluidics system connection {success_text}\n")

            # Start the background listening thread
            self.listening_flag = True
            listener_thread = threading.Thread(target=self._listen_to_bridge, daemon=True)
            listener_thread.start()

            # Initializes states (speed and direction)
            self._initialize_hardware_state()

            # Clear the tube after reconnection
            if is_reconnect:
                self.clear_tube()

        except serial.SerialException as e:
            print(f"\n>> Connection failed: {e}. Check USB connection.\n")
        except Exception as e:
            print(f"\n>> Exception occurred: {e}\n")


    def _initialize_hardware_state(self):
        """
            Sets default software states and pushes the initial configuration
        commands down to the Arduino bridge.
        """
        self.current_speed = 0
        self.current_dir = Direction.FORWARD
        self.running = False

        time.sleep(1)
        self._set_speed(200)  # Initial value that the pump registers
        time.sleep(2)
        self._set_direction(Direction.FORWARD)

        self.ready = False

    def __del__(self):
        """
        Fluidics system destructor. Stops listening thread, then closes comport to fluidics_bridge
        :return: VOID
        """
        # Empty tube back into container
        self.clear_tube()

        # Shut down listening
        self.listening_flag = False
        self.fluidics_bridge.close()
        print("Fluidics system closed...")
        time.sleep(1)

    def output(self, amount):
        """
        Outputs the given amount of fluid. Requires the fill tube function to be used first
        :param amount: amount of food to output (im micro-liters)
        :return: boolean true for success, false otherwise
        """
        if not self._set_speed(FEED_SPEED): return False
        if not self._set_direction(Direction.FORWARD): return False
        if not self._start_stop(): return False
        time.sleep(amount / FEED_SPEED)
        return self._start_stop()

    def flush(self):
        """
        Flushes the tube (used for cleaning). Uses a predefined amount
        :return: true when finished, false otherwise
        """
        if not self._set_speed(FLUSH_SPEED): return False
        if not self._set_direction(Direction.FORWARD): return False
        if not self._start_stop(): return False
        time.sleep(FLUSH_AMOUNT/ FLUSH_SPEED)
        return self._start_stop()

    def fill_tube(self):
        """
        Fills the tube before feeding (above empty container). Will use a predefined amount
        :return: true when finished, false otherwise
        """
        try:
            if not self._set_speed(FLUSH_SPEED): return False
            time.sleep(1)
            if not self._set_direction(Direction.FORWARD): return False
            time.sleep(1)
            if not self._start_stop(): return False
            time.sleep(TUBE_VOLUME / FLUSH_SPEED + 1)

            # Returns True if successful, False if it failed
            stopped_successfully = self._start_stop()
            if stopped_successfully:
                self.ready = True
                return True
            return False

        except Exception as e:
            print("ERROR: Exception occurred while filling tube")
            return False

        # May need movement system to touch surface before starting

    def clear_tube(self):
        """
        Clears the tube after feeding and when closing. Will use a predefined amount
        :return: true when finished, false otherwise
        """
        try:
            if not self._set_speed(FLUSH_SPEED): return False
            time.sleep(1)
            if not self._set_direction(Direction.REVERSE): return False
            time.sleep(1)
            if not self.running:
                if not self._start_stop(): return False
            time.sleep(TUBE_VOLUME / FLUSH_SPEED)

            # Returns True if successful, False if it failed
            return self._start_stop()
        except Exception as e:
            print("ERROR: Exception occurred while filling tube")
            return False

    def _start_stop(self):
        """
        Starts/Stops the pump (toggle)
        :return: true if successful (received ack from bridge), false otherwise
        """

        rsp = self._send_command(f"toggle")

        if not rsp:
            return False

        self.running = not self.running
        return True

    def _set_speed(self, speed):
        """
        Sets the speed of the pump.
        :param speed: The speed to set the pump (between 31 and 10000)
        :return: true if successful (received ack from bridge), false otherwise
        """
        if speed < 0 or speed > 10000:
            print("Speed must be between 0 to 10000")
            return False

        rsp = self._send_command(f"speed {speed}")

        if rsp:
            self.current_speed = speed
            return True
        return False

    def _set_direction(self, direction: Direction):
        """
        Sets the direction of the pump.
        :param direction: The direction to send the machine. Values from Direction enum
        :return: true if successful (received ack from bridge), false otherwise
        """
        if direction == Direction.FORWARD:
            rsp = self._send_command("forward")
            if rsp:
                self.current_dir = Direction.FORWARD
                return True

        elif direction == Direction.REVERSE:
            rsp = self._send_command("reverse")
            if rsp:
                self.current_dir = Direction.REVERSE
                return True

        return False

    def _send_command(self, command_input, timeout=2.0):
        """
        Sends a command to the fluidics bridge and waits for an ACK.
        """
        print(f"Processing command: {command_input}")

        # Split string by spaces
        parts = str(command_input).strip().split()
        if not parts:
            return False

        base_cmd = parts[0].lower()

        if base_cmd not in BRIDGE_COMMANDS:
            print(f"Invalid command: {base_cmd}")
            return False

        # Construct the string for bridge
        serial_msg = BRIDGE_COMMANDS[base_cmd]

        # If there's a second argument (like the 5000 in "speed 5000"), append it directly
        if len(parts) > 1:
            serial_msg += parts[1]

        with self.command_lock:
            self.ack_event.clear()
            self.command_success = False

            # Send command to bridge with the newline character your Arduino expects
            self.fluidics_bridge.write(f"{serial_msg}\n".encode('utf-8'))

            # Wait for ACK
            event_not_timed_out = self.ack_event.wait(timeout)

            if not event_not_timed_out:
                print(f"[Timeout] No ACK received for '{serial_msg}' within {timeout}s.")
                return False

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
                        print(f"\n[Arduino]: {incoming_data}")  # Print received message

                        # Incoming data analysis
                        if "ACK" in incoming_data:
                            self.command_success = True
                            self.ack_event.set()  # Wakes up _send_command

                        # Bridge ready message, happens at startup
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

    def emergency_stop(self):
        """
            Commands the Arduino to reboot via Watchdog, then reestablishes the connection.
        """
        print(">> FLUIDICS EMERGENCY STOP TRIGGERED!")

        if hasattr(self, 'fluidics_bridge') and self.fluidics_bridge.is_open:
            # Send the kill command
            self.fluidics_bridge.write(b"ESTOP\n")
            self.fluidics_bridge.flush()

            # Shut down listening thread and close serial port
            self.listening_flag = False
            time.sleep(0.5)
            self.fluidics_bridge.close()

            # Reset software state
            self.current_speed = 0
            self.running = False
            self.ready = False
            self.command_success = False
            self.ack_event.set()

            # Start a background thread to reconnect so the UI does not freeze
            threading.Thread(target=self._reconnect_bridge, daemon=True).start()

    def _reconnect_bridge(self):
        """
        Waits for the Arduino bootloader to finish, then rebuilds the serial connection.
        """
        print(">> Waiting for Arduino to reboot...")
        time.sleep(3)  # Give bridge time to restart

        self._connect_and_start(is_reconnect=True)
