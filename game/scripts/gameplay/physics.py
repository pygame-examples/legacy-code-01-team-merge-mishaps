from typing import Iterator, Callable
from queue import Queue
from enum import Enum

import pygame

from ..interfaces import SpriteInitData, PhysicsType, SpritePhysicsData, SpriteInterface, Direction, PhysicsSpriteInterface
from ..const import GRAVITY
from .sprite import Sprite
from ..const import MAX_SPEED

def is_aligned_with_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    """Returns if a rect is aligned with the portal in its axis"""
    if direction in {Direction.NORTH, Direction.SOUTH}:
        return collision_rect.left > portal_rect.left and collision_rect.right < portal_rect.right
    return collision_rect.top > portal_rect.top and collision_rect.bottom < portal_rect.bottom

def is_inside_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    """Returns if a rect is inside a portal"""
    if not collision_rect.colliderect(portal_rect):
        return False
    return is_aligned_with_portal(collision_rect, portal_rect, direction)

def is_through_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> bool:
    """Returns if a rect is aligned and behind the back of a portal"""
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
    """Returns if a velocity is in a direction that would enter a portal with the given direction"""
    if direction == Direction.NORTH:
        return velocity.y > 0
    if direction == Direction.SOUTH:
        return velocity.y < 0
    if direction == Direction.EAST:
        return velocity.x < 0
    if direction == Direction.WEST:
        return velocity.x > 0

def clip_rect_to_portal(collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction) -> pygame.FRect:
    """Clips a rect to only what you would see if the rect entered a portal"""
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

def get_axis_of_direction(direction: Direction) -> int:
    """Returns integer axis of a direction (0 for x, 1 for y)"""
    return int(direction in {Direction.NORTH, Direction.SOUTH})


