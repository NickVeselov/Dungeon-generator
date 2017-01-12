import math
import random
import fbx


class rooms_generator:

  def read_components(self):
    importer = fbx.FbxImporter.Create(self.sdk_manager, "")    

    result = importer.Initialize("scenes/components_v2.fbx", -1, self.io_settings)
    if not result:
      raise BaseException("could not find components file")
    
    #scene creation
    self.components = fbx.FbxScene.Create(self.sdk_manager, "")
    result = importer.Import(self.components)
    importer.Destroy()

    root = self.components.GetRootNode()
    top_level = [root.GetChild(i) for i in range(root.GetChildCount())]

    # child nodes matching this pattern are feature markup
    feature_pattern = re.compile('(\<|\>)([^.]+)(\..*)?')