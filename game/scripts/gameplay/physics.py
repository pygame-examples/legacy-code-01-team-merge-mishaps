from typing import Iterator
from queue import Queue

import pygame

from ..interfaces import SpriteInitData, PhysicsType, SpritePhysicsData, SpriteInterface, SpriteCommand
from ..const import GRAVITY
from .sprite import Sprite
    

class PhysicsSprite(Sprite):
    def __init__(self, data: SpriteInitData, physics_data: SpritePhysicsData):
        super().__init__(data)
        self.physics_type: PhysicsType = physics_data.physics_type
        self.velocity: pygame.Vector2 = pygame.Vector2()
        self.acceleration: pygame.Vector2 = pygame.Vector2(GRAVITY)
        self.horizontal_speed: float = physics_data.horizontal_speed
        self.weight: float = physics_data.weight
        self.jump_speed: float = physics_data.jump_speed
        self.duck_speed: float = physics_data.duck_speed
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

    @property
    def collision_rect(self):
        return self.rect.copy()

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
        print("jump")
        if self.on_ground:
            print("boing")
            self.velocity.y = -self.jump_speed

    def duck(self, lost_time: float) -> None:
        self.ducking = True
        if not self.on_ground:
            self.velocity.y = max(self.duck_speed, self.velocity.y)

    def interpolated_pos(self, dt_since_physics: float) -> pygame.Vector2:
        return self.pos + self.velocity * dt_since_physics
    
    def handle_dynamic_collision(self, index: int, dt: float) -> bool:
        def must_move():
            for sprite in self.level.get_group("static-physics"):
                if sprite.one_way and (self.velocity.y < 0 or self.ducking):
                    continue
                if sprite.collision_rect.colliderect(self.collision_rect):
                    return True
            return False

        self.velocity[index] += self.acceleration[index] * dt
        center = pygame.Vector2(self.rect.center)
        center[index] += self.velocity[index] * dt + self.missed[index]
        self.missed[index] = 0
        self.rect.center = center

        offset: int = 1
        if self.velocity[index] > 0:
            offset = -1
        
        moved: bool = False
        while must_move():
            moved = True
            self.rect[index] += offset
            self.velocity[index] = 0

        if moved:
            self.rect.center = pygame.Rect(self.rect).center

        return moved

    def handle_trigger_collision(self) -> None:
        for sprite in self.level.get_group("triggerable").sprites():
            if sprite.rect.collision_rect.colliderect(self.collision_rect):
                sprite.trigger(self)

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
            falling = self.velocity.y > 0
            self.handle_dynamic_collision(0, dt)
            moved = self.handle_dynamic_collision(1, dt)
            if falling and moved:
                self.on_ground = True
                self.ducking = False
        if self.physics_type == PhysicsType.TRIGGER:
            self.handle_trigger_collision()

        
