from typing import Dict, Optional
from app.simulation.core.interfaces import Component
from app.simulation.models import Entity
from app.simulation.core.context import SimulationContext

class SocialComponent(Component):
    def __init__(self, pack_mentality: float = 0.5):
        self.pack_mentality = pack_mentality
        self.group_id: Optional[str] = None
        self.meeting_history: Dict[str, int] = {}
        self.time_in_group = 0
        self.leadership_score = 0.0
        self.relationships: Dict[str, float] = {}

    def update(self, owner: 'Entity', context: 'SimulationContext', dt: float) -> None:
        if self.group_id:
            self.time_in_group += 1
            
            # Update relationships with group members
            group = context.world.get_group(self.group_id)
            if group:
                for member_id in group.members:
                    if member_id != owner.id:
                        self.relationships[member_id] = min(
                            1.0, 
                            self.relationships.get(member_id, 0) + 0.01 * dt
                        )
