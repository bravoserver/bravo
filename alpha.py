from construct import Container, ListContainer

from packets import make_packet

class Inventory(object):

    def __init__(self, unknown1, length):
        self.unknown1 = unknown1
        self.items = [None] * length

    def load_from_tag(self, tag):
        """
        Load data from an Inventory tag.

        These tags are always lists of items.
        """

        for item in tag.tags:
            slot = item["Slot"].value
            if slot < len(self.items):
                self.items[slot] = (item["id"].value, item["Damage"].value,
                    item["Count"].value)

    def save_to_packet(self):
        lc = ListContainer()
        for item in self.items:
            if item is None:
                lc.append(Container(id=0xffff))
            else:
                lc.append(Container(id=item[0], damage=item[1],
                        count=item[2]))

        packet = make_packet(5, unknown1=self.unknown1, length = len(lc),
            items=lc)

        return packet

class Player(object):

    def load_from_container(self, container):
        pass

    def save_to_packet(self):
        pass
