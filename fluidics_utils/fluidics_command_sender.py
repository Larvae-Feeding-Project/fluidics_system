import serial
import time
import threading
import sys

# Global flag to signal the reading thread when to stop
is_running = True


def listen_to_arduino(arduino_conn):
    """
    This function runs in the background. It constantly checks for
    new data from the Arduino and prints it to the console.
    """
    while is_running:
        try:
            # Check if there is data waiting in the serial buffer
            if arduino_conn.in_waiting > 0:
                # Read, decode, and clean up the incoming line
                incoming_data = arduino_conn.readline().decode('utf-8', errors='ignore').strip()

                if incoming_data:
                    # Print the Arduino's message.
                    # The '\n> ' ensures your typing prompt isn't visually ruined.
                    print(f"\n[Arduino]: {incoming_data}\n> ", end="")
                    sys.stdout.flush()

        except Exception as e:
            print(f"\n[Serial Read Error]: {e}")
            break

        # A tiny sleep prevents this thread from maxing out your CPU
        time.sleep(0.01)


def main():
    global is_running

    port = 'COM7'  # Update this to your actual port
    baudrate = 115200

    try:
        print(f"Connecting to Arduino on {port}...")
        arduino = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Give the Arduino a moment to reset

        print("\n--- Connection Established ---")
        print("Type commands directly (e.g., START, STOP, SPEED:5000, DIR_REV)")
        print("Type 'EXIT' or 'QUIT' to close the connection.\n")

        # 1. Start the background listening thread
        listener_thread = threading.Thread(target=listen_to_arduino, args=(arduino,), daemon=True)
        listener_thread.start()

        # 2. Main loop: Wait for user keyboard input
        while True:
            user_cmd = input("> ")
            cleaned_cmd = user_cmd.strip().upper()

            # Handle the exit command to close gracefully
            if cleaned_cmd in ['EXIT', 'QUIT']:
                print("Closing connection...")
                is_running = False  # Stop the background thread
                break

            # Send the command if it's not empty
            if cleaned_cmd:
                arduino.write(f"{cleaned_cmd}\n".encode('utf-8'))

    except serial.SerialException as e:
        print(f"\nCould not open serial port: {e}")
        print("Make sure the port is correct and not open in the Arduino IDE Serial Monitor.")
    except KeyboardInterrupt:
        print("\nProgram forced to close (Ctrl+C).")
        is_running = False
    finally:
        # Clean up the serial connection before closing the script
        if 'arduino' in locals() and arduino.is_open:
            arduino.close()
        print("Port closed. Goodbye.")


if __name__ == "__main__":
    main()