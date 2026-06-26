# src/player.py
import pygame
from src.settings import *   # 注意这里是从 src.settings 导入

class Player:  # ← 注意是大写 P
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.color = PLAYER_GREEN
        self.speed_x = 0
        self.speed_y = 0
        self.on_ground = False

    def update(self, keys_pressed):
        # ... 后面的代码
        pass

    def draw(self, screen):
        # ... 后面的代码
        pass