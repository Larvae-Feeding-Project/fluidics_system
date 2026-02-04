import serial


class FluidicsDriver:
    def __init__(self):
        """
        Control Unit constructor. Creates movement system, fluidics system and CV objects.
        :return: MovementDriver object
        """
        # Probably need to read from json here (comport etc):

        self.ready = False

    def __del__(self):
        """
        Fluidics system destructor. Stops system action and then closes port
        :return: VOID
        """

    def output(self, amount):
        """
        Output the given amount of fluid. Requires the fill tube function to be used first
        :param amount: amount of food to output (im micro-liters)
        :return: boolean true for success, false otherwise
        """
        if not self.ready:
            print("Tube was not initialized yet")
            return False

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
        self.ready = True
