import pygame
import math

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

# ==========================================
# Level 3 专属怪物系统
# ==========================================

class ToxicSludge(pygame.sprite.Sprite):
    """怪物 1: 地面缓慢追击者 (高血量，低移速)"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill((50, 150, 50))  # 墨绿色软泥
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.hp = 30
        self.speed = 1.5

        # 【新增】攻击冷却计时器
        self.attack_timer = 0

    def update(self, player):
        # 始终朝着玩家在 X 轴上移动
        if player:
            if self.rect.centerx < player.rect.centerx:
                self.rect.x += self.speed
            elif self.rect.centerx > player.rect.centerx:
                self.rect.x -= self.speed

            # 2. 【新增】对玩家的伤害判定
            # 检测自身是否碰到了玩家
            if self.rect.colliderect(player.rect):
                self.attack_timer += 1
                # 每 45 帧（约 0.75 秒）对玩家造成一次伤害
                if self.attack_timer >= 45:
                    # 假设玩家扣血的方法叫 take_damage
                    player.take_damage(10) 
                    print("⚠️ 玩家被软泥怪腐蚀，扣除 10 点 HP!")
                    self.attack_timer = 0
            else:
                # 没碰到玩家时，重置计时器
                self.attack_timer = 0

class SwampMoth(pygame.sprite.Sprite):
    """怪物 2: 空中正弦波飞行者 (远程射手)"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 20))
        self.image.fill((150, 50, 150))  
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 15
        self.speed = 2
        self.start_y = y
        self.timer = 0
        
        # 【修改】将近战属性改为远程射击冷却
        self.shoot_timer = 0

    def update(self, player):
        self.timer += 1
        # 正弦波上下飘动
        self.rect.y = self.start_y + int(math.sin(self.timer * 0.05) * 30)
        
        if player:
            # 缓慢向玩家靠近，但可以设置一个距离，比如离玩家 200 像素就不靠近了
            distance_x = abs(self.rect.centerx - player.rect.centerx)
            if distance_x > 300:
                if self.rect.centerx < player.rect.centerx:
                    self.rect.x += self.speed
                elif self.rect.centerx > player.rect.centerx:
                    self.rect.x -= self.speed
                
            # 【核心修改】远程射击逻辑
            self.shoot_timer += 1
            if self.shoot_timer >= 120:  # 假设 60FPS，120 帧等于 2 秒发射一次
                self.shoot_timer = 0
                
                # 实例化一根毒刺，起点是飞蛾的底部，目标是玩家的中心点
                spike = MothSpike(self.rect.centerx, self.rect.bottom, player.rect.centerx, player.rect.centery)
                
                # 最巧妙的一步：把这根毒刺自动加入到飞蛾所在的组（也就是 main.py 里的 enemies 组）
                for group in self.groups():
                    group.add(spike)

class MothSpike(pygame.sprite.Sprite):
    """飞蛾发射的毒刺子弹"""
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((12, 12))
        self.image.fill((200, 255, 50))  # 亮黄绿色的毒刺
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 1  # 血量只有1，意味着玩家可以用子弹或近战把它打烂！
        
        # 计算飞向玩家的 X 和 Y 轴速度
        angle = math.atan2(target_y - y, target_x - x)
        speed = 5  # 子弹飞行速度
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, player):
        # 让子弹飞
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # 伤害判定：如果打中了玩家
        if player and self.rect.colliderect(player.rect):
            player.take_damage(5) 
            print("📌 玩家被飞蛾毒刺击中，扣除 5 点 HP!")
            self.kill()  # 击中后销毁子弹
            
        # 垃圾回收：如果子弹飞出屏幕边界（比如掉进沼泽或飞向天空），自动销毁防止卡顿
        if self.rect.y > 800 or self.rect.x < -500 or self.rect.x > 2500:
            self.kill()

class PoisonToad(pygame.sprite.Sprite):
    """怪物 3: 跳跃突击者"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((35, 35))
        self.image.fill((0, 100, 100)) 
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.hp = 20
        self.ground_y = y
        
        self.vy = 0
        self.jump_timer = 0
        self.is_jumping = False
        
        self.attack_timer = 0
        self.attack_damage = 8

        # ==========================================
        # 【在这里统一管理跳跃和猛扑参数】
        # ==========================================
        self.pounce_distance = 200  # 核心：改变这个数字就能直接调整扑击的水平距离！
        self.jump_force = -10      # 顺便提一句：改变这个数字可以调整跳跃的高度（负数代表向上）
        # ==========================================

    def update(self, player):
        # 1. 简易重力系统
        self.vy += 0.5
        self.rect.y += self.vy
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vy = 0
            self.is_jumping = False

        # 2. 蓄力跳跃逻辑
        if not self.is_jumping:
            self.jump_timer += 1
            if self.jump_timer > 90:  # 蓄力 1.5 秒
                self.vy = self.jump_force   # 使用变量控制跳跃高度
                self.is_jumping = True
                self.jump_timer = 0
                
                # 使用变量灵活控制朝向玩家猛扑的水平位移
                if player:
                    if self.rect.centerx < player.rect.centerx:
                        self.rect.x += self.pounce_distance
                    else:
                        self.rect.x -= self.pounce_distance
                        
        # 3. 伤害检测核心逻辑 (保持不变)
        if player:
            if self.rect.colliderect(player.rect):
                self.attack_timer += 1
                if self.attack_timer >= 45:  
                    player.take_damage(self.attack_damage) 
                    print(f"🐸 玩家被毒蟾蜍撞击，扣除 {self.attack_damage} 点 HP!")
                    self.attack_timer = 0
            else:
                self.attack_timer = 0