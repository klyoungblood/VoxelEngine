from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.filter.CommonFilters import CommonFilters
from direct.filter.FilterManager import FilterManager
from odvm.renderer import Renderer
from odvm.optimizedvm import OptimizedVM
import os, json
from direct.showbase.ShowBase import ShowBase


hi_white = (1,1,1,1)
hi_yellow = (1,1,0,1)
hi_red = (1,0,0,1)

def unlock_camera(): base.disable_mouse()


def lock_camera():
   mat = Mat4(base.camera.get_mat())
   mat.invert_in_place()
   base.mouseInterfaceNode.set_mat(mat)
   base.enable_mouse()

class VoxelEngine(ShowBase):
   def NewModel(self):
      model = OptimizedVM( 'VoxelModel', GeomVertexFormat.get_v3c4(), 2 )
      model.set_shader_input( Vec3( 1.0,0.0,0.0), 'gnormal', Vec3( 1.0,0.0,0.0) )
      model.set_shader_input( Vec3(-1.0,0.0,0.0), 'gnormal', Vec3(-1.0,0.0,0.0) )
      model.set_shader_input( Vec3(0.0, 1.0,0.0), 'gnormal', Vec3(0.0, 1.0,0.0) )
      model.set_shader_input( Vec3(0.0,-1.0,0.0), 'gnormal', Vec3(0.0,-1.0,0.0) )
      model.set_shader_input( Vec3(0.0,0.0, 1.0), 'gnormal', Vec3(0.0,0.0, 1.0) )
      model.set_shader_input( Vec3(0.0,0.0,-1.0), 'gnormal', Vec3(0.0,0.0,-1.0) )
      model_path = render.attach_new_node(model)
      model_path.set_color_off()
      model_path.setShaderInput('f_color',(0,0,0,0))
      model_path.set_attrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
      model_path.set_transparency(TransparencyAttrib.MDual)
      model_path.set_render_mode_filled()
      model_path.reparentTo(render)
      self.models.append(model)
      self.model_paths.append(model_path)
      return len(self.models)-1
   
   def MoveCameraTo(self,x,y,z):
      unlock_camera()
      self.labelscamera.set_pos(x,y,z)
      self.labelscamera.look_at(0,0,0)
      base.camera.set_pos(x,y,z)
      base.camera.look_at(0,0,0)
      self.light.setPos(x+50, y+50, z+50)
      lock_camera()

   def __init__(self):
      load_prc_file_data('','coordinate-system yup_right' )
      ShowBase.__init__(self)
            
      base.set_frame_rate_meter(True)
      self.models = []
      self.model_paths = []
      self.ships = []
      
      self.font = loader.loadFont('data/fonts/iceland.ttf')
      self.font.setPixelsPerUnit(100)
   
      tempnode = NodePath(PandaNode("temp node"))
      tempnode.setShader(loader.loadShader("data/shaders/lightinggen.sha"))
      self.cam.node().setInitialState(tempnode.getState())

      self.light = render.attachNewNode("light")
      self.light.setPos(50, 50, 50)
      render.setShaderInput("light", self.light)
      
      normalsBuffer = self.win.makeTextureBuffer("normalsBuffer", 0, 0)
      normalsBuffer.setClearColor((0.5, 0.5, 0.5, 1))
      self.normalsBuffer = normalsBuffer
      normalsCamera = self.makeCamera(
            normalsBuffer, lens=self.cam.node().getLens())
      normalsCamera.node().setScene(render)
      tempnode = NodePath(PandaNode("temp node"))
      tempnode.setShader(loader.loadShader("data/shaders/normalgen.sha"))
      normalsCamera.node().setInitialState(tempnode.getState())

      drawnScene = normalsBuffer.getTextureCard()
      drawnScene.setTransparency(1)
      drawnScene.setColor(1, 1, 1, 0)
      drawnScene.reparentTo(render2d)
      self.drawnScene = drawnScene
      
      self.separation = 0.0005
      self.cutoff = 0.75
      inkGen = loader.loadShader("data/shaders/inkgen.sha")
      drawnScene.setShader(inkGen)
      drawnScene.setShaderInput("separation", LVecBase4(self.separation, 0, self.separation, 0))
      drawnScene.setShaderInput("cutoff", LVecBase4(self.cutoff))
      
      self.labelsbuffer = self.win.makeTextureBuffer("LabelsBuffer", 0, 0)
      self.labelsbuffer.setSort(-2)
      self.labelsbuffer.setClearColor(LVector4(0, 0, 0, 0))
      self.labelscamera = self.makeCamera(self.labelsbuffer, lens=base.cam.node().getLens())
      self.labelsnode = NodePath("new render")
      self.labelscamera.reparentTo(self.labelsnode)
      
      self.starbuffer = self.win.makeTextureBuffer("StarBuffer", 0, 0)
      self.starbuffer.setSort(5)
      self.starbuffer.setClearColor(LVector4(0, 0, 0, 1))
      self.starcamera = self.makeCamera(self.starbuffer, lens=base.cam.node().getLens(),sort=-10)
      self.starnode = NodePath("new render")
      self.starcamera.reparentTo(self.starnode)
      
      self.sky = loader.loadModel("skysphere.bam")
      self.sky.setBin('background',1)
      self.sky.setShaderOff()
      self.sky.setLightOff()
      self.sky.reparentTo(self.starnode)
      #self.sky.reparentTo(render)
      self.sky.setScale(1000)   
      
      #the wrong way to do it      
      #sScene = self.starbuffer.getTextureCard()
      #sScene.setTransparency(1)
      #sScene.reparentTo(render2d)

      #mScene = self.mainbuffer.getTextureCard()
      #mScene.setTransparency(1)
      #mScene.reparentTo(render2d)
            
      #lScene = self.labelsbuffer.getTextureCard()
      #lScene.setTransparency(1)
      #lScene.reparentTo(render2d)
      
      drstars = base.win.makeDisplayRegion(0, 1, 0, 1)
      drstars.setCamera(self.starcamera)
      drstars.setSort(-1)
      
      drlabels = base.win.makeDisplayRegion(0, 1, 0, 1)
      drlabels.setCamera(self.labelscamera)
      drlabels.setSort(10)
            
      base.accept( 'w', self.toggle_wireframes )
      
      base.bufferViewer.position = 'llcorner'
      base.bufferViewer.setCardSize(0,0.25)
      base.bufferViewer.layout   = 'vline'      
      base.accept( 'v', self.toggle_cards )
            
   def SetModelPos(self,modelidx,x,y,z):
      self.model_paths[modelidx].setPos(x,y,z)
      
   def SetModelColor(self, modelidx, r, g, b, a):
      self.model_paths[modelidx].setColor(r,g,b,a)
            
   def SetModelParent(self, child, parent):
      self.model_paths[child].wrtReparentTo(self.model_paths[parent])
      
   def SetModelRotate(self, modelidx, speed, x, y, z):
      self.model_paths[modelidx].hprInterval(speed,(x,y,z)).loop()

   def toggle_wireframe(self, modelidx):
      if self.model_paths[modelidx].get_render_mode() == 2:
         self.model_paths[modelidx].set_render_mode_filled()
      elif self.model_paths[modelidx].get_render_mode() == 1 or self.model_path.get_render_mode() == 0:
         self.model_paths[modelidx].set_render_mode_wireframe()

   def toggle_wireframes(self):
      for i in range(0,len(self.model_paths)):
        self.toggle_wireframe(i)
    
   def toggle_cards(self):
      render.analyze()
      base.bufferViewer.toggleEnable()

   def LoadVoxModel(self, filename, is_engine=False):
      modelidx = self.NewModel()
      srgba = [Vec4(1.0,1.0,1.0,1.0)]*256
      rgba_prcd = False
      xyzi_pmtd = False
      with open(filename, 'rb' ) as f:
         if f.read(4) != b'VOX ': raise IOError
         version = int.from_bytes(f.read(4),byteorder='little')
         while f:
            chunk_id = f.read(4)
            if not chunk_id:
               if not rgba_prcd:
                  srgba[0] = Vec4(0.0,0.0,0.0,0.0)
                  # load default palette
                  rgba_prcd = True
               if not xyzi_pmtd:
                  xyzi_pmtd = True
                  f.seek(8,0)
                  continue
               else: break
            cn = int.from_bytes(f.read(4),byteorder='little')
            cm = int.from_bytes(f.read(4),byteorder='little')
            #print(chunk_id.decode(),cn,cm)
            if chunk_id == b'MAIN': continue
            if chunk_id == b'SIZE':
               sx = int.from_bytes(f.read(4),byteorder='little')
               sz = int.from_bytes(f.read(4),byteorder='little')
               sy = int.from_bytes(f.read(4),byteorder='little')
               ox = int((sx) /2)
               oy = int((sy) /2)
               oz = int((sz) /2)-1
               #print(sx,sy,sz)
               #print(ox,oy,oz)
               continue
            if chunk_id == b'XYZI' and xyzi_pmtd:
               n = int.from_bytes(f.read(4),byteorder='little')
               with self.models[modelidx].optimized(2,3) as m:
                  for i in range(n):
                     x = int.from_bytes(f.read(1),byteorder='little')
                     z = int.from_bytes(f.read(1),byteorder='little')
                     y = int.from_bytes(f.read(1),byteorder='little')
                     c = int.from_bytes(f.read(1),byteorder='little')
                     m.add(0,x-ox,y-oy,z-oz,srgba[c])
               continue
            if chunk_id == b'RGBA' and not rgba_prcd:
               for i in range(1,257):
                  r = int.from_bytes(f.read(1),byteorder='little')
                  g = int.from_bytes(f.read(1),byteorder='little')
                  b = int.from_bytes(f.read(1),byteorder='little')
                  a = int.from_bytes(f.read(1),byteorder='little')
                  if is_engine:
                     srgba[i&255] = Vec4(1.0,1.0,0.80,0.5*(b/255.0)) # engines use blue channel as alpha
                  else:
                     #srgba[i&255] = Vec4(r/255.0,g/255.0,b/255.0,a/255.0) # need to convert to srgb color space
                     srgba[i&255] = Vec4(r/300.0,g/300.0,b/300.0,a/255.0) # need to convert to srgb
               rgba_prcd = True
               continue
            f.seek( cn+cm, 1 )
      return modelidx
           
   def NewShip(self,shipfile):
       with open(shipfile,'r') as jsonfile:
          shipdata = json.load(jsonfile)
          modelidx = self.LoadVoxModel(shipdata['MainModel'])
          childmodels = []
          for child in shipdata['ChildModels']:
             childidx = self.LoadVoxModel(child['Model'])
             self.SetModelPos(childidx, child['Offset'][0], child['Offset'][1], child['Offset'][2])
             self.SetModelParent(childidx, modelidx)
             if child['Rotation'] != [0,0,0,0]:
                self.SetModelRotate(childidx, child['Rotation'][0], child['Rotation'][1], child['Rotation'][2], child['Rotation'][3])
             childmodels.append(childidx)
          engines = []
          for engine in shipdata['EngineFires']:
             fireidx = self.LoadVoxModel(engine['Model'], True)
             self.SetModelPos(fireidx, engine['Offset'][0], engine['Offset'][1], engine['Offset'][2])
             self.SetModelParent(fireidx, modelidx)
             engines.append(fireidx)
          ship = {'modelidx':modelidx, 'highlights':[], 'childmodels': childmodels, 'engines': engines, 'label': -1}
          
          self.ships.append(ship)
          return len(self.ships)-1
   
   def SetShipRotate(self, shipidx, speed, x, y, z):
      ship = self.ships[shipidx]
      self.model_paths[ship['modelidx']].hprInterval(speed,(x,y,z)).loop()
      
   def SetShipHi(self,shipidx,color):
      ship = self.ships[shipidx]
      self.model_paths[ship['modelidx']].setShaderInput('f_color',color)
      for childidx in ship['childmodels']:
         self.model_paths[childidx].setColor(color)
         
   def SetShipChildHi(self,shipidx,childidx,color):
      ship = self.ships[shipidx]
      self.model_paths[ship['childmodels'][childidx]].setShaderInput('f_color',color)
      
   def SetShipPos(self,shipidx,x,y,z):
      ship = self.ships[shipidx]
      self.model_paths[ship['modelidx']].setPos(x,y,z)

   def ShipLookAtCamera(self,shipidx):
      ship = self.ships[shipidx]
      self.model_paths[ship['modelidx']].lookAt(base.camera)
      
   def SetShipLabel(self, shipidx, labeltext):
      ship = self.ships[shipidx]
      label = TextNode('label')
      label.setFont(self.font)
      label.setTextColor(0.5,0.5,1,1)
      label.clearShadow()
      label.setText(labeltext)
      node=self.labelsnode.attachNewNode(label)
      node.setPos(self.model_paths[ship['modelidx']].getPos()+(2.5,-1.5,0))
      node.setShaderOff()
      node.setLightOff()
      node.setBillboardPointEye()
      node.setScale(8)
      ship['label'] = node