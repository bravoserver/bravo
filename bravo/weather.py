from bravo.beta.packets import make_packet

class WeatherVane(object):
    """
    An indicator of the current weather.

    The vane is meant to centrally remember what the weather is currently
    like, to keep all clients on the same page.
    """

    def __init__(self, factory):
        self.factory = factory

    _weather = "sunny"

    @property
    def weather(self):
        return self._weather

    @weather.setter
    def weather(self, value):
        if self._weather != value:
            self._weather = value
            self.factory.broadcast(self.make_packet())

    def make_packet(self):
        # XXX this probably should use the factory's mode rather than
        # hardcoding creative mode. Probably.
        if self.weather == "rainy":
            return make_packet("state", state="start_rain", mode="creative")
        elif self.weather == "sunny":
            return make_packet("state", state="stop_rain", mode="creative")
        else:
            return ""
