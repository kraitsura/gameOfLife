from enum import Enum
from typing import NewType

EntityId = NewType('EntityId', str)
SpeciesId = NewType('SpeciesId', str)
PackId = NewType('PackId', str)

class EntityType(str, Enum):
    CREATURE = "creature"
    PLANT = "plant"
    OBSTACLE = "obstacle"

class Trait(str, Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"
    SELF_REPLICATING = "self_replicating"
    TWO_PARENTS = "two_parents"

