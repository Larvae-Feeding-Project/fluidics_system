from fluidics_system.fluidics_module import FluidicsDriver

"""
This module lets you send commands directly to the pump (meaning to the bridge)
Valid commands are in BRIDGE_COMMANDS in fluidics_module.py (Which has all the commands the bridge currently has)
"""
def main():

    fluidics_system = FluidicsDriver()

    while True:
        user_cmd = input("> ")
        cleaned_cmd = user_cmd.strip()

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