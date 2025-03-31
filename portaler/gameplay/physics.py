from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from functools import wraps

import pygame

from ..const import (
    AIR_CONTROLS_REDUCTION,
    GRAVITY,
    HORIZONTAL_YEET_ANGLE,
    MAX_COLLISION_OFFSET,
    MAX_SPEED,
    TILE_SIZE,
)
from ..interfaces import (
    DIRECTION_TO_ANGLE,
    Direction,
    PhysicsSpriteInterface,
    PhysicsType,
    SpriteInitData,
    SpriteInterface,
    SpritePhysicsData,
)
from .sprite import Sprite
from .sprites_and_sounds import play_sound


def is_aligned_with_portal(
    collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction, tolerance: float = 0.0
) -> bool:
    """Returns if a rect is aligned with the portal in its axis"""
    if direction in {Direction.NORTH, Direction.SOUTH}:
        return (
            collision_rect.left > portal_rect.left - tolerance
            and collision_rect.right < portal_rect.right + tolerance
        )
    return (
        collision_rect.top > portal_rect.top - tolerance
        and collision_rect.bottom < portal_rect.bottom + tolerance
    )


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

    raise ValueError("This shouldn't be ever reached")


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

    raise ValueError("This shouldn't be ever reached")


def clip_rect_to_portal(
    collision_rect: pygame.FRect, portal_rect: pygame.FRect, direction: Direction
) -> pygame.FRect:
    """Clips a rect to only what you would see if the rect entered a portal"""
    collision_rect = collision_rect.copy()
    # to avoid accidental colision with the floor below the portal
    # because I HAVE NO CLUE WHERE THAT ISSUE EVEN STEMS FROM
    collision_offset = 4
    overlap = 0.0

    if direction == Direction.NORTH:
        # only show rect above top  ?????
        if collision_rect.bottom > portal_rect.bottom:
            overlap = min(
                collision_rect.bottom - portal_rect.bottom + collision_offset, collision_rect.height
            )
        collision_rect.height -= overlap

    if direction == Direction.SOUTH:
        # only show rect below bottom  ?????
        if collision_rect.top < portal_rect.top:
            overlap = min(portal_rect.top - collision_rect.top + collision_offset, collision_rect.height)
        collision_rect.top += overlap
        collision_rect.height -= overlap

    if direction == Direction.EAST:
        # only show rect right of right  ?????
        if collision_rect.left < portal_rect.left:
            overlap = min(portal_rect.left - collision_rect.left + collision_offset, collision_rect.height)

        collision_rect.width -= overlap
        collision_rect.left += overlap

    if direction == Direction.WEST:
        # only show rect left of left  ?????
        if collision_rect.right > portal_rect.right:
            overlap = min(collision_rect.right - portal_rect.right + collision_offset, collision_rect.height)
        collision_rect.width -= overlap
    return collision_rect


def get_axis_of_direction(direction: Direction) -> int:
    """Returns integer axis of a direction (0 for x, 1 for y)"""
    return int(direction in {Direction.NORTH, Direction.SOUTH})


def protect(fn: Callable[[PhysicsSprite, float], None]):
    """
    Simple wrapper for control command functions to avoid calling them multiple times a physics frame.
    """

    @wraps(fn)
    def inner(self, dt: float) -> None:
        if not self.commands_used.get(fn.__name__, False):
            self.commands_used[fn.__name__] = True
            fn(self, dt)

    return inner


