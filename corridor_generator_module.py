import math
import random
import fbx

import dungeon_generator


class corridor_generator:

  def try_tile(self, new_scene, stack, edges, pos, angle, incoming, id, check_overlap):
    in_feature_name, in_tile_name, in_trans, in_rot = incoming

    # from the feature, set the position and rotation of the new tile
    new_angle = dungeon_generator.lim360(angle - in_rot[2])
    tile_pos = dungeon_generator.add3(pos, dungeon_generator.rotateZ(dungeon_generator.neg3(in_trans), new_angle))
    tile_name = in_tile_name
    print(tile_pos, new_angle, tile_name)

    # outgoing features are indexed on the tile name
    outgoing = self.outgoing[tile_name]

    # check existing edges to see if this tile fits.
    # although we know that one edge fits, we haven't checked the others.
    for out_sel in range(len(outgoing)):
      out_feature_name, out_tile_name, out_trans, out_rot = outgoing[out_sel]
      new_pos = dungeon_generator.add3(tile_pos, dungeon_generator.rotateZ(out_trans, new_angle))
      if dungeon_generator.xy_location(new_pos) in edges:
        edge_pos, edge_angle, edge_feature_name, edge_satisfied = edges[dungeon_generator.xy_location(new_pos)]
        print("check", new_pos, edge_pos, out_feature_name, edge_feature_name, edge_satisfied)
        if edge_satisfied:
          return False
        # check the height of the join.
        # note: we should also check that the incoming matches the outgoing.
        if abs(edge_pos[2] - new_pos[2]) > 0.01:
          print("fail")
          return False
    if check_overlap:
        if not dungeon_generator.dungeon_generator.check_for_overlapping(self, new_scene, tile_pos,tile_name):
            return False
    # add all outgoing edges to the todo list and mark edges
    # note: if there were multiple outgoing edge choices, we would have to select them.
    for out_sel in range(len(outgoing)):
      out_feature_name, out_tile_name, out_trans, out_rot = outgoing[out_sel]
      new_pos = dungeon_generator.add3(tile_pos, dungeon_generator.rotateZ(out_trans, new_angle))
      if not dungeon_generator.xy_location(new_pos) in edges:
        # make an unsatisfied edge
        edge = (new_pos, dungeon_generator.lim360(new_angle + out_rot[2]), out_feature_name, None)
        edges[dungeon_generator.xy_location(new_pos)] = edge
        stack.append((new_pos, tile_pos, dungeon_generator.lim360(new_angle + out_rot[2]), out_feature_name, None))
      else:
        edge_pos, edge_angle, edge_feature_name, edge_satisfied = edges[dungeon_generator.xy_location(new_pos)]
        edges[dungeon_generator.xy_location(new_pos)] = (edge_pos, edge_angle, edge_feature_name, out_feature_name)

    dungeon_generator.dungeon_generator.make_node(self,new_scene, tile_name, tile_pos, new_angle,id)
    print("pass")
    return True 

  def close_ends(self, scene, stack, distance, tile_categories, edges):
    root_node = scene.GetRootNode()
    tiles = [root_node.GetChild(i) for i in range(root_node.GetChildCount())]

    while len(stack) > 0:
        edge_pos, tile_pos, angle, out_feature_name, in_feature_name = stack.pop()
        tile = False
        tile_pos = dungeon_generator.round3(tile_pos)
        
        #find tile in the scene
        for node in tiles:            
            pos = dungeon_generator.round3(node.LclTranslation.Get())
            if (pos == tile_pos):
                tile = node
                break
        
        if tile:
            name = tile.GetName()
            category = tile_categories[name]

            search_finished = False
            self.open_edges = []
            self.closed_edges = []            

            while not search_finished:
                search_finished = True
                for cone in stack:
                    if dungeon_generator.round3(cone[1]) == tile_pos:
                        stack.remove(cone)
                        search_finished = False
                        break
            self.substitution_tile_name = False
                        
            self.characterize_ending(stack, edges, category, tile_pos, distance);            

            if self.pick_substitution(scene, edges, out_feature_name, category, name, edge_pos,angle, tile_pos, self.incoming[out_feature_name], distance):
                if self.substitution_tile_name:
                    self.outgoing
                    a = tile.GetNodeAttribute(); 
                    tile.SetNodeAttribute(self.tile_meshes[self.substitution_tile_name])
                    b = tile.GetNodeAttribute();
                    tile.LclRotation.Set(fbx.FbxDouble3(0, 0, self.substitution_tile_angle))
                    tile.SetName(self.substitution_tile_name)                
                    print("Tile substituted", self.closed_edges, self.substitution_tile_name,"->",name, tile_pos)  
                    
                    outgoing = self.outgoing[self.substitution_tile_name]
                    for out_sel in range(len(outgoing)):
                      out_feature_name, out_tile_name, out_trans, out_rot = outgoing[out_sel]
                      new_pos = dungeon_generator.add3(tile_pos, dungeon_generator.rotateZ(out_trans, self.substitution_tile_angle))
                      if not dungeon_generator.xy_location(new_pos) in edges:
                        # make an unsatisfied edge
                        edge = (new_pos, dungeon_generator.lim360(self.substitution_tile_angle + out_rot[2]), out_feature_name, None)
                        edges[dungeon_generator.xy_location(new_pos)] = edge
                        stack.append((new_pos, tile_pos, dungeon_generator.lim360(self.substitution_tile_angle + out_rot[2]), out_feature_name, None))
                      else:
                          if not (edges[dungeon_generator.xy_location(new_pos)][3]):
                            edge = (new_pos, dungeon_generator.lim360(self.substitution_tile_angle + out_rot[2]), out_feature_name, None)
                            edges[dungeon_generator.xy_location(new_pos)] = edge
                            stack.append((new_pos, tile_pos, dungeon_generator.lim360(self.substitution_tile_angle + out_rot[2]), out_feature_name, None))
                    
                                   
                elif not(self.free_space):
                    #place wall                    
                    wall = self.walls[self.continuation]

                    wall_angle = angle

                    if wall.GetChildCount() != 1:
                            print("Wall has incorrect children number:", wall)
                    else:
                        child = wall.GetChild(0)
                        connector_loc = child.LclTranslation.Get()
                        a = wall.LclTranslation.Get()
                        wall_pos = dungeon_generator.sub3(edge_pos, [0, 0, connector_loc[2]])
                                                          
                        new_node = fbx.FbxNode.Create(scene, self.continuation)
                        new_node.SetNodeAttribute(self.tile_meshes[self.continuation])
                        new_node.LclTranslation.Set(fbx.FbxDouble3(wall_pos[0], wall_pos[1], wall_pos[2]))
                        new_node.LclRotation.Set(fbx.FbxDouble3(0, 0, wall_angle))
                        root = scene.GetRootNode()
                        root.AddChild(new_node)  
                        print("Wall added. Tile name = ", name, " Tile pos =", dungeon_generator.round3(tile_pos),
                              " Wall pos = ",dungeon_generator.round3(edge_pos)," Angle =", wall_angle)
  
  def characterize_ending(self, stack, edges, category, tile_pos, distance):
            edges_number = 0
            ids = []
            id = dungeon_generator.xy_location(dungeon_generator.add3(tile_pos,[0, distance, 0]))
            if id in edges:
                ids.append(id)
                if edges[id][3] == None:
                    self.open_edges.append('top')
                else:
                    self.closed_edges.append('top')
            id = dungeon_generator.xy_location(dungeon_generator.add3(tile_pos,[0, -distance, 0]))
            if id in edges:
                ids.append(id)
                if edges[id][3] == None:
                    self.open_edges.append('bottom')
                else:
                    self.closed_edges.append('bottom')
            id = dungeon_generator.xy_location(dungeon_generator.add3(tile_pos,[distance, 0, 0]))
            if id in edges:
                ids.append(id)
                if edges[id][3] == None:
                    self.open_edges.append('right')
                else:
                    self.closed_edges.append('right')
            id = dungeon_generator.xy_location(dungeon_generator.add3(tile_pos,[-distance, 0, 0]))
            if id in edges:
                ids.append(id)
                if edges[id][3] == None:
                    self.open_edges.append('left')
                else:
                    self.closed_edges.append('left')            

  def pick_substitution(self, scene, edges, out_feature_name, category, name, connector_pos, connector_angle, tile_pos, incoming, distance):      
            self.substitution_tile_name = False
            self.substitution_tile_angle = False
            if category == '4way':
                if len(self.open_edges) == 1:
                    self.substitution_tile_name = 'corridor_3way_wide_01'
                    if 'top' in self.open_edges:
                        self.substitution_tile_angle = 270
                    elif 'right' in self.open_edges:
                        self.substitution_tile_angle = 180
                    elif 'bottom' in self.open_edges:
                        self.substitution_tile_angle = 90
                    else:
                        self.substitution_tile_angle = 0
                elif len(self.open_edges) == 2:
                    if 'top' in self.closed_edges and 'bottom' in self.closed_edges:
                        self.substitution_tile_name = 'corridor_1way_wide_01'
                        self.substitution_tile_angle = 0
                    elif 'left' in self.closed_edges and 'right' in self.closed_edges:
                        self.substitution_tile_name = 'corridor_1way_wide_01'
                        self.substitution_tile_angle = 90
                    else:
                        if 'left' in self.closed_edges and 'top' in self.closed_edges:
                            self.substitution_tile_angle = 180
                        if 'right' in self.closed_edges and 'bottom' in self.closed_edges:
                            self.substitution_tile_angle = 0
                        if 'right' in self.closed_edges and 'top' in self.closed_edges:
                            self.substitution_tile_angle = 90
                        if 'bottom' in self.closed_edges and 'left' in self.closed_edges:
                            self.substitution_tile_angle = 270
                        self.substitution_tile_name = 'corridor_2way_wide_01'
                elif len(self.open_edges) == 3:
                    self.substitution_tile_name = 'corridor_1way_wide_01'
                    if 'top' in self.closed_edges or 'bottom' in self.closed_edges:
                        self.substitution_tile_angle = 0
                    else:
                        self.substitution_tile_angle = 90
            elif category == '3way':
                if len(self.open_edges) == 1 and len(self.closed_edges) == 2:
                    if 'top' in self.closed_edges and 'bottom' in self.closed_edges:
                        self.substitution_tile_name = 'corridor_1way_wide_01'
                        self.substitution_tile_angle = 0
                    elif 'left' in self.closed_edges and 'right' in self.closed_edges:
                        self.substitution_tile_name = 'corridor_1way_wide_01'
                        self.substitution_tile_angle = 90
                    else:
                        self.substitution_tile_name = 'corridor_2way_wide_01'
                        if 'top' in self.closed_edges and 'right' in self.closed_edges:
                            self.substitution_tile_angle = 90
                        elif 'right' in self.closed_edges and 'bottom' in self.closed_edges:
                            self.substitution_tile_angle = 0
                        elif 'bottom' in self.closed_edges and 'left' in self.closed_edges:
                            self.substitution_tile_angle = 270
                        else:
                            self.substitution_tile_angle = 180
                elif len(self.closed_edges) == 1:
                    if len(self.open_edges) == 2:
                        self.substitution_tile_name = 'corridor_2way_wide_01'
                        if 'top' not in self.open_edges and 'right' not in self.open_edges:
                            self.substitution_tile_angle = 90
                        elif 'right' not in self.open_edges and 'bottom' not in self.open_edges:
                            self.substitution_tile_angle = 0
                        elif 'bottom' not in self.open_edges and 'left' not in self.open_edges:
                            self.substitution_tile_angle = 270
                        else:
                            self.substitution_tile_angle = 180
                    else:
                        self.substitution_tile_name = 'corridor_1way_wide_01'
                        if 'top' in self.closed_edges or 'bottom' in self.closed_edges:
                            self.substitution_tile_angle = 0
                        else:
                            self.substitution_tile_angle = 90
            else:         
                if (len(self.closed_edges) == 2):
                    return False
                if 'narrow' in name.split('_'):
                    width = 'narrow'
                elif 'wide' in name.split('_'):
                    width = 'wide' 
                else:
                    return False  
                corridor_name = 'corridor_1way_'+width+'_01'
                stack = []
                
                incoming = (width, corridor_name, dungeon_generator.sub3(tile_pos,connector_pos), [0, 0, connector_angle]) 
                if self.try_tile(scene, stack, edges, connector_pos, connector_angle, incoming, id, True):
                    self.room_connectors.append((stack.pop()))
                self.free_space = False
                self.continuation = 'corridor_wall_' + width
                return True
            if not(self.substitution_tile_name):
                return False
            return True             
        
  def create_corridor(self, new_scene, corridor_size, pos, tile_pos, angle, outgoing_connection, incoming_connection):
    # clone the tile meshes and name them after their original nodes.
    tile_meshes = self.tile_meshes = {}
    tile_weights = {}
    tile_categories = {}
    # add each tile mesh to the mesh array
    for name in self.tiles:
      tile = self.tiles[name]    
      tile_mesh = tile.GetNodeAttribute()
      tile_meshes[name] = tile_mesh.Clone(fbx.FbxObject.eDeepClone, None)
      tile_meshes[name].SetName(name)
      tile_weights[name] = 1
      category = name.split('_')[1]
      tile_categories[name] = category

    edges = {}
    self.room_connectors = []
    # create an unsatisfied edge
    stack = [(pos, tile_pos, angle, outgoing_connection, incoming_connection)]
    open_edges_deleted_from_stack = []
    num_tiles = 0
    random.seed(1)

    same_tile_spree = 0
    tile_spree_limit = 4

    previous_tile_name = False

    # this loop processes one edge from the todo list.
    while len(stack) and num_tiles < corridor_size:

      r = random.randrange(len(stack))
      edge_pos, tile_pos, angle, out_feature_name, in_feature_name = stack.pop()#r)
      
      print(dungeon_generator.xy_location(pos))
      element_placed = False

      for i in range(4):
        # incoming features are indexed on the feature name
        
        #randomly pick one of the tiles, based on weights
        incoming = self.incoming[out_feature_name]
        sum = 0
        for tile_name in incoming:
            sum += tile_weights[tile_name[1]]
        r = random.randrange(100*sum)

        for tile_name in incoming:
            if 100*tile_weights[tile_name[1]] > r:
                picked_tile = tile_name
                break
            else:
                r -= 100*tile_weights[tile_name[1]]

        picked_tile_name = picked_tile[1]
        
        #check if this tile category is the same as previous
        cat = tile_categories[picked_tile_name]
        if previous_tile_name:
            if tile_categories[previous_tile_name] == cat:
                ++same_tile_spree

        #alternate weights of the tiles
        if (cat == '1way' or cat == '2way') and previous_tile_name:
            if (tile_categories[previous_tile_name] == cat) and (same_tile_spree < tile_spree_limit):
                tile_weights[picked_tile_name] = 9
                ++same_tile_spree
            else:
                tile_weights[picked_tile_name] = 0
        else:
            tile_weights[picked_tile_name] = 0
        
        previous_tile_name = picked_tile_name
                    
        #increment weights of all tiles
        for tile_name in tile_weights:
            tile_weights[tile_name] += 1

        if self.try_tile(new_scene, stack, edges, edge_pos, angle, picked_tile, num_tiles, True):
          element_placed = True        
          break

      if not element_placed:
         open_edges_deleted_from_stack.append((edge_pos, tile_pos, angle, out_feature_name, in_feature_name))

      num_tiles += 1
    while len(open_edges_deleted_from_stack) > 0:
        stack.append(open_edges_deleted_from_stack.pop())
    self.close_ends(new_scene, stack, 4, tile_categories, edges, )
        
    stack = []
    for connector in self.room_connectors:
        connector_pos, tile_pos, tile_angle, inc, outg = connector
        wide_tiles = self.door_incoming[inc]
        if 'room' in wide_tiles[0][1]:
            incoming = self.door_incoming[inc][0]
        else:
            incoming = self.door_incoming[inc][1]        
        self.try_tile(new_scene, stack, edges, connector_pos, tile_angle, incoming, 0, False)
    rooms_stack = []
    for connector in stack:
        connector_pos, tile_pos, tile_angle, inc, outg = connector
        incoming = self.rooms_incoming[inc][0]      
        self.try_tile(new_scene, rooms_stack, edges, connector_pos, tile_angle, incoming, 0, True)

    for connector in rooms_stack:
        connector_pos, tile_pos, tile_angle, inc, outg = connector   
        wall_name = 'room_wall_'+inc          
        wall = self.walls[wall_name]
        if wall.GetChildCount() != 1:
            print("Wall has incorrect children number:", wall)
        else:
            child = wall.GetChild(0)
            wall_connector_loc = child.LclTranslation.Get()
            wall_pos = dungeon_generator.sub3(connector_pos, [0, 0, wall_connector_loc[2]])
                                                          
            new_node = fbx.FbxNode.Create(new_scene, wall_name)
            new_node.SetNodeAttribute(self.tile_meshes[wall_name])
            new_node.LclTranslation.Set(fbx.FbxDouble3(wall_pos[0], wall_pos[1], wall_pos[2]))
            new_node.LclRotation.Set(fbx.FbxDouble3(0, 0, tile_angle))
            root = new_scene.GetRootNode()
            root.AddChild(new_node)  
            print("Wall added. Tile name = ", name, " Tile pos =", dungeon_generator.round3(tile_pos),
                " Wall pos = ",dungeon_generator.round3(connector_pos)," Angle =", tile_angle)