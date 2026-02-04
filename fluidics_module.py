import serial


class FluidicsDriver:
    def __init__(self):
        """
        Control Unit constructor. Creates movement system, fluidics system and CV objects.
        :return: MovementDriver object
        """
        try:
            self.fluidic_module = fluidics_module()
            self.movement_module = movement_driver.MovementDriver()
            self.cv_module = cv_module()
        except:
            print("Subsystem initiation failed")
            exit(1)

    def __del__(self):
        """
        Fluidics system destructor. Stops system action and then closes port
        :return: VOID
        """
        # Close movement serial
        self.movement_module.__del__()
        self.cv_module.__del__()
        self.fluidics_module.__del__()