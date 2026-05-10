
from fluidics_system.fluidics_module import FluidicsDriver


def main():

    fluidics_system = FluidicsDriver()

    # Main loop: Wait for user keyboard input
    while True:
        user_cmd = input("> ")
        cleaned_cmd = user_cmd.strip().upper()

        # End connection
        if cleaned_cmd in ['EXIT', 'QUIT']:
            print("Closing programn...")
            fluidics_system.__del__()
            break

        # Send the command if it's not empty
        if cleaned_cmd:
            fluidics_system._send_command(cleaned_cmd)

if __name__ == "__main__":
    main()