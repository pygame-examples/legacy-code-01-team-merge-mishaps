from typing import Iterator
from queue import Queue
from enum import Enum

import pygame

from ..interfaces import SpriteInitData, PhysicsType, SpritePhysicsData, SpriteInterface, Direction, PhysicsSpriteInterface
from ..const import GRAVITY
from .sprite import Sprite
from ..const import MAX_SPEED

def is_aligned_with_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    if direction in {Direction.NORTH, Direction.SOUTH}:
        return collision_rect.left > portal_rect.left and collision_rect.right < portal_rect.right
    return collision_rect.top > portal_rect.top and collision_rect.bottom < portal_rect.bottom

def is_inside_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    if not collision_rect.colliderect(portal_rect):
        return False
    return is_aligned_with_portal(collision_rect, portal_rect, direction)

def is_through_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    if not is_aligned_with_portal(collision_rect, portal_rect, direction):
        return False
    if direction == Direction.NORTH:
        return collision_rect.top >= portal_rect.bottom - 1
    if direction == Direction.SOUTH:
        return collision_rect.bottom <= portal_rect.top + 1
    if direction == Direction.EAST:
        return collision_rect.right <= portal_rect.left + 1
    if direction == Direction.WEST:
        return collision_rect.left >= portal_rect.right - 1
    
def is_entering_portal(direction: Direction, velocity: pygame.Vector2) -> bool:
    if direction == Direction.NORTH:
        return velocity.y > 0
    if direction == Direction.SOUTH:
        return velocity.y < 0
    if direction == Direction.EAST:
        return velocity.x < 0
    if direction == Direction.WEST:
        return velocity.x > 0

def clip_rect_to_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    collision_rect = collision_rect.copy()
    if direction == Direction.NORTH:
        # only show rect above top
        overlap = min(abs(collision_rect.bottom - portal_rect.top), collision_rect.height)
        collision_rect.height -= overlap
    if direction == Direction.SOUTH:
        # only show rect below bottom
        overlap = min(abs(collision_rect.top - portal_rect.bottom), collision_rect.height)
        collision_rect.top += overlap
        collision_rect.height -= overlap
    if direction == Direction.EAST:
        # only show rect right of right
        overlap = min(abs(collision_rect.left - portal_rect.right), collision_rect.width)
        collision_rect.width -= overlap
        collision_rect.left += overlap
    if direction == Direction.WEST:
        # only show rect left of left
        overlap = min(abs(collision_rect.right - portal_rect.left), collision_rect.width)
        collision_rect.width -= overlap
    return collision_rect

def get_axis_of_direction(direction: Direction):
    return int(direction in {Direction.NORTH, Direction.SOUTH})

