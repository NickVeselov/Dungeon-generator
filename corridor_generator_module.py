import math
import random
import fbx

import dungeon_generator


class corridor_generator:

  def try_tile(self, new_scene, stack, edges, pos, angle, incoming, in_sel, id):
    in_feature_name, in_tile_name, in_trans, in_rot = incoming[in_sel]

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
        stack.append(edge)
      else:
        edge_pos, edge_angle, edge_feature_name, edge_satisfied = edges[dungeon_generator.xy_location(new_pos)]
        edges[dungeon_generator.xy_location(new_pos)] = (edge_pos, edge_angle, edge_feature_name, out_feature_name)

    dungeon_generator.dungeon_generator.make_node(self,new_scene, tile_name, tile_pos, new_angle,id)
    print("pass")
    return True 

  def create_corridor(self, new_scene):
    # clone the tile meshes and name them after their original nodes.
    tile_meshes = self.tile_meshes = {}
    # add each tile mesh to the mesh array
    for name in self.tiles:
      tile = self.tiles[name]
      tile_mesh = tile.GetNodeAttribute()
      tile_meshes[name] = tile_mesh.Clone(fbx.FbxObject.eDeepClone, None)
      tile_meshes[name].SetName(name)

    edges = {}
    pos = (0, 0, 0)
    angle = 0
    corridor_size = 100

    # create an unsatisfied edge
    stack = [(pos, angle, 'wide', False)]
    num_tiles = 0
    random.seed(1)

    # this loop processes one edge from the todo list.
    while len(stack) and num_tiles < corridor_size:
      pos, angle, out_feature_name, in_feature_name = stack.pop()
      
      print(dungeon_generator.xy_location(pos))

      for i in range(4):
        # incoming features are indexed on the feature name
        incoming = self.incoming[out_feature_name]
        #randomly pick one of the tiles
        in_sel = int(random.randrange(len(incoming)))

        if self.try_tile(new_scene, stack, edges, pos, angle, incoming, in_sel, num_tiles):
          break

      num_tiles += 1
