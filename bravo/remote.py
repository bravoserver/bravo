from ampoule import AMPChild
import ampoule.pool

from twisted.protocols.amp import ListOf, Command, Integer, String

from bravo.chunk import Chunk
from bravo.ibravo import ITerrainGenerator
from bravo.plugin import retrieve_plugins

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

        plugins = retrieve_plugins(ITerrainGenerator)
        stages = [plugins[g] for g in generators]

        chunk = Chunk(x, z)

        for stage in stages:
            stage.populate(chunk, seed)

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
