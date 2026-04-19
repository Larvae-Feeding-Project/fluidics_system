# Fluidics System

This repo contains our implementation of the fluidics system. 
We decided to use the Chorny BT100M peristaltic pump. Its external control doesn't directly
connect to PC, so we built a bridge module using an arduino and their DA-15 connector diagram.
The fluidics_arduino_bridge is our arduino code, while the fluidics_module.py is the module the
rest of the project (Control unit) uses.
This repo also includes utils that utilize the pump (using the bridge)

## Dependencies - nees update

1. pySerial
2. keyboard
3. time
4. serial
5. json
6. pathlib

## Utils
Utils can be found in the fluidics_utils folder. They can be used for calibration, introduction of new commands and more. The current utils are:
1. command_sender: initiates the movement system, and then enable the user to send G-code directly to the movement_system.

## TODO's
1. Finialize and verify bridge
2. build fluidics_module

## Usage - nees update
IN THE FUTURE WILL BE USED BY CONTROL UNIT


## Contributing

Asaf Shasha and Nitai Gildor
