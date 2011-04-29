class SpeedyDigPolicy(object):
    """
    A digging policy which lets blocks be broken very fast.
    """

    def is_1ko(self, block):
        return True

    def dig_time(self, block):
        return 0.0

dig_policies = {
    "speedy": SpeedyDigPolicy(),
}
