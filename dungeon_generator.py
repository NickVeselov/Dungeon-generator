
import re
import math
import random
import rooms_generator_module
import corridor_generator_module

# if (when) this doesn't work, copy 64 bit Python 3.3 fbx.pyd and fbxsip.pyd from the Autodesk FBX SDK
# into this directory
import fbx

# FbxDouble3 unpacker
def tolist(x):
  return [x[i] for i in range(3)]

# FbxDouble3 packer
def tovec3(x):
  return fbx.FbxDouble3(x[0], x[1], x[2], x[3])

def add3(x, y):
  return [x[i]+y[i] for i in range(3)]

def abs3(x):
  return [abs(x[i]) for i in range(3)]

def sub3(x, y):
  return [x[i]-y[i] for i in range(3)]

def div3byconst(x,num):
  return [x[i]/num for i in range(3)]

def neg3(x):
  return [-x[i] for i in range(3)]

def less3(x,y):
    return ((x[0] < y[0]) and (x[1]<y[1]) and (x[2]<y[2]))

def round3(x):
    return [round(x[i]) for i in range(3)]

def xy_location(x):
  return (round(x[0]), round(x[1]))

def rotateZ(v, angle):
  sz = math.sin(angle * (3.14159/180))
  cz = math.cos(angle * (3.14159/180))
  return [
    cz * v[0] - sz * v[1],
    sz * v[0] + cz * v[1],
    v[2]
  ]

def lim360(x):
  x = x + 360 if x < 0 else x
  x = x - 360 if x >= 360 else x
  return round(x)
  

