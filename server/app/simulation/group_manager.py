# server/app/simulation/group_manager.py
import uuid
import random
from typing import List, Optional, Set

from app.models.simulation import (
    SimulationState, Particle, ParticleGroup
)

class GroupManager:
    def __init__(self, state: SimulationState):
        self.state = state

    def create_group(self, members: List[Particle], parent_ids: Optional[Set[str]] = None, child_id: Optional[str] = None) -> str:
        """Create a new group with the given members"""
        if len(members) < 2:
            return None

        group_id = str(uuid.uuid4())
        member_ids = {member.id for member in members}
        species_id = members[0].speciesId

        self.state.groups[group_id] = ParticleGroup(
            id=group_id,
            memberIds=member_ids,
            speciesId=species_id,
            parentIds=parent_ids if parent_ids is not None else set(),
            childId=child_id
        )

        # Update member particles with group ID
        for member in members:
            member.attributes.groupId = group_id
            member.attributes.meetingCount = {}

        return group_id

    def leave_group(self, particle: Particle, group_id: str):
        """Remove a particle from its group"""
        if group_id not in self.state.groups:
            return

        group = self.state.groups[group_id]
        
        # Remove particle from group
        if particle.id in group.memberIds:
            group.memberIds.remove(particle.id)
        
        # Clear particle's group reference
        particle.attributes.groupId = None
        particle.attributes.timeInGroup = 0
        particle.attributes.meetingCount = {}
        
        # Remove empty or single-member groups
        if len(group.memberIds) < 2:
            for member_id in group.memberIds:
                if member_id in self.state.particles:
                    self.state.particles[member_id].attributes.groupId = None
                    self.state.particles[member_id].attributes.timeInGroup = 0
                    self.state.particles[member_id].attributes.meetingCount = {}
            del self.state.groups[group_id]

    def merge_groups(self, group1_id: str, group2_id: str):
        """Merge two groups if they are compatible"""
        if group1_id not in self.state.groups or group2_id not in self.state.groups:
            return

        group1 = self.state.groups[group1_id]
        group2 = self.state.groups[group2_id]

        if group1.speciesId != group2.speciesId:
            return

        new_members = group1.memberIds.union(group2.memberIds)
        parent_ids = (group1.parentIds or set()).union(group2.parentIds or set())
        child_ids = set()
        if group1.childId:
            child_ids.add(group1.childId)
        if group2.childId:
            child_ids.add(group2.childId)

        new_group_id = str(uuid.uuid4())
        self.state.groups[new_group_id] = ParticleGroup(
            id=new_group_id,
            memberIds=new_members,
            speciesId=group1.speciesId,
            parentIds=parent_ids,
            childId=list(child_ids)[0] if child_ids else None
        )

        # Update member references
        for member_id in new_members:
            if member_id in self.state.particles:
                self.state.particles[member_id].attributes.groupId = new_group_id

        # Remove old groups
        del self.state.groups[group1_id]
        del self.state.groups[group2_id]

    def update_groups(self):
        """Update particle groups"""
        groups_to_remove = set()
        
        for group_id, group in list(self.state.groups.items()):
            valid_members = set()
            
            for member_id in list(group.memberIds):
                if member_id not in self.state.particles:
                    continue
                    
                particle = self.state.particles[member_id]
                particle.attributes.timeInGroup += 1
                particle.attributes.energy = min(100, particle.attributes.energy + 0.1)
                
                should_leave = self._should_leave_group(particle, group)
                
                if should_leave:
                    self.leave_group(particle, group_id)
                else:
                    valid_members.add(member_id)
            
            group.memberIds = valid_members
            
            if len(group.memberIds) < 2:
                groups_to_remove.add(group_id)
                for member_id in group.memberIds:
                    if member_id in self.state.particles:
                        self.state.particles[member_id].attributes.groupId = None
        
        for group_id in groups_to_remove:
            if group_id in self.state.groups:
                del self.state.groups[group_id]

    def _should_leave_group(self, particle: Particle, group: ParticleGroup) -> bool:
        """Determine if a particle should leave its group"""
        # Leave if energy is high enough and not a child
        if particle.attributes.energy >= 70 and not particle.attributes.isChild:
            return True
        
        # Random chance to leave based on pack mentality
        if random.random() > particle.attributes.packMentality:
            return True
        
        # Children leave when they're old enough
        if (particle.attributes.isChild and 
            particle.attributes.age > 100 and 
            particle.id == group.childId):
            particle.attributes.isChild = False  # Update child status
            return True
        
        return False