def sign(num):
    # return -1 if num < 0 else int(num > 0)
    return (0, -1, 1)[(num != 0) + (num > 0)]


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
        self.acceleration: pygame.Vector2 = pygame.Vector2(
            0
        )  # Separated from gravity, to not apply gravity when on ground.
        self.gravity: pygame.Vector2 = pygame.Vector2(GRAVITY)  # pixels/second squared (I think)
        self.yeet_force: float = physics_data.yeet_force  # how hard the sprite is thrown (if dynamic)
        self.horizontal_ground_speed: float = (
            physics_data.horizontal_ground_speed
        )  # how fast the sprite walks up to, right and left (if dynamic), on ground
        self.horizontal_ground_acceleration: float = (
            physics_data.horizontal_ground_acceleration
        )  # how fast sprite accelerates on ground
        self.horizontal_air_speed: float = (
            physics_data.horizontal_air_speed
        )  # how fast the sprite accelerates up to (from 0) while in the air
        self.horizontal_air_acceleration: float = (
            physics_data.horizontal_air_acceleration
        )  # how fast sprite accelerates in air
        self.ground_damping: float = (
            physics_data.ground_damping
        )  # how quickly the sprite slows down (if dynamic)
        self.air_damping: float = physics_data.air_damping  # see above, but applied when in the air
        self.weight: float = physics_data.weight  # unused atm
        self.jump_speed: float = physics_data.jump_speed  # initial jump velocity (if dynamic)
        self.duck_speed: float = physics_data.duck_speed  # initial downward duck velocity (if dynamic)
        self.orientation: Direction = physics_data.orientation  # orientation
        self.tunnel_id: str = physics_data.tunnel_id  # used to get twin portal (if portal)
        self.coyote_time: float = (
            physics_data.coyote_time
        )  # time-frame of allowed jumping when disconnected from the ground (if dynamic)
        self.coyote_time_left: float = 0  # see above
        self.on_ground: bool = False  # whether sprite is touching ground (if dynamic)
        self.one_way: bool = physics_data.one_way  # whether sprite only collides downward (if static)
        self.facing: pygame.Vector2 = (
            pygame.Vector2()
        )  # the direction the sprite is manually facing (usually <0, 0> for non-player sprites)

        self.max_holding_distance: float = TILE_SIZE * 1.0  # maximum distance to pick up something, carry it
        self.current_throwable: PhysicsSprite | None = (
            None  # the current think you're about to throw at someone        # bro made a gramatikal mistak
        )
        self.picker_upper: PhysicsSprite | None = None  # the one picking up self

        # (Latency compensation removed. So unnecessary.)

        # Used to limit control command per physics frame.
        self.commands_used: dict[str, bool] = {}

        # portal handling
        self.in_portal: PhysicsSprite | None = None  # which portal I am entering
        self.out_portal: PhysicsSprite | None = None  # which portal I am exiting
        self.portal_state: PhysicsSprite.PortalState = self.PortalState.OUT  # what portal state I am in

    def interpolated_clip_rect(self, dt_since_physics: float) -> pygame.FRect:
        """Use this clip rect during render calls"""
        if self.portal_state == self.PortalState.OUT:
            return self.image.get_frect()
        assert self.engaged_portal is not None
        collision_rect = self.rect.copy()
        collision_rect.center = self.interpolated_pos(dt_since_physics)
        clipped = clip_rect_to_portal(
            collision_rect, self.engaged_portal.rect, self.engaged_portal.orientation
        )
        clipped.move_ip(-collision_rect.x, -collision_rect.y)
        return clipped

    def clipped_collision_rect(self):
        """
        Collision rect used in actual collision checking.

        Areas that are inside portals are clipped off.
        """
        collision_rect = self.collision_rect.copy()
        for portal in self.level.get_group("portal-physics"):
            if is_inside_portal(collision_rect, portal.collision_rect, portal.orientation):
                collision_rect = clip_rect_to_portal(
                    collision_rect, portal.collision_rect, portal.orientation
                )
        return collision_rect

    @property
    def engaged_portal(self) -> PhysicsSprite | None:
        """Which portal sprite is currently "inside" (entering or exiting) or None"""
        if self.portal_state == self.PortalState.ENTER:
            return self.in_portal
        if self.portal_state == self.PortalState.EXIT:
            return self.out_portal
        # I'm assuming it was supposed to be PortalState.Exit in
        # the second if statement and not PortalState.Enter??? - Aiden
        return None

    def trigger(self, other: SpriteInterface | None) -> None:
        """
        Called when this sprite is being touched by a dynamic physics object.

        Other is the sprite that triggered me. Called every frame I am touching it.
        """
        pass

    def untrigger(self, other: SpriteInterface | None):
        """
        If i am a triggerable object.

        Called when this sprite stops being touched by a dynamic physics object.
        Called every frame i am not touched    <- DIABOLICAL wording

        Other is the sprite that untriggered me.
        For activation objects: activated only when a button (or something else) activates it
        """
        pass

    @protect
    def left(self, dt: float) -> None:
        """If I am dynamic, try to move left until the next frame"""
        self._move(dt, -1)

    @protect
    def right(self, dt: float) -> None:
        """If I am dynamic, try to move right until the next frame"""
        self._move(dt, 1)

    def _move(self, dt: float, sign: int) -> None:
        if not dt:
            return
        if self.on_ground:
            # DO NOT USE dt HERE
            if self.horizontal_ground_speed > sign * self.velocity.x:
                self.velocity.x = sign * min(
                    self.horizontal_ground_speed,
                    sign * self.velocity.x
                    + self.horizontal_ground_acceleration * dt * AIR_CONTROLS_REDUCTION,
                )
            # self.velocity.x = sign * self.horizontal_ground_speed
        else:
            if self.horizontal_air_speed > sign * self.velocity.x:
                self.velocity.x = sign * min(
                    self.horizontal_air_speed,
                    sign * self.velocity.x + self.horizontal_air_acceleration * dt * AIR_CONTROLS_REDUCTION,
                )

    @protect
    def jump(self, dt: float) -> None:
        """If I am dynamic, try to jump"""
        if self.on_ground or self.coyote_time_left > 0:
            self.velocity.y = -self.jump_speed  # DO NOT USE dt HERE
            self.coyote_time_left = 0
            play_sound("jump.ogg")

    @protect
    def duck(self, dt: float) -> None:
        """If I am dynamic, try to duck until the next frame"""
        if not self.on_ground:
            self.velocity.y = max(self.duck_speed, self.velocity.y, 1)  # DO NOT USE dt HERE
            play_sound("slam.ogg")

    @protect
    def interact(self, dt: float) -> None:
        """Interact with different objects"""
        if self.throw(dt):
            return
        if self.pick_up():
            return

    def interpolated_pos(self, dt_since_physics: float) -> tuple[float, float]:
        """Use this position during render calls"""
        pos = self.pos + self.velocity * dt_since_physics
        return pos[0], pos[1]

    def handle_dynamic_collision_inside_portal(self, axis: int, dt: float) -> None:
        """Extra collision handling when inside a portal

        Called internally.
        """
        assert self.engaged_portal is not None
        assert self.in_portal is not None
        assert self.out_portal is not None
        # If I've gone through the enter portal, switch to the exit one
        if self.portal_state == self.PortalState.ENTER and is_through_portal(
            self.collision_rect,
            self.in_portal.collision_rect,
            self.in_portal.orientation,
        ):
            self.teleport_portal()
            return
        # If I've turned around when inside the exit portal, swap the enter and exit portals
        if self.portal_state == self.PortalState.EXIT and is_entering_portal(
            self.out_portal.orientation, self.velocity
        ):
            self.enter_portal(self.out_portal, self.in_portal)
            return
        # If I'm not touching any portal, normalize state
        if not is_inside_portal(
            self.collision_rect, self.engaged_portal.collision_rect, self.engaged_portal.orientation
        ):
            self.exit_portal()
            return
        return

    def update_position(self, axis: int, dt: float) -> None:
        """
        Update position and do collision resolution.

        Called internally
        """

        if self.portal_state != self.PortalState.OUT:
            self.handle_dynamic_collision_inside_portal(axis, dt)

        # looped portals can make you go FAST
        self.velocity.clamp_magnitude_ip(MAX_SPEED)

        # semi-implicit Euler integration + latency compensation
        self.velocity[axis] += (
            self.acceleration[axis] * dt
        )  # buddy, what 'Euler integration' and 'latency compensation' are you yapping about
        self.velocity[axis] += self.gravity[axis] * dt

        center = pygame.Vector2(self.rect.center)
        center[axis] += self.velocity[axis] * dt
        self.rect.center = center[0], center[1]

        offset = self.resolve_collision(axis, dt)
        if offset == 0.0:
            return
        self.velocity[axis] = 0.0
        self.rect[axis] += offset

    def resolve_collision(self, axis: int, dt: float) -> float:
        """
        Find the offset to resolve a collision, for the given axis.
        Both directions are checked, with the smallest offset being chosen.
        Velocity direction is not taken into account.
        An offset of 0.0 indicates no collision.

        If the offset returned would be greater than MAX_COLLISION_OFFSET, 0.0 is returned instead.

        Called internally
        """
        # which way I need to move if I'm colliding based on velocity
        offset_step: float = 0.2  # (>0.0) how precise collision resolution is

        # move me out of collision
        offset: float = 0.0
        while offset <= MAX_COLLISION_OFFSET:
            if not self.is_colliding_static(axis, dt, offset):
                return offset
            if not self.is_colliding_static(axis, dt, -offset):
                return -offset
            offset += offset_step
        return 0.0  # Offset too large

    def handle_trigger_collision(self) -> None:
        """
        Collision handling for trigger sprites

        Called internally.
        """
        collision_rect = self.clipped_collision_rect()
        for sprite in self.level.get_group("dynamic-physics"):
            if sprite.collision_rect.colliderect(collision_rect):
                self.trigger(sprite)
                return
        self.untrigger(None)

    def handle_portal_collision(self) -> None:
        """
        Collision handling for portal sprites

        Called internally.
        """
        sprite: PhysicsSprite
        for sprite in self.level.get_group("dynamic-physics"):
            if (
                sprite.portal_state == self.PortalState.OUT
                and is_inside_portal(sprite.collision_rect, self.collision_rect, self.orientation)
                and is_entering_portal(self.orientation, sprite.velocity)
            ):
                for portal in self.level.get_group(self.tunnel_id):
                    # Find twin
                    if portal is not self:
                        sprite.enter_portal(self, portal)

    def enter_portal(self, in_portal: PhysicsSprite, out_portal: PhysicsSprite) -> None:
        """
        State changes when a sprite enters a portal

        Called internally.
        """
        self.in_portal = in_portal
        self.out_portal = out_portal
        self.portal_state = self.PortalState.ENTER

    def teleport_portal(self) -> None:
        """
        State changes when a sprite switches from entering a portal to exiting a different portal
        (Now it accounts for portals being of different orientations :D)

        Called internally.
        """
        assert self.out_portal is not None
        assert self.in_portal is not None
        if self.picker_upper is not None and self.picker_upper.engaged_portal is not self.out_portal:
            # Do not teleport if picker upper has not already teleported
            return
        out_orientation = self.out_portal.orientation
        self.velocity = pygame.Vector2(self.velocity.length(), 0).rotate(DIRECTION_TO_ANGLE[out_orientation])
        # move the sprite to behind the exit portal
        if get_axis_of_direction(out_orientation) == 0:
            self.rect.top = self.out_portal.rect.top + (
                self.rect.top - self.in_portal.rect.top
                if get_axis_of_direction(self.in_portal.orientation) == 0
                else self.in_portal.rect.right - self.rect.right
            )
            if out_orientation == Direction.WEST:
                self.rect.left = self.out_portal.rect.right - 1
            else:
                self.rect.right = self.out_portal.rect.left + 1
        else:
            self.rect.left = self.out_portal.rect.left + (
                self.rect.left - self.in_portal.rect.left
                if get_axis_of_direction(self.in_portal.orientation) == 1
                else self.in_portal.rect.bottom - self.rect.bottom
            )
            if out_orientation == Direction.NORTH:
                self.rect.top = self.out_portal.rect.bottom - 1
            else:
                self.rect.bottom = self.out_portal.rect.top + 1
        self.portal_state = self.PortalState.EXIT
        play_sound("teleport.ogg")
        if self.current_throwable is not None:
            # Teleport current throwable
            if self.current_throwable.in_portal is not self.in_portal:
                self.current_throwable.enter_portal(self.in_portal, self.out_portal)
            self.current_throwable.teleport_portal()

    def exit_portal(self) -> None:
        """
        State changes when I leave the portal completely

        Called internally.
        """
        self.in_portal = None
        self.out_portal = None
        self.portal_state = self.PortalState.OUT

    def pick_up(self) -> bool:
        """
        Finds closest throwable object and sets it as the current object picked up
        """
        closest_throwable, distance = self.find_closest_throwable()
        if closest_throwable is None:
            return False
        if distance <= self.max_holding_distance and not self.current_throwable:
            self.current_throwable = closest_throwable
            self.current_throwable.picker_upper = self
            return True
        return False

    def throw(self, dt: float) -> bool:
        """
        Throws the current object held
        """
        if self.current_throwable is None:
            return False
        yeet_force = self.yeet_force
        if self.facing:
            if not self.facing.y:
                yeet_angle = -HORIZONTAL_YEET_ANGLE if self.facing.x > 0 else 180 + HORIZONTAL_YEET_ANGLE
            else:
                yeet_angle = pygame.Vector2(self.facing.x, -self.facing.y).angle_to((1, 0))
            impulse = pygame.Vector2(yeet_force, 0).rotate(yeet_angle)  # DO NOT USE dt HERE
        else:
            impulse = pygame.Vector2()
        # HACK: halve x impulse because it is too powerful
        self.current_throwable.velocity.x += impulse.x * 0.5 / self.current_throwable.weight
        # HACK: don't inherit old y velocity so that jump + throw is more consistent
        self.current_throwable.velocity.y = impulse.y / self.current_throwable.weight
        self.velocity -= impulse / self.weight
        self.current_throwable.picker_upper = None
        self.current_throwable = None
        return True

    def find_closest_throwable(self) -> tuple[PhysicsSprite | None, float]:
        """Finds the closest throwable object and its distance.

        If no throwables, the sprite is None and distance is infinity.
        """
        # Forgive me for the atrocity I have commited here
        group: pygame.sprite.AbstractGroup | None = self.level.get_group("throwable-physics", None)
        throwables = set(group) if group else set()
        closest_throwable = None
        closest_distance = float("inf")
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
        if self.picker_upper is None:
            return
        offset = pygame.Vector2(self.picker_upper.pos) - pygame.Vector2(self.pos)
        if offset.length() > self.max_holding_distance:
            # Throwable is released if it is too far
            self.picker_upper.current_throwable = None
            self.picker_upper = None
            return
        leeway = TILE_SIZE // 4
        if offset.length() <= leeway:
            # Give some leeway offset for pulling
            return
        # otherwise make this cool magnet effect
        spring_force: float = 10_000  # stronger pull
        damping_coefficient: float = 2_000  # reduce jittering, whipping
        damping_impulse = (self.picker_upper.velocity - self.velocity) * (damping_coefficient * dt)
        impulse = offset * spring_force * dt + damping_impulse
        self.velocity += impulse / self.weight
        opposite_impulse = -impulse / self.picker_upper.weight
        # Cap opposite impulse so that player cannot 'hang' from its throwable (for one-way platforms)
        opposite_impulse[1] = max(-GRAVITY[1] * dt * 0.9, opposite_impulse[1])
        self.picker_upper.velocity += opposite_impulse

    def is_colliding_static(self, axis: int, dt: float, offset: float = 0.0) -> bool:
        """Check if I am colliding with a static object along the given axis, when moved by offset.

        Uses dt in order to prevent tunneling.
        """
        collision_rect = self.clipped_collision_rect()
        collision_rect[axis] += offset

        if self.engaged_portal is not None and (
            # Don't collide on portal axis when moving into or out of the portal
            get_axis_of_direction(self.engaged_portal.orientation) == axis
            # Don't collide perpendicularly when within the sides of portal
            or is_aligned_with_portal(
                collision_rect, self.engaged_portal.rect, self.engaged_portal.orientation
            )
        ):
            return False
        for sprite in self.level.get_group("static-physics"):
            if not sprite.collision_rect.colliderect(collision_rect):
                continue
            if not sprite.one_way:
                return True
            if axis == 0:
                # Never collide horizontally with one way platforms
                continue
            y_velocity = self.velocity.y
            if y_velocity < 0:
                # skip one way if moving up
                continue
            min_one_way_velocity = 100.0  # The lowest velocity at which a player can manually go down through
            if self.facing.y > 0 and y_velocity < min_one_way_velocity:
                # player presses down
                # AND velocity is low (forces fast falling speeds to collide at least once)
                continue
            # NOTE: one way platforms are thinner (shorter) than normal tiles for obvious reasons
            if self.collision_rect.bottom > sprite.collision_rect.bottom:
                # inside platform tile rect but too low to get on top
                if self.collision_rect.bottom - y_velocity * dt > sprite.collision_rect.bottom:
                    # (anti-tunneling) previous position was also too low to get on top
                    continue
            return True
        return False

    def update_physics(self, dt: float) -> None:
        """Update this sprite's physics"""
        # Restore previous commands
        self.commands_used.clear()

        if self.physics_type == PhysicsType.DYNAMIC:
            # Note: Make sure to do any velocity modifications before update_position
            # otherwise weird stuff happen - Aiden
            self.update_throwable(dt)
            self.update_position(1, dt)
            self.update_position(0, dt)
            self.on_ground = self.is_colliding_static(1, dt, 0.5)
            if self.on_ground:
                self.velocity[1] = 0
                if (
                    sign(self.facing[0]) != sign(self.velocity[0])
                    or abs(self.velocity[0]) > self.horizontal_ground_speed
                ):
                    self.velocity[0] *= self.ground_damping**dt
                self.coyote_time_left = self.coyote_time
            else:
                # A bit unrealistic, that there's no vertical damping.
                if sign(self.facing[0]) != sign(self.velocity[0]):
                    self.velocity[0] *= self.air_damping**dt
                self.coyote_time_left -= dt
            self.update_facing()  # get the direction the object is facing

        if self.physics_type == PhysicsType.TRIGGER:
            self.handle_trigger_collision()
        if self.physics_type == PhysicsType.PORTAL:
            self.handle_portal_collision()

    def update_facing(self) -> None:
        """Update self.facing.

        Base behavior: don't change self.facing.
        """

    def draw(
        self,
        surface: pygame.Surface,
        offset: pygame.Vector2,
        dt_since_physics: float,
    ) -> None:
        """
        Draw sprite.image at sprite.rect, excluding area not in sprite.clip_rect

        Except all of the above is interpolated
        """
        new_rect = self.rect.copy()
        # only draw the part of the sprite that is above the 'bottom' of the portal (if we are inside one)
        # (only applies to dynamic objects)
        clip_rect = self.interpolated_clip_rect(dt_since_physics)
        center = self.interpolated_pos(dt_since_physics) + pygame.Vector2(clip_rect.topleft) - offset
        new_rect.center = center[0], center[1]
        surface.blit(self.image.subsurface(clip_rect), new_rect)
