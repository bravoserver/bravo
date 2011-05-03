from bravo.blocks import blocks

class SpeedyDigPolicy(object):
    """
    A digging policy which lets blocks be broken very fast.
    """

    def is_1ko(self, block):
        return True

    def dig_time(self, block):
        return 0.0

class NotchyDigPolicy(object):
    """
    A digging policy modeled after the Notchian server dig times.
    """

    def is_1ko(self, block):
        return block in (
            blocks["sapling"].slot,
            blocks["snow"].slot,
        )

    def dig_time(self, block):
        return 1.0

dig_policies = {
    "notchy": NotchyDigPolicy(),
    "speedy": SpeedyDigPolicy(),
}
