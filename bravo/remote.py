from ampoule import AMPChild
import ampoule.pool

from twisted.protocols.amp import ListOf, Command, Integer, String

from bravo.chunk import Chunk
from bravo.ibravo import ITerrainGenerator
from bravo.plugin import retrieve_sorted_plugins

class MakeChunk(Command):
    arguments = [
        ("x", Integer()),
        ("z", Integer()),
        ("seed", Integer()),
        ("generators", ListOf(String())),
    ]
    response = [
        ("blocks", String()),
        ("metadata", String()),
        ("skylight", String()),
        ("blocklight", String()),
        ("heightmap", String()),
    ]
    errors = {
        Exception: "Exception",
    }

class Slave(AMPChild):
    """
    Process-based peon for processing and populating.
    """

    def make_chunk(self, x, z, seed, generators):
        """
        Create a chunk using the given parameters.
        """

        generators = retrieve_sorted_plugins(ITerrainGenerator, generators)

        chunk = Chunk(x, z)

        for stage in generators:
            stage.populate(chunk, seed)

        chunk.regenerate()

        return {
            "blocks": chunk.blocks.tostring(),
            "metadata": chunk.metadata.tostring(),
            "skylight": chunk.skylight.tostring(),
            "blocklight": chunk.blocklight.tostring(),
            "heightmap": chunk.heightmap.tostring(),
        }

    MakeChunk.responder(make_chunk)

ampoule.pool.pp = ampoule.pool.ProcessPool(
    ampChild=Slave,
)
