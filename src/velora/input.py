from .domain import MovementIntent
class InputController:
    """Platform-neutral intent sink; OS-specific input implementation stays isolated here."""
    def __init__(self):self.last=MovementIntent()
    def apply(self,intent:MovementIntent)->None:self.last=intent
    def release_all(self)->None:self.last=MovementIntent()
