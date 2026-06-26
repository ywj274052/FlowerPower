import pygame
import sys
from src.settings import *
from src.player import Player

# 初始化
pygame.init()

# 窗口设置
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FlowerPower")
clock = pygame.time.Clock()

# 创建玩家（起始位置在左边）
player = Player(100, 400)

# 游戏循环
running = True
while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 获取按键
    keys = pygame.key.get_pressed()

    # 更新玩家
    player.update(keys)

    # === 绘制 ===
    screen.fill(SKY_BLUE)

    # 画地面
    pygame.draw.rect(screen, GROUND_BROWN, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))

    # 画玩家
    player.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()