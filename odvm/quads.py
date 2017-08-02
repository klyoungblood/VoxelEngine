from panda3d.core import *
from odvm.edges import edge, edges
from odvm.grid import square, grid, intersect, same_corners


class Quad:
   def __init__(self,v0,v1,v2,v3,colour):
      self.diag12 = (v1,v2)
      self.diag03 = (v0,v3)
      self.colour = colour

   def match(self,v1,v2): return same_corners(self.diag12[0],self.diag12[1],v1,v2)

   def attach(self,geom):
      self.geom = geom

      x0,y0,z0 = self.diag12[0]
      x1,y1,z1 = self.diag12[1]
      if   y0 == y1: self.normal = Vec3(0.0,(1.0 if (x0-x1)*(z1-z0) >= 0.0 else -1.0),0.0) # == -ux*vz, u=(x1-x0,0,z1-z0), v=(0,0,z1-z0)
      elif x0 == x1: self.normal = Vec3((1.0 if (z0-z1)*(y1-y0) >= 0.0 else -1.0),0.0,0.0) # == -uz*vy, u=(0,y1-y0,z1-z0), v=(0,y1-y0,0)
      else         : self.normal = Vec3(0.0,0.0,(1.0 if (x1-x0)*(y1-y0) >= 0.0 else -1.0)) # ==  ux*vy, u=(x1-x0,y1-y0,0), v=(0,y1-y0,0)
      self.edges     = ( [], [], [], [] )
      self.points    = ( [], [], [], [] )
      self.vertices  = []
      self.triangles = []
      self.desc = ( [self.diag03[0],self.diag12[0],self.geom.add_edge(self.diag03[0],self.diag12[0],self)],  # v0 -> v1 : left
                    [self.diag12[0],self.diag03[1],self.geom.add_edge(self.diag12[0],self.diag03[1],self)],  # v1 -> v3 : bottom
                    [self.diag03[1],self.diag12[1],self.geom.add_edge(self.diag03[1],self.diag12[1],self)],  # v3 -> v2 : right
                    [self.diag12[1],self.diag03[0],self.geom.add_edge(self.diag12[1],self.diag03[0],self)] ) # v2 -> v0 : top
      self.geom.update_q.add(self)

   def detach(self):
      if hasattr(self,'vertices'):
         self.geom.unused_v.extend(self.vertices )
         self.geom.unused_t.extend(self.triangles)
         del self.vertices
         del self.triangles
         for d in self.desc: self.geom.sub_edge(d[0],d[1],d[2],self)
         del self.edges
         del self.points
         del self.desc
         del self.normal
      self.geom.update_q.discard(self)

   def change_edge(self,f,t):
      for d in self.desc:
         if d[2] is f: d[2] = t

   def query_edges(self):
      build_rqrd = False
      for i,d in enumerate(self.desc):
         if   d[0][0] != d[1][0]: ps = d[2].query_points(d[0][0],d[1][0])
         elif d[0][1] != d[1][1]: ps = d[2].query_points(d[0][1],d[1][1])
         else                   : ps = d[2].query_points(d[0][2],d[1][2])

         if not self.edges[i] or self.points[i] != ps:
            self.points[i][:] = ps
            build_rqrd = True

            del self.edges[i][:]
            self.edges[i].append(d[0])
            if   d[0][0] != d[1][0]:
               pp = d[0][0]
               for p in ps:
                  if p == pp: continue
                  self.edges[i].append(Vec3(p,d[0][1],d[0][2]))
                  pp = p
            elif d[0][1] != d[1][1]:
               pp = d[0][1]
               for p in ps:
                  if p == pp: continue
                  self.edges[i].append(Vec3(d[0][0],p,d[0][2]))
                  pp = p
            else:
               pp = d[0][2]
               for p in ps:
                  if p == pp: continue
                  self.edges[i].append(Vec3(d[0][0],d[0][1],p))
                  pp = p
            self.edges[i].append(d[1])
      return build_rqrd

   def add_triangle(self,e0,k0,e1,k1,e2,k2,dk):
      i0 = self.imap[e0][k0]
      if i0 < 0:
         i0 = self.geom.add_vertex(self.edges[e0][k0],self.normal,self.colour)
         self.imap[e0][k0] = i0
      i1 = self.imap[e1][k1]
      if i1 < 0:
         i1 = self.geom.add_vertex(self.edges[e1][k1],self.normal,self.colour)
         self.imap[e1][k1] = i1
      i2 = self.imap[e2][k2]
      if i2 < 0:
         i2 = self.geom.add_vertex(self.edges[e2][k2],self.normal,self.colour)
         self.imap[e2][k2] = i2
      if dk > 0: self.geom.add_triangle(i0,i1,i2)
      else     : self.geom.add_triangle(i1,i0,i2)

   def build(self):
      if not self.query_edges(): return

      assert( not self.geom.used_v )
      assert( not self.geom.used_t )

      self.geom.unused_v.extend(self.vertices )
      self.geom.unused_t.extend(self.triangles)

      lsts      = ( len(self.edges[0])-1, len(self.edges[1])-1, len(self.edges[2])-1, len(self.edges[3])-1 )
      idxs      = ( [ 0, lsts[0], 0x7f ], [ 0, lsts[1], 0x7f ], [ 0, lsts[2], 0x7f ], [ 0, lsts[3], 0x7f ] )
      attach    = ( -1, 0, 0, 1, -1, -1, 1 )
      self.imap = ( [-1]*len(self.edges[0]), [-2]*len(self.edges[1]), [-3]*len(self.edges[2]), [-4]*len(self.edges[3]) )
      self.imap[0][ 0] = self.imap[3][-1] = self.geom.add_vertex(self.edges[0][0],self.normal,self.colour)
      self.imap[0][-1] = self.imap[1][ 0] = self.geom.add_vertex(self.edges[1][0],self.normal,self.colour)
      self.imap[2][-1] = self.imap[3][ 0] = self.geom.add_vertex(self.edges[3][0],self.normal,self.colour)
      self.imap[1][-1] = self.imap[2][ 0] = self.geom.add_vertex(self.edges[2][0],self.normal,self.colour)

      while True:
         sel = ( 1e9, )
         for e0 in range(4):
            if idxs[e0][2] and idxs[e0][0] != idxs[e0][1]:
               for e in (3,1,2,6):
                  if idxs[e0][2]&(1<<e) != 0:
                     j2 = attach[e]
                     j0 = j2^1
                     k0 = idxs[e0][j0]
                     e2 = (e0+e)&3
                     k2 = idxs[e2][j2]
                     dk = 1-(j0<<1) # +1 or -1
                     if self.imap[e0][k0] == self.imap[e2][k2]: # corner
                        if k2 == idxs[e2][j0]: continue
                        k2 -= dk
                     d  = max( (self.edges[e2][k2]-self.edges[e0][k0]).length_squared(), (self.edges[e2][k2]-self.edges[e0][k0+dk]).length_squared() )
                     if d < sel[0]: sel = (d,e0,j0,k0,e2,j2,k2,dk,e)
         if len(sel) == 1:
            for e0 in range(4):
               if idxs[e0][0] == idxs[e0][1] and 0 < idxs[e0][0] < lsts[e0] and idxs[e0][2]&((1<<1)|(1<<3)) == ((1<<1)|(1<<3)):
                  e1 = (e0+1)&3
                  e2 = (e0+3)&3
                  if idxs[e1][0] == idxs[e1][1] and idxs[e2][0] == idxs[e2][1]: break
            else: break
            idxs[e0][2] = 0
            self.add_triangle(e0,idxs[e0][0],e1,idxs[e1][0],e2,idxs[e2][0],1)
            continue
         d,e0,j0,k0,e2,j2,k2,dk,e = sel
         k1 = k0+dk
         self.add_triangle(e0,k0,e0,k1,e2,k2,dk)
         idxs[e0][j0] = k1
         idxs[e2][j2] = k2
         if e&3 == 2: # opposite
            if j0 == 0:
               idxs[(e0+1)&3][2] &= ~((1<<2)|(1<<6))
               idxs[ e0     ][2] &= ~(1<<3)
               idxs[(e0+3)&3][2]  = 0
               idxs[ e2     ][2] &= ~(1<<1)
            else:
               idxs[(e0+3)&3][2] &= ~((1<<2)|(1<<6))
               idxs[ e0     ][2] &= ~(1<<1)
               idxs[(e0+1)&3][2]  = 0
               idxs[ e2     ][2] &= ~(1<<3)

      del self.imap
      self.vertices    = self.geom.used_v
      self.triangles   = self.geom.used_t
      self.geom.used_v = []
      self.geom.used_t = []

   def change_triangles(self,imap):
      for i in range(len(self.triangles)): self.triangles[i] = imap.pop(self.triangles[i],self.triangles[i])