class dungeon_generator:
  def __init__(self):  
    self.sdk_manager = fbx.FbxManager.Create()
    if not self.sdk_manager:
      sys.exit(1)
    
    self.io_settings = fbx.FbxIOSettings.Create(self.sdk_manager, fbx.IOSROOT)
    self.sdk_manager.SetIOSettings(self.io_settings)

  def read_components(self):
    importer = fbx.FbxImporter.Create(self.sdk_manager, "")    

    result = importer.Initialize("scenes/components.fbx", -1, self.io_settings)
    if not result:
      raise BaseException("could not find components file")
    
    #scene creation
    self.components = fbx.FbxScene.Create(self.sdk_manager, "")
    result = importer.Import(self.components)
    importer.Destroy()

    root = self.components.GetRootNode()
    top_level = [root.GetChild(i) for i in range(root.GetChildCount())]

    # child nodes matching this pattern are feature markup
    connectors_regex_pattern = re.compile('(\<|\>)([^.]+)(\..*)?')

    incoming = self.incoming = {}
    outgoing = self.outgoing = {}
    tiles = self.tiles = {}
    self.room = rooms_generator_module.rooms_generator()
    self.corridor = corridor_generator_module.corridor_generator()

    self.room.incoming = {}
    self.corridor.incoming = {}

    self.room.outgoing = {}
    self.corridor.outgoing = {}

    self.room.bb = {}
    self.corridor.bb = {}

    self.room.tiles = {}
    self.corridor.tiles = {}

    self.doorframes = {}
    self.unused = {}

    # find the tiles in the file with at least one child (the connectors)
    for node in top_level:
      if node.GetChildCount():

        #get the name of the tile
        tile_name = node.GetName()

        #identify tile type

        tile_name_parts = tile_name.split('_')
        is_room_part = False
        is_corridor_part = False
        is_doorframe = False

        
        for name in tile_name_parts:
            if name == "room":
                is_room_part = True
            if name == "corridor":
                is_corridor_part = True
            if name == "doorframe":
                is_doorframe = True

        #add tile to the appropriate tile dictionary
        if is_room_part:
            self.room.tiles[tile_name] = node
        elif is_corridor_part:
            self.corridor.tiles[tile_name] = node
        elif is_doorframe:
            self.doorframes.tiles[tile_name] = node        

        #read connectors of the tile
        connectors = [node.GetChild(i) for i in range(node.GetChildCount())]        

        print("%s has %d children" % (tile_name, node.GetChildCount()))

        max_x = 0
        max_y = 0
        max_z = 0
        #for each connector
        for c in connectors:
          conn_name = c.GetName();
          # use a regular expression to match the connector name
          # and discard any trailing numbers
          match = connectors_regex_pattern.match(conn_name)
          if match:
            direction = match.group(1)
            feature_name = match.group(2)
            print("  %s %s %s" % (tile_name, direction, feature_name))
            trans = c.LclTranslation.Get()
            rot = c.LclRotation.Get()

            max_x = max(max_x, abs(trans[0]))
            max_y = max(max_y, abs(trans[1]))
            max_z = max(max_z, abs(trans[2]))

            result = (feature_name, tile_name, trans, rot)

            if direction == '>':
              # outgoing tile indexed by tile_name
              idx = tile_name
              if is_room_part:
                dict = self.room.outgoing
              elif is_corridor_part:
                dict = self.corridor.outgoing
              elif is_doorframe:
                dict = self.doorframes
              else:
                dict = self.unused
            else:
              # incoming tile indexed by feature name
              idx = feature_name
              if is_room_part:
                dict = self.room.incoming
              elif is_corridor_part:
                dict = self.corridor.incoming
              elif is_doorframe:
                dict = self.doorframes
              else:
                dict = self.unused
            if not idx in dict:
              dict[idx] = []
            dict[idx].append(result)

        if is_corridor_part:
            max_dim = max(max_x,max_y,max_z)

            if round(max_x) == 0:
                max_x = max_dim
            if round(max_y) == 0:
                max_y = max_dim
            if round(max_z) == 0:
                max_z = max_dim
            self.corridor.bb[tile_name] = (round(2*max_x),round(2*max_y),round(2*max_z))
            
    # at this point incoming and outgoing index connectors
    # tiles indexes the tiles by name.
    print("Rooms.incoming:", self.room.incoming)
    print("Rooms.outgoing:", self.room.outgoing)

    print("Corridors.incoming:", self.corridor.incoming)
    print("Corridors.outgoing:", self.corridor.outgoing)

    print("Doorframes:", self.doorframes)

  def get_format(self, name):
    reg = self.sdk_manager.GetIOPluginRegistry()
    for idx in range(reg.GetWriterFormatCount()):
      desc = reg.GetWriterFormatDescription(idx)
      print(desc)
      if name in desc:
        return idx
    return -1

  def write_result(self):
    #format = self.get_format("FBX binary")
    format = self.get_format("FBX ascii")

    new_scene = fbx.FbxScene.Create(self.sdk_manager, "result");
    self.create_dungeon(new_scene)

    exporter = fbx.FbxExporter.Create(self.sdk_manager, "")
    
    if exporter.Initialize("scenes/result2.fbx", format, self.io_settings):
      exporter.Export(new_scene)

    exporter.Destroy()

  def make_node(self, new_scene, node_name, pos, angle, id):
    #if dungeon_generator.check_for_overlapping(self,new_scene, pos, node_name):
        dest_node = fbx.FbxNode.Create( new_scene, node_name)
        dest_node.SetNodeAttribute(self.tile_meshes[node_name])
        dest_node.LclTranslation.Set(fbx.FbxDouble3(pos[0], pos[1], pos[2]))
        dest_node.LclRotation.Set(fbx.FbxDouble3(0, 0, angle))
        root = new_scene.GetRootNode()
        root.AddChild(dest_node)    

  def check_for_overlapping(self, scene, new_el_loc, node_name):
    if node_name.split('_')[2] == 'Stairs':
        a = 5    
    new_el_half_size = div3byconst(self.bb[node_name], 2)
    root_node = scene.GetRootNode()
    tiles = [root_node.GetChild(i) for i in range(root_node.GetChildCount())]
    #check overlapping for all nodes
    for node in tiles:
        old_el_loc = node.LclTranslation.Get()
        old_el_half_size = div3byconst(self.bb[node.GetName()], 2)
        diff = round3(abs3(sub3(new_el_loc, old_el_loc)))
        half_size = round3(add3(old_el_half_size, new_el_half_size))
        if less3(diff, half_size):
            return False
    return True

 

  def create_dungeon(self, new_scene):
      #self.corridor.create_corridor(new_scene)
      self.room.create_room(new_scene)



      ### Below this comment is old Andy's code
      ### For Jack -> Instead, here should be combination of module creation (corridors & rooms)
      ### For Luke -> You can test your code here, by changing line 255 to the call of your function




    