class PhysicsSprite(Sprite, PhysicsSpriteInterface):
    class PortalState(Enum):
        """Local-Use enum.  Cool."""
        ENTER = 1
        EXIT = 2
        OUT = 3

    def __init__(self, data: SpriteInitData, physics_data: SpritePhysicsData):
        super().__init__(data)
        self.physics_type: PhysicsType = physics_data.physics_type
        self.velocity: pygame.Vector2 = pygame.Vector2()
        self.acceleration: pygame.Vector2 = pygame.Vector2(GRAVITY)
        self.horizontal_speed: float = physics_data.horizontal_speed
        self.weight: float = physics_data.weight
        self.jump_speed: float = physics_data.jump_speed
        self.duck_speed: float = physics_data.duck_speed
        self.orientation: Direction = physics_data.orientation
        self.tunnel_id: str = physics_data.tunnel_id
        self.on_ground: bool = False
        self.one_way: bool = physics_data.one_way
        self.ducking: bool = False

        self.missed: pygame.Vector2 = pygame.Vector2()
        self.missed_accel: pygame.Vector2 = pygame.Vector2()

        self.just_went: dict[str, bool] = {
            "jump": False,
            "left": False,
            "right": False,
            "duck": False,
        }
        self.just_went_buffer: dict[str, bool] = {
            "jump": False,
            "left": False,
            "right": False,
            "duck": False,
        }

        self.full_clip_rect: pygame.Rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        self.current_portal: PhysicsSpriteInterface | None = None
        self.twin_portal: PhysicsSpriteInterface | None = None
        self.portal_state: PhysicsSprite.PortalState = self.PortalState.OUT

    @property
    def collision_rect(self):
        return self.rect.copy()
    
    @property
    def clip_rect(self):
        clipped = self.full_clip_rect.copy()
        if self.portal_state == self.PortalState.ENTER:
            clipped = clip_rect_to_portal(self.rect, self.current_portal.rect, self.current_portal.orientation)
            clipped.center -= pygame.Vector2(self.rect.topleft)
        elif self.portal_state == self.PortalState.EXIT:
            clipped = clip_rect_to_portal(self.rect, self.twin_portal.rect, self.twin_portal.orientation)
            clipped.center -= pygame.Vector2(self.rect.topleft)
        clipped.center -= self.rect.center
        return clipped
    
    @property
    def engaged_portal(self):
        if self.portal_state == self.PortalState.ENTER:
            return self.current_portal
        if self.portal_state == self.PortalState.ENTER:
            return self.twin_portal
        return None
        
    def trigger(self, other: SpriteInterface) -> None:
        pass

    def left(self, lost_time: float) -> None:
        self.velocity.x = -self.horizontal_speed
        if not self.just_went["left"]:
            self.missed += pygame.Vector2(-self.horizontal_speed, 0) * lost_time
        self.just_went_buffer["left"] = True

    def right(self, lost_time: float) -> None:
        self.velocity.x = self.horizontal_speed
        if not self.just_went["right"]:
            self.missed += pygame.Vector2(self.horizontal_speed, 0) * lost_time
        self.just_went_buffer["right"] = True

    def jump(self, lost_time: float) -> None:
        if self.on_ground:
            self.velocity.y = -self.jump_speed
        # TODO: use lost_time to approximate jump position and velocity

    def duck(self, lost_time: float) -> None:
        # TODO: use lost_time to approxmiate jump position and velocity
        self.ducking = True
        if not self.on_ground:
            self.velocity.y = max(self.duck_speed, self.velocity.y)

    def interpolated_pos(self, dt_since_physics: float) -> pygame.Vector2:
        return self.pos + self.velocity * dt_since_physics
    
    def interpolated_cliprect(self, dt_since_physics: float) -> pygame.FRect:
        clipped = self.full_clip_rect
        collision_rect = self.rect.copy()
        collision_rect.center = self.interpolated_pos(dt_since_physics)
        if self.portal_state == self.PortalState.ENTER:
            clipped = clip_rect_to_portal(collision_rect, self.current_portal.rect, self.current_portal.orientation)
            clipped.center -= pygame.Vector2(collision_rect.topleft)
        elif self.portal_state == self.PortalState.EXIT:
            clipped = clip_rect_to_portal(collision_rect, self.twin_portal.rect, self.twin_portal.orientation)
            clipped.center -= pygame.Vector2(collision_rect.topleft)
        return clipped
    
    def clipped_collision_rect(self):
        collision_rect = self.collision_rect.copy()
        for portal in self.level.get_group("portal-physics"):
            if is_inside_portal(collision_rect, portal.collision_rect, portal.orientation):
                collision_rect = clip_rect_to_portal(collision_rect, portal.collision_rect, portal.orientation)
        return collision_rect
    
    def handle_dynamic_collision_inside_portal(self, axis: int, dt: float) -> bool:
        if is_through_portal(self.collision_rect, self.current_portal.collision_rect, self.current_portal.orientation):
            self.exit_portal()
            return True
        elif self.portal_state == self.PortalState.EXIT and is_entering_portal(self.twin_portal.orientation, self.velocity):
            self.enter_portal(self.twin_portal, self.current_portal)
            return True
        elif (not is_inside_portal(self.collision_rect, self.current_portal.collision_rect, self.current_portal.orientation) and not 
                is_inside_portal(self.collision_rect, self.twin_portal.collision_rect, self.twin_portal.orientation)):
            self.abort_portal()
            return False

        return False
    
    def handle_dynamic_collision(self, axis: int, dt: float) -> bool: 
        def must_move():
            collision_rect = self.clipped_collision_rect()
            for sprite in self.level.get_group("static-physics"):
                if sprite.one_way and (self.velocity.y < 0 or self.ducking):
                    continue
                if sprite.collision_rect.colliderect(collision_rect):
                    return True
            return False
        
        if self.current_portal:
            self.handle_dynamic_collision_inside_portal(axis, dt)

        self.velocity.clamp_magnitude_ip(MAX_SPEED)

        self.velocity[axis] += self.acceleration[axis] * dt
        center = pygame.Vector2(self.rect.center)
        center[axis] += self.velocity[axis] * dt + self.missed[axis]
        self.missed[axis] = 0
        self.rect.center = center

        offset: int = 1
        if self.velocity[axis] > 0:
            offset = -1
        
        moved: bool = False
        while must_move():
            self.rect[axis] += offset
            if (self.engaged_portal is not None and get_axis_of_direction(self.engaged_portal.orientation) == axis):
                moved = False
            else:
                self.velocity[axis] = 0
                moved = True

        if moved:
            self.rect.center = pygame.Rect(self.rect).center

        return moved

    def handle_trigger_collision(self) -> None:
        for sprite in self.level.get_group("triggerable").sprites():
            if sprite.rect.collision_rect.colliderect(self.collision_rect):
                sprite.trigger(self)

    def handle_portal_collision(self) -> None:
        for sprite in self.level.get_group("dynamic-physics"):
            if sprite.portal_state == self.PortalState.OUT and is_inside_portal(sprite.collision_rect, self.collision_rect, self.orientation) and is_entering_portal(self.orientation, sprite.velocity):
                for portal in self.level.get_group(self.tunnel_id):
                    if portal is not self:
                        sprite.enter_portal(self, portal)

    def enter_portal(self, portal: PhysicsSpriteInterface, twin: PhysicsSpriteInterface):
        self.current_portal = portal
        self.twin_portal = twin
        self.portal_state = self.PortalState.ENTER
        
    def exit_portal(self):
        if self.twin_portal.orientation == Direction.NORTH:
            self.velocity = pygame.Vector2(0, -self.velocity.length())
            self.rect.top = self.twin_portal.rect.bottom - 1
            self.rect.left = self.twin_portal.rect.left + self.rect.left - self.current_portal.rect.left
        if self.twin_portal.orientation == Direction.SOUTH:
            self.velocity = pygame.Vector2(0, self.velocity.length())
            self.rect.bottom = self.twin_portal.rect.top + 1
            self.rect.left = self.twin_portal.rect.left + self.rect.left - self.current_portal.rect.left
        if self.twin_portal.orientation == Direction.EAST:
            self.velocity = pygame.Vector2(-self.velocity.length(), 0)
            self.rect.right = self.twin_portal.rect.left + 1
            self.rect.top = self.twin_portal.rect.top + self.rect.top - self.current_portal.rect.top
        if self.twin_portal.orientation == Direction.WEST:
            self.velocity = pygame.Vector2(self.velocity.length(), 0)
            self.rect.left = self.twin_portal.rect.right - 1
            self.rect.top = self.twin_portal.rect.top + self.rect.top - self.current_portal.rect.top
        self.portal_state = self.PortalState.EXIT

    def abort_portal(self):
        self.current_portal = None
        self.twin_portal = None
        self.portal_state = self.PortalState.OUT

    def handle_commands(self) -> None:
        self.velocity.x = 0
        self.just_went_buffer = {
            "left": False,
            "right": False,
            "jump": False,
            "duck": False
        }
        for command in self.controller.get_commands():
            name: str = command.command
            if name == "left":
                self.left((pygame.time.get_ticks() - command.timestamp) / 1000)
            if name == "right":
                self.right((pygame.time.get_ticks() - command.timestamp) / 1000)
            if name == "jump":
                self.jump((pygame.time.get_ticks() - command.timestamp) / 1000)
            if name == "duck":
                self.duck((pygame.time.get_ticks() - command.timestamp) / 1000)

        self.just_went = self.just_went_buffer

    def update_physics(self, dt) -> None:
        self.handle_commands()
        if self.physics_type == PhysicsType.DYNAMIC:
            self.on_ground = False
            falling = self.velocity.y > 0 and not self.current_portal
            self.handle_dynamic_collision(0, dt)
            moved = self.handle_dynamic_collision(1, dt)
            if falling and moved:
                self.on_ground = True
                self.ducking = False
        if self.physics_type == PhysicsType.TRIGGER:
            self.handle_trigger_collision()
        if self.physics_type == PhysicsType.PORTAL:
            self.handle_portal_collision()

    def draw(self, surface: pygame.Surface, dt_since_physics: float) -> None:
        new_rect: pygame.FRect = self.rect.copy()
        clip_rect = self.interpolated_cliprect(dt_since_physics)
        new_rect.center = self.interpolated_pos(dt_since_physics) + pygame.Vector2(clip_rect.topleft)
        surface.blit(self.image.subsurface(clip_rect), new_rect)

        
