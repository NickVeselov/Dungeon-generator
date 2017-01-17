import math
import random
import fbx

import dungeon_generator
from inspect import stack


class rooms_generator:


  lastRoom = False;

  def try_tile(self, new_scene, stack, edges, pos, angle, incoming, id):
    in_feature_name, in_tile_name, in_trans, in_rot = incoming
    # from the feature, set the position and rotation of the new tile
    new_angle = dungeon_generator.lim360(angle - in_rot[2])
    #new_angle = 360
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

 
    
  def check_neighbours(self, scene, new_el_loc, node_name):
    new_el_half_size = div3byconst(self.bb[node_name], 2)
    root_node = scene.GetRootNode()
    tiles = [root_node.GetChild(i) for i in range(root_node.GetChildCount())]
    #check overlapping for all nodes
    for node in tiles:
        old_el_loc = node.LclTranslation.Get()
        old_el_half_size = div3byconst(self.bb[node.GetName()], 2)
        diff = sub3(new_el_loc, old_el_loc)
        if (less3(abs3(diff), old_el_half_size + new_el_half_size)):
            return False
    return True    

  def create_room(self, new_scene):
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
    pos = (0, 0, 0)
    angle = 0
    no_of_rooms = 80

    # create an unsatisfied edge
    
   # if (lastRoom):
    stack = [(pos, pos, angle, 'bigroomflat', False)]
   # else :
   #   stack = [(pos, pos, angle, 'end', False)]
    num_tiles = 0
    random.seed(1)

    same_tile_spree = 0
    tile_spree_limit = 4

    previous_tile_name = False

    # this loop processes one edge from the todo list.
    while len(stack) and num_tiles < no_of_rooms:
      r = random.randrange(len(stack))
      edge_pos, tile_pos, angle, out_feature_name, in_feature_name = stack.pop(r)
      
      print(dungeon_generator.xy_location(pos))

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

        if self.try_tile(new_scene, stack, edges, edge_pos, angle, picked_tile, num_tiles):
          
          break

      num_tiles += 1

    
    #self.close_ends(new_scene, stack, 4, tile_categories, 2, edges)