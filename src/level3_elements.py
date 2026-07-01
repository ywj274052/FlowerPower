import pygame

class PoisonZone(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        # 创建一个支持透明度的表面，设为紫色半透明以符合毒液的视觉效果
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((128, 0, 128, 120)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # 伤害计时器
        self.damage_timer = 0

    def update(self, player):
        # 检测玩家的碰撞框是否和毒沼泽重叠
        if self.rect.colliderect(player.rect):
            self.damage_timer += 1
            # 假设游戏是 60 FPS，30 帧就是半秒
            if self.damage_timer >= 30: 
                player.hp -= 2
                self.damage_timer = 0
        else:
            # 玩家离开毒沼泽，立刻重置计时器
            self.damage_timer = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)