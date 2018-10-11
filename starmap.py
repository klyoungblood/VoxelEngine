from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.filter.CommonFilters import CommonFilters
from direct.filter.FilterManager import FilterManager
from odvm.renderer import Renderer
from odvm.optimizedvm import OptimizedVM
import os, json, csv, math, random

from voxelengine import *

loadPrcFileData('', 'win-size 1280 720') 
loadPrcFileData('', 'show-frame-rate-meter  t')

game = VoxelEngine()

lymult = 12

colors = {
    'yellow': (1,1,0,1),
    'red': (1,0,0,1),
    'orange': (1,0.5,0,1),
    'white': (1,1,1,1),
    'brown': (0.5, 0, 0, 1)
}

with open('starlist.csv','r') as csvfile:
    stars = csv.reader(csvfile)
    for row in stars:
        star = {'name':row[0],'l':float(row[1]),'dist':float(row[2]),'color':row[3].lstrip()}
        lrad = -math.radians(star['l'])
        lrad -= 0.3
        x = (star['dist']*lymult) * math.cos(lrad)
        y = (star['dist']*lymult) * math.sin(lrad)
        if star['color'] == 'binary':
            starn = game.NewShip(os.path.join('data','ships','binary_star.json'))
            color1 = row[4].lstrip()
            color2 = row[5].lstrip()
            game.SetShipChildHi(starn,0,colors[color1])
            game.SetShipChildHi(starn,1,colors[color2])            
        elif star['color'] == 'trinary':
            starn = game.NewShip(os.path.join('data','ships','trinary_star.json'))
            color1 = row[4].lstrip()
            color2 = row[5].lstrip()
            color3 = row[6].lstrip()
            game.SetShipChildHi(starn,0,colors[color1])
            game.SetShipChildHi(starn,1,colors[color2])
            game.SetShipChildHi(starn,2,colors[color3])
        else:
            starn = game.NewShip(os.path.join('data','ships','star.json'))
            game.SetShipHi(starn, colors[star['color']])
        game.SetShipPos(starn, x, y, 0.0)
        game.SetShipRotate(starn, random.uniform(10,30), 0, 0, 360)
        game.SetShipLabel(starn, "- "+star['name'])

game.MoveCameraTo(0,-50,400)
game.run()
