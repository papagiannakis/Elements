import Elements.extensions.SkinnedAnimation.SkinnedAnimation
from Elements.extensions.SkinnedAnimation.SkinnedAnimation import AnimationComponents
import Elements.pyECSS.System
from Elements.pyECSS.System import System

class SkinnedAnimationSystem(System):
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)

    def apply2AnimationComponents(self, animationComponents: Elements.extensions.SkinnedAnimation.SkinnedAnimation.AnimationComponents):

        # if (isinstance(animationComponents, Elements.features.SkinnedAnimation.SkinnedAnimation.AnimationComponents)) == False:
        #     return #in Python due to duck typing we need to check this!
        #print(self.getClassName(), ": apply2AnimationComponents called")

        animation_data = animationComponents.animation_loop()
        
        return animation_data