class PhysicsSprite(Sprite, PhysicsSpriteInterface):
    class PortalState(Enum):
        """State of sprite regarding portals"""
        ENTER = 1  # entering a portal
        EXIT = 2  # exiting a portal
        OUT = 3  # not touching or within a portal

    def __init__(self, data: SpriteInitData, physics_data: SpritePhysicsData):
        super().__init__(data)
        self.physics_type: PhysicsType = physics_data.physics_type
        self.velocity: pygame.Vector2 = pygame.Vector2()  # pixels/second
        self.acceleration: pygame.Vector2 = pygame.Vector2(GRAVITY)  # pixels/second squared (I think)
        self.flight_speed: float = physics_data.flight_speed  # how fast the sprite flies when thrown (if dynamic)
        self.horizontal_speed: float = physics_data.horizontal_speed  # how fast the sprite walks right and left (if dynamic)
        self.friction: float = physics_data.friction # how quickly the sprite slows down (if dynamic)
        self.weight: float = physics_data.weight  # unused atm
        self.jump_speed: float = physics_data.jump_speed  # initial jump velocity (if dynamic)
        self.duck_speed: float = physics_data.duck_speed  # initial downward duck velocity (if dynamic)
        self.orientation: Direction = physics_data.orientation  # orientation (if portal)
        self.tunnel_id: str = physics_data.tunnel_id  # used to get twin portal (if portal)
        self.on_ground: bool = False  # whether sprite is touching ground (if dynamic)
        self.one_way: bool = physics_data.one_way  # whether sprite only collides downward (if static)
        self.ducking: bool = False  # whether sprite is ducking (if dynamic)
        self.facing: pygame.Vector2 = pygame.Vector2(1, 0) # the direction the sprite should be facing

        self.min_distance: int = 40 # minimum ditance to pick up something
        self.current_throwable: PhysicsSprite = None # the current think you're about to throw at someone
        self.picker_upper: PhysicsSprite = None # the one picking up self
        self.was_thrown: bool = False # bool for when the sprite is thrown (duuuuuuuuh)

        # latency compensation 
        # all inputs are polled faster than physics framerate and timestamped
        # then the physics engine can use that timestamp to correct for time difference
        # eg move the player just a wee bit more if he hit the left key a millisecond after the last frame
        self.missed: pygame.Vector2 = pygame.Vector2()  # missed motion that needs to be caught up with (if dynamic)
        self.missed_accel: pygame.Vector2 = pygame.Vector2()  # missed acceleration that needs to be caught up with (if dynamic)

        # which commands were called last frame (if dynamic)
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

        # portal handling
        self.current_portal: PhysicsSpriteInterface | None = None  # which portal I am entering
        self.twin_portal: PhysicsSpriteInterface | None = None  # which portal I am exiting
        self.portal_state: PhysicsSprite.PortalState = self.PortalState.OUT  # what portal state I am in

    @property
    def collision_rect(self):
        """
        Rect used for collision detection.

        NOT interpolated, do NOT use without interpolation in render or draw code
        """
        return self.rect.copy()
    
    @property
    def full_clip_rect(self):
        """
        Rect used if drawing entire sprite.
        
        NOT interpolated, do NOT use without interpolation in render or draw code
        """
        return self.image.get_rect()
    
    @property
    def clip_rect(self):
        """
        Rect amount actually drawn.
        
        NOT interpolated, do NOT use without interpolation in render or draw code
        """
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
        """Which portal sprite is currently "inside" (entering or exiting) or None"""
        if self.portal_state == self.PortalState.ENTER:
            return self.current_portal
        if self.portal_state == self.PortalState.EXIT:
            return self.twin_portal
        # I'm assuming it was supposed to be PortalState.Exit in the second if statement and not PortalState.Enter??? - Aiden
        return None
        
    def trigger(self, other: SpriteInterface) -> None:
        """
        Called when this sprite touches a Trigger physics object and is part of its trigger group.
        
        Other is the sprite that triggered me.  Called every frame I am touching it.
        """
        pass

    def left(self, lost_time: float) -> None:
        """If I am dynamic, try to move left until the next frame"""
        self.velocity.x = -self.horizontal_speed
        if not self.just_went["left"]:
            self.missed += pygame.Vector2(-self.horizontal_speed, 0) * lost_time
        self.just_went_buffer["left"] = True

    def right(self, lost_time: float) -> None:
        """If I am dynamic, try to move right until the next frame"""
        self.velocity.x = self.horizontal_speed
        if not self.just_went["right"]:
            self.missed += pygame.Vector2(self.horizontal_speed, 0) * lost_time
        self.just_went_buffer["right"] = True

    def jump(self, lost_time: float) -> None:
        """If I am dynamic, try to jump"""
        if self.on_ground:
            self.velocity.y = -self.jump_speed
        # TODO: use lost_time to approximate jump position and velocity

    def duck(self, lost_time: float) -> None:
        """If I am dynamic, try to duck until the next frame"""
        # TODO: use lost_time to approxmiate jump position and velocity
        self.ducking = True
        if not self.on_ground:
            self.velocity.y = max(self.duck_speed, self.velocity.y)

    def interpolated_pos(self, dt_since_physics: float) -> pygame.Vector2:
        """Use this position during render calls"""
        return self.pos + self.velocity * dt_since_physics

    def interpolated_cliprect(self, dt_since_physics: float) -> pygame.FRect:
        """Use this clip rect during render calls"""
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
        """
        Collision rect used in actual collision checking.
        
        Areas that are inside portals are clipped off.
        """
        collision_rect = self.collision_rect.copy()
        for portal in self.level.get_group("portal-physics"):
            if is_inside_portal(collision_rect, portal.collision_rect, portal.orientation):
                collision_rect = clip_rect_to_portal(collision_rect, portal.collision_rect, portal.orientation)
        return collision_rect

    def handle_dynamic_collision_inside_portal(self, axis: int, dt: float) -> bool:
        """
        Extra collision handling when inside a portal

        Called internally.
        """
        # If I've gone through the enter portal, switch to the exit one
        if is_through_portal(self.collision_rect, self.current_portal.collision_rect, self.current_portal.orientation) and self.portal_state != self.PortalState.EXIT:
            self.exit_portal()
            return True
        # If I've turned around when inside the exit portal, swap the enter and exit portals
        elif self.portal_state == self.PortalState.EXIT and is_entering_portal(self.twin_portal.orientation, self.velocity):
            self.enter_portal(self.twin_portal, self.current_portal)
            return True
        # If I'm not touching any portal, normalize state
        elif (not is_inside_portal(self.collision_rect, self.current_portal.collision_rect, self.current_portal.orientation) and not 
                is_inside_portal(self.collision_rect, self.twin_portal.collision_rect, self.twin_portal.orientation)):
            self.abort_portal()
            return False

        return False
    
    def handle_dynamic_collision(self, axis: int, dt: float) -> bool: 
        """
        Collision handling for dynamic sprites

        Called internally
        """
        def must_move():
            # Part of me that is inside a portal does not collide
            collision_rect = self.clipped_collision_rect()
            for sprite in self.level.get_group("static-physics"):
                # only collide with one_way when going down or ducking
                if sprite.one_way and (self.velocity.y < 0 or self.ducking):
                    continue
                if sprite.collision_rect.colliderect(collision_rect):
                    return True
            return False
        
        if self.current_portal:
            self.handle_position_in_portal()
            self.handle_dynamic_collision_inside_portal(axis, dt)

        # looped portals can make you go FAST
        self.velocity.clamp_magnitude_ip(MAX_SPEED)

        # semi-implicit Euler integration + latency compenstation
        self.velocity[axis] += self.acceleration[axis] * dt


        center = pygame.Vector2(self.rect.center)
        center[axis] += self.velocity[axis] * dt + self.missed[axis]
        self.missed[axis] = 0
        self.rect.center = center

        # which way I need to move if I'm colliding based on velocity
        offset: int = 1
        if self.velocity[axis] > 0:
            offset = -1

        # move me out of collision
        moved: bool = False
        while must_move():
            self.rect[axis] += offset
            # Don't collide with stuff overlapping with portals when moving into or out of the portal
            if (self.engaged_portal is not None and get_axis_of_direction(self.engaged_portal.orientation) == axis):
                moved = False
            else:
                self.velocity[axis] = 0
                moved = True

        if moved:
            # :sob: what does this even mean - Aiden
            self.rect.center = pygame.Rect(self.rect).center
            # apply friction when sprite is touching the ground
            self.velocity[0] *= 1 / (1 + (self.friction * dt)) 

        return moved

    def handle_trigger_collision(self) -> None:
        """
        Collision handling for trigger sprites

        Called internally.
        """
        for sprite in self.level.get_group("triggerable").sprites():
            if sprite.rect.collision_rect.colliderect(self.collision_rect):
                sprite.trigger(self)

    def handle_portal_collision(self) -> None:
        """
        Collision handling for portal sprites

        Called internally.
        """
        for sprite in self.level.get_group("dynamic-physics"):
            if sprite.portal_state == self.PortalState.OUT and is_inside_portal(sprite.collision_rect, self.collision_rect, self.orientation) and is_entering_portal(self.orientation, sprite.velocity):
                for portal in self.level.get_group(self.tunnel_id):
                    if portal is not self:
                        sprite.enter_portal(self, portal)

    def handle_position_in_portal(self) -> None:
        """
        If the sprite is inside the portal, it can't leave it, except through the way it entered
        """
        # PS - sorry all the collision based names for functions were taken :|
        # TODO: get this to restrict the sprite tries to leave the portal in a direction perpendicular to it's orientation
        if self.rect.colliderect(self.current_portal.rect) and self.portal_state in {self.PortalState.EXIT, self.PortalState.ENTER}:
            if get_axis_of_direction(self.current_portal.orientation):
                if self.rect.right > self.current_portal.rect.right:
                    self.rect.right = self.current_portal.rect.right - 1
                    self.velocity.x = 0
                elif self.rect.left < self.current_portal.rect.left:
                    self.rect.left = self.current_portal.rect.left + 1
                    self.velocity.x = 0
            else:
                if self.rect.top < self.current_portal.rect.top:
                    self.rect.top = self.current_portal.rect.top + 1
                    self.velocity.y = 0
                elif self.rect.bottom > self.current_portal.rect.bottom:
                    self.rect.bottom = self.current_portal.rect.bottom - 1
                    self.velocity.y = 0

    def enter_portal(self, portal: PhysicsSpriteInterface, twin: PhysicsSpriteInterface) -> None:
        """
        State changes when a sprite enters a portal

        Called internally.
        """
        self.current_portal = portal
        self.twin_portal = twin
        self.portal_state = self.PortalState.ENTER
        
    def exit_portal(self) -> None:
        """
        State changes when a sprite switches from entering a portal to exiting a different portal (Now it accounts for portals being of different orientations :D)

        Called internally.
        """
        # move the sprite to behind the exit portal
        if self.twin_portal.orientation == Direction.NORTH:
            self.velocity = pygame.Vector2(0, -self.velocity.length())
            if get_axis_of_direction(self.current_portal.orientation):
                self.rect.left = self.twin_portal.rect.left + self.rect.left - self.current_portal.rect.left
            else:
                self.rect.left = self.twin_portal.rect.left + self.current_portal.rect.bottom - self.rect.bottom
            self.rect.top = self.twin_portal.rect.bottom - 1

        if self.twin_portal.orientation == Direction.SOUTH:
            self.velocity = pygame.Vector2(0, self.velocity.length())
            if get_axis_of_direction(self.current_portal.orientation):
                self.rect.left = self.twin_portal.rect.left + self.rect.left - self.current_portal.rect.left
            else:
                self.rect.left = self.twin_portal.rect.left + self.current_portal.rect.bottom - self.rect.bottom
            self.rect.bottom = self.twin_portal.rect.top + 1

        if self.twin_portal.orientation == Direction.EAST:
            self.velocity = pygame.Vector2(self.velocity.length(), 0)
            if get_axis_of_direction(self.current_portal.orientation):
                self.rect.top = self.twin_portal.rect.top + self.current_portal.rect.right - self.rect.right
            else:
                self.rect.top = self.twin_portal.rect.top + self.rect.top - self.current_portal.rect.top
            self.rect.right = self.twin_portal.rect.left + 1

        if self.twin_portal.orientation == Direction.WEST:
            self.velocity = pygame.Vector2(-self.velocity.length(), 0)
            if get_axis_of_direction(self.current_portal.orientation):
                self.rect.top = self.twin_portal.rect.top + self.current_portal.rect.right - self.rect.right
            else:
                self.rect.top = self.twin_portal.rect.top + self.rect.top - self.current_portal.rect.top
            self.rect.left = self.twin_portal.rect.right - 1

        self.portal_state = self.PortalState.EXIT

    def abort_portal(self) -> None:
        """
        State changes when I leave the portal completely

        Called internally.
        """
        self.current_portal = None
        self.twin_portal = None
        self.portal_state = self.PortalState.OUT

    def pick_up(self) -> None:
        """
        Finds closest throwable object and sets it as the current object picked up
        """
        closest_throwable, distance = self.find_closest_throwable()
        if distance <= self.min_distance and not self.current_throwable:
            self.current_throwable = closest_throwable
            self.current_throwable.picker_upper = self

    def throw(self, dt: float) -> None:
        """
        Throws the current object held
        """
        self.current_throwable.velocity = self.facing * self.current_throwable.flight_speed
        self.current_throwable.was_thrown = True
        self.current_throwable.picker_upper = None
        self.current_throwable = None

    def find_closest_throwable(self) -> None:
        """
        Finds the closest throwable object
        """
        # Forgive me for the atrocity I have commited here
        throwables = self.level.get_group("throwable-physics").sprites()
        if not len(throwables):
            return None, 0
        closest_throwable = throwables[0]
        closest_distance = (pygame.Vector2(self.pos) - pygame.Vector2(closest_throwable.pos)).length()
        for throwable in throwables:
            current_distance = (pygame.Vector2(self.pos) - pygame.Vector2(throwable.pos)).length()
            if current_distance < closest_distance:
                closest_throwable = throwable
                closest_distance = current_distance

        return closest_throwable, closest_distance
    
    def update_throwable(self, dt: float) -> None:
        """
        makes the picked up object follow the one who picked up the object
        """
        if self.picker_upper:
            distance_to = pygame.Vector2(self.picker_upper.pos) - pygame.Vector2(self.pos)
            self.velocity = distance_to * 2000 * dt

    def handle_commands(self) -> None:
        """
        Accepts movement commands (left, right, jump, duck) from this sprite's Controller
        """
        self.just_went_buffer = {
            "up": False,
            "left": False,
            "right": False,
            "jump": False,
            "duck": False,
            "pick_up_or_throw": False,
        }
        for command in self.controller.get_commands():
            name: str = command.command
            if name == "up":
                self.facing.update(0, -1)
                self.just_went["up"] = True
            if name == "left":
                self.left((pygame.time.get_ticks() - command.timestamp) / 1000)
                self.facing.update(-1, 0)
            if name == "right":
                self.right((pygame.time.get_ticks() - command.timestamp) / 1000)
                self.facing.update(1, 0)
            if name == "duck":
                self.duck((pygame.time.get_ticks() - command.timestamp) / 1000)
                self.facing.update(0, 1)
            if name == "jump":
                self.jump((pygame.time.get_ticks() - command.timestamp) / 1000)
            if name == "pick_up_or_throw":
                if not self.current_throwable:
                    self.pick_up()
                else:
                    self.throw((pygame.time.get_ticks() - command.timestamp) / 1000)
                self.just_went["pick_up_or_throw"] = True # Don't know the purpose of this one :P - Aiden

        self.just_went = self.just_went_buffer

    def update_physics(self, dt) -> None:
        """Update this sprite's physics"""
        self.handle_commands()
        if self.physics_type == PhysicsType.DYNAMIC:
            self.on_ground = False
            falling = self.velocity.y > 0 and not self.current_portal
            self.update_throwable(dt) # Note: Make sure to do any velocity modifications before handle_dynamic_collision otherwise weird stuff happen - Aiden
            self.handle_dynamic_collision(0, dt)
            moved = self.handle_dynamic_collision(1, dt)
            if falling and moved:
                self.on_ground = True
                self.ducking = False
        if self.physics_type == PhysicsType.TRIGGER:
            self.handle_trigger_collision()
        if self.physics_type == PhysicsType.PORTAL:
            self.handle_portal_collision()

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        """
        Draw sprite.image at sprite.rect, excluding area not in sprite.clip_rect

        Except all of the above is interpolated
        """
        new_rect: pygame.FRect = self.rect.copy()
        # only draw the part of the sprite that is not in a portal
        clip_rect = self.interpolated_cliprect(dt_since_physics)
        new_rect.center = self.interpolated_pos(dt_since_physics) + pygame.Vector2(clip_rect.topleft) - offset
        surface.blit(self.image.subsurface(clip_rect), new_rect)