def point_shift(p,df,dt):
   if   df[0] != dt[0]: return Vec3(p[0]+(1.0 if dt[0] > df[0] else -1.0),p[1],p[2])
   elif df[1] != dt[1]: return Vec3(p[0],p[1]+(1.0 if dt[1] > df[1] else -1.0),p[2])
   else               : return Vec3(p[0],p[1],p[2]+(1.0 if dt[2] > df[2] else -1.0))


class Quads(GeomTriangles):
   def __init__(self,geom):
      GeomTriangles.__init__(self,Geom.UH_static)
      self.make_indexed()
      self.geom       = geom
      self.unused_v   = []
      self.unused_t   = []
      self.used_v     = []
      self.used_t     = []
      self.update_q   = set()
      self.plane_x    = grid()
      self.plane_y    = grid()
      self.plane_z    = grid()
      self.line_x     = edges(self)
      self.line_y     = edges(self)
      self.line_z     = edges(self)
      self.new_quads  = set()
      self.updating   = 0

   def __enter__(self):
      if self.updating == 0: 
         assert( not self.new_quads  )
         assert( not self.update_q   )
      self.updating += 1
      return self

   def __exit__(self,exc_type,exc_value,traceback): 
      self.updating -= 1
      if self.updating == 0:
         while self.new_quads: self.new_quads.pop().attach(self)
         self.vertices = self.geom.modify_vertex_data()
         self.vertex   = GeomVertexWriter(self.vertices,'vertex')
         self.normal   = GeomVertexWriter(self.vertices,'normal')
         self.colour   = GeomVertexWriter(self.vertices,'color' )
         indices       = self.modify_vertices()
         self.index    = GeomVertexRewriter(indices,0)
         while self.update_q: self.update_q.pop().build()

         if self.unused_v:
            self.unused_v.sort()
            num_v    = self.vertices.get_num_rows()
            shrink_v = num_v
            while self.unused_v and self.unused_v[-1] == shrink_v-1:
               self.unused_v.pop()
               shrink_v -= 1
            if shrink_v != num_v: self.vertices.set_num_rows(shrink_v)

         if self.unused_t:
            self.unused_t.sort()
            num_t = indices.get_num_rows()
            refs  = {}
            while self.unused_t:
               num_t -= 3
               idx    = self.unused_t.pop()
               if idx != num_t: refs[idx] = refs.pop(num_t,num_t)
            if refs:
               tmap = {}
               for t,f in refs.items(): 
                  self.index.set_row(f)
                  i0 = self.index.get_data1i()
                  i1 = self.index.get_data1i()
                  i2 = self.index.get_data1i()
                  self.index.set_row(t)
                  self.index.set_data1i(i0)
                  self.index.set_data1i(i1)
                  self.index.set_data1i(i2)
                  tmap[f] = t
               for q in set( s[2] for e in self.line_x.values() for s in e ) | set( s[2] for e in self.line_y.values() for s in e ) | set( s[2] for e in self.line_z.values() for s in e ):
                  q.change_triangles(tmap)
                  if not tmap: break
               assert( not tmap )
            indices.set_num_rows(num_t)

         del self.index
         del indices
         del self.colour
         del self.normal
         del self.vertex
         del self.vertices

   def add_sqr(self,quad):
      self.new_quads.add(quad)
      if   quad.diag12[0][0] == quad.diag12[1][0]: self.plane_x.set(quad.diag12[0][1],quad.diag12[0][2],quad.diag12[1][1],quad.diag12[1][2],quad.diag12[0][0],quad)
      elif quad.diag12[0][1] == quad.diag12[1][1]: self.plane_y.set(quad.diag12[0][0],quad.diag12[0][2],quad.diag12[1][0],quad.diag12[1][2],quad.diag12[0][1],quad)
      else                                       : self.plane_z.set(quad.diag12[0][0],quad.diag12[0][1],quad.diag12[1][0],quad.diag12[1][1],quad.diag12[0][2],quad)

   def sel_sqr(self,v1,v2):
      if   v1[0] == v2[0]:
         self.plane1 = self.plane_x
         return self.plane1.pop1(v1[1],v1[2],v2[1],v2[2],v1[0])
      elif v1[1] == v2[1]:
         self.plane1 = self.plane_y
         return self.plane1.pop1(v1[0],v1[2],v2[0],v2[2],v1[1])
      else:
         self.plane1 = self.plane_z
         return self.plane1.pop1(v1[0],v1[1],v2[0],v2[1],v1[2])

   def sub_sqr(self,sqr):
      self.plane1.popR(sqr)
      try:
         self.new_quads.remove(sqr.cover)
      except KeyError:
         sqr.cover.detach()

   def ret_sqr(self,sqr): self.plane1.set1(sqr)

   def add_edge(self,v0,v1,quad):
      if   v0[0] != v1[0]: return self.line_x.add(v0[0],v1[0],v0[1],v0[2],quad)
      elif v0[1] != v1[1]: return self.line_y.add(v0[1],v1[1],v0[0],v0[2],quad)
      else               : return self.line_z.add(v0[2],v1[2],v0[0],v0[1],quad)

   def sub_edge(self,v0,v1,e,quad):
      if   v0[0] != v1[0]: self.line_x.sub(v0[0],v1[0],e,quad)
      elif v0[1] != v1[1]: self.line_y.sub(v0[1],v1[1],e,quad)
      else               : self.line_z.sub(v0[2],v1[2],e,quad)

   def inhalf(self,v0,v1,v2,v3):
      if   abs(v1[0]-v2[0]) <= abs(v1[1]-v2[1]) >= abs(v1[2]-v2[2]):
         m01 = Vec3(v1[0],round(0.5*(v0[1]+v1[1])),v1[2])
         m02 = Vec3(v2[0],round(0.5*(v0[1]+v2[1])),v2[2])
         m03 = Vec3(v3[0],round(0.5*(v0[1]+v3[1])),v3[2])
         m10 = Vec3(v0[0],round(0.5*(v3[1]+v0[1])),v0[2])
         m11 = Vec3(v1[0],round(0.5*(v3[1]+v1[1])),v1[2])
         m12 = Vec3(v2[0],round(0.5*(v3[1]+v2[1])),v2[2])
      elif abs(v1[0]-v2[0]) <= abs(v1[2]-v2[2]) >= abs(v1[0]-v2[0]):
         m01 = Vec3(v1[0],v1[1],round(0.5*(v0[2]+v1[2])))
         m02 = Vec3(v2[0],v2[1],round(0.5*(v0[2]+v2[2])))
         m03 = Vec3(v3[0],v3[1],round(0.5*(v0[2]+v3[2])))
         m10 = Vec3(v0[0],v0[1],round(0.5*(v3[2]+v0[2])))
         m11 = Vec3(v1[0],v1[1],round(0.5*(v3[2]+v1[2])))
         m12 = Vec3(v2[0],v2[1],round(0.5*(v3[2]+v2[2])))
      else:
         m01 = Vec3(round(0.5*(v0[0]+v1[0])),v1[1],v1[2])
         m02 = Vec3(round(0.5*(v0[0]+v2[0])),v2[1],v2[2])
         m03 = Vec3(round(0.5*(v0[0]+v3[0])),v3[1],v3[2])
         m10 = Vec3(round(0.5*(v3[0]+v0[0])),v0[1],v0[2])
         m11 = Vec3(round(0.5*(v3[0]+v1[0])),v1[1],v1[2])
         m12 = Vec3(round(0.5*(v3[0]+v2[0])),v2[1],v2[2])
      return ( ( v0, m01, m02, m03 ), ( m10, m11, m12, v3 ) )

   def add_vertex(self,v,n,c):
      if self.unused_v:
         idx = self.unused_v.pop()
         self.vertex.set_row(idx)
         self.vertex.set_data3f(v)
         self.normal.set_row(idx)
         self.normal.set_data3f(n)
         self.colour.set_row(idx)
         self.colour.set_data4f(c)
      else:
         idx = self.vertices.get_num_rows()
         self.vertex.set_row(idx)
         self.vertex.add_data3f(v)
         self.normal.set_row(idx)
         self.normal.add_data3f(n)
         self.colour.set_row(idx)
         self.colour.add_data4f(c)
      self.used_v.append(idx)
      return idx

   def add_triangle(self,i0,i1,i2):
      if self.unused_t:
         idx = self.unused_t.pop()
         self.index.set_row(idx)
         self.index.set_data1i(i0)
         self.index.set_data1i(i1)
         self.index.set_data1i(i2)
      else:
         idx = self.get_vertices().get_num_rows()
         self.add_vertices(i0,i1,i2)
      self.used_t.append(idx)
      return idx

   def add_quad(self,v0,v1,v2,v3,colour):
      quad_rqrd = True
      s = self.sel_sqr(v1,v2)
      while s is not None:
         q = s.cover
         if q.match(v1,v2):
            if q.colour[3] == 1.0 and colour[3] == 1.0 or q.colour[3] < 1.0 and colour[3] < 1.0:
               self.sub_sqr(s)
               quad_rqrd = False
            elif colour[3] == 1.0:
               self.sub_sqr(s)
            else:
               self.ret_sqr(s)
               quad_rqrd = False
            break
         elif abs(q.diag12[0][0]-q.diag12[1][0]) < abs(v1[0]-v2[0]) or abs(q.diag12[0][1]-q.diag12[1][1]) < abs(v1[1]-v2[1]) or abs(q.diag12[0][2]-q.diag12[1][2]) < abs(v1[2]-v2[2]):
            qs = self.inhalf(v0,v1,v2,v3)
            if   q.match(qs[0][1],qs[0][2]):
               self.sub_sqr(s) # need alpha processing
               v0,v1,v2,v3 = qs[1]
            elif q.match(qs[1][1],qs[1][2]):
               self.sub_sqr(s) # need alpha processing
               v0,v1,v2,v3 = qs[0]
            else:
               self.ret_sqr(s)
               self.add_quad(qs[0][0],qs[0][1],qs[0][2],qs[0][3],colour)
               v0,v1,v2,v3 = qs[1]
         else:
            self.sub_sqr(s) # need alpha processing
            qs = self.inhalf(q.diag03[0],q.diag12[0],q.diag12[1],q.diag03[1])
            if   same_corners(qs[0][1],qs[0][2],v1,v2):
               v0,v1,v2,v3 = qs[1]
               colour      = q.colour
               break
            elif same_corners(qs[1][1],qs[1][2],v1,v2):
               v0,v1,v2,v3 = qs[0]
               colour      = q.colour
               break
            else:
               q0_first = intersect(qs[0][1],qs[0][2],v1,v2)
               if q0_first: self.add_sqr(Quad(qs[0][0],qs[0][1],qs[0][2],qs[0][3],q.colour))
               else       : self.add_sqr(Quad(qs[1][0],qs[1][1],qs[1][2],qs[1][3],q.colour))
               self.add_quad(v0,v1,v2,v3,colour)
               v0,v1,v2,v3 = qs[1 if q0_first else 0]
               colour      = q.colour
         s = self.sel_sqr(v1,v2)
      if quad_rqrd:
         while True:
            lr_idx = 0 if (v1-v0).length_squared() >= (v1-v3).length_squared() else 1
            for idx in range(2):
               if idx == lr_idx:
                  s = self.sel_sqr(point_shift(v1,v3,v1),v0) # left
                  if s is not None:
                     q = s.cover
                     if q.diag12[1] == v0 and q.diag03[1] == v1 and q.colour == colour:
                        self.sub_sqr(s)
                        v0,v1 = q.diag03[0],q.diag12[0]
                        break
                     self.ret_sqr(s)
                  s = self.sel_sqr(v3,point_shift(v2,v0,v2)) # right
                  if s is not None:
                     q = s.cover
                     if q.diag03[0] == v2 and q.diag12[0] == v3 and q.colour == colour:
                        self.sub_sqr(s)
                        v2,v3 = q.diag12[1],q.diag03[1]
                        break
                     self.ret_sqr(s)
               else:
                  s = self.sel_sqr(point_shift(v1,v0,v1),v3) # top
                  if s is not None:
                     q = s.cover
                     if q.diag03[0] == v1 and q.diag12[1] == v3 and q.colour == colour:
                        self.sub_sqr(s)
                        v1,v3 = q.diag12[0],q.diag03[1]
                        break
                     self.ret_sqr(s)
                  s = self.sel_sqr(v0,point_shift(v2,v3,v2)) # bottom
                  if s is not None:
                     q = s.cover
                     if q.diag12[0] == v0 and q.diag03[1] == v2 and q.colour == colour:
                        self.sub_sqr(s)
                        v0,v2 = q.diag03[0],q.diag12[1]
                        break
                     self.ret_sqr(s)
            else: break
         self.add_sqr(Quad(v0,v1,v2,v3,colour))

   def add(self,scale,i0,j0,k0,vs):
      with self:
         for v in vs:
            x0,y0,z0 = v[0][0],v[0][1],v[0][2]
            x1,y1,z1 = v[0][3],v[0][4],v[0][5]

            x0 = (x0+i0)*scale
            y0 = (y0+j0)*scale
            z0 = (z0+k0)*scale
            x1 = (x1+i0)*scale
            y1 = (y1+j0)*scale
            z1 = (z1+k0)*scale
            if   y0 == y1:
               v0 = Vec3(x0,y0,z1)
               v1 = Vec3(x0,y0,z0)
               v2 = Vec3(x1,y1,z1)
               v3 = Vec3(x1,y1,z0)
            elif x0 == x1:
               v0 = Vec3(x0,y1,z0)                           
               v1 = Vec3(x0,y0,z0)
               v2 = Vec3(x1,y1,z1)
               v3 = Vec3(x1,y0,z1)
            else:
               v0 = Vec3(x0,y1,z1)
               v1 = Vec3(x0,y0,z0)
               v2 = Vec3(x1,y1,z1)
               v3 = Vec3(x1,y0,z0)

            self.add_quad(v0,v1,v2,v3,v[1])