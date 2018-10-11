from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.filter.CommonFilters import CommonFilters
from direct.filter.FilterManager import FilterManager
from odvm.renderer import Renderer
from odvm.optimizedvm import OptimizedVM
import os, json

from voxelengine import *

loadPrcFileData('', 'win-size 1280 720') 
loadPrcFileData('', 'show-frame-rate-meter  t')

game = VoxelEngine()

core = game.NewShip(os.path.join('data','ships','carrier.json'))

game.SetShipRotate(core, 20, 360, 0, 0)
#game.SetShipHi(core, hi_yellow)
#game.ShipLookAtCamera(core)

game.MoveCameraTo(-40,40,40)
game.run()
