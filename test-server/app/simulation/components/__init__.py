from .base import (
    PhysicsComponent,
    VitalityComponent,
    SocialComponent,
    ReproductionComponent
)
from .behaviors import (
    HuntingComponent,
)
from .diet import (
    HerbivoreComponent,
    CarnivoreComponent,
    OmnivoreComponent
)

__all__ = [
    "PhysicsComponent",
    "VitalityComponent",
    "SocialComponent",
    "ReproductionComponent",
    "HuntingComponent",
    "HerbivoreComponent",
    "CarnivoreComponent",
    "OmnivoreComponent",
]
