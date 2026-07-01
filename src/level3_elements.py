import pygame
import math
import os

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
    """怪物 1: 兽人步兵 (分离式 PNG 动画加载)"""
    def __init__(self, x, y):
        super().__init__()
        
        self.state = 'walk'            
        self.facing_right = False      
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'hurt': [], 'dead': []}
        self.frame_index = 0           
        self.animation_speed = 0.2     
        
        self.load_animations(base_path="assets/sprites/enemies/")
        
        self.image = self.animations[self.state][self.frame_index]
        
        # 【视觉修复 1：解决悬空问题】
        # 图片下方有大量透明留白，我们需要把它的物理碰撞框强行往下平移 (补偿视觉差)
        self.y_offset = 15  # 如果他还是悬空，把数字加大；如果陷进土里了，把数字减小！
        self.rect = self.image.get_rect(bottomleft=(x, y + self.y_offset))

        self.hp = 30
        self.last_hp = 30              
        self.speed = 1.5
        self.attack_damage = 5

        self.is_hurt = False
        self.is_dead = False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.has_dealt_damage = False  

    def load_animations(self, base_path):
        """处理单独的 PNG 序列图"""
        
        # 配置每个动作对应的【文件名】和【总帧数】
        animation_config = {
            'idle':   {'file': 'Idle.png', 'frames': 5},
            'walk':   {'file': 'Walk.png', 'frames': 7},
            'attack': {'file': 'Attack_1.png', 'frames': 4},
            'hurt':   {'file': 'Hurt.png', 'frames': 2},
            'dead':   {'file': 'Dead.png', 'frames': 4}
        }

        scale = 1.2 # 放大倍数
        
        for state, info in animation_config.items():
            path = os.path.join(base_path, info['file'])
            
            if os.path.exists(path):
                sheet = pygame.image.load(path).convert_alpha()
                
                frame_width = sheet.get_width() // info['frames']
                frame_height = sheet.get_height()
                
                for i in range(info['frames']):
                    img = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA).convert_alpha()
                    img.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
                    img = pygame.transform.scale(img, (int(frame_width * scale), int(frame_height * scale)))
                    self.animations[state].append(img)
            else:
                print(f"⚠️ 找不到图片 {path}，使用默认红色方块代替")
                frame_width, frame_height = 100, 100
                for i in range(info['frames']):
                    img = pygame.Surface((int(frame_width * scale), int(frame_height * scale)))
                    img.fill((200, 50, 50))
                    self.animations[state].append(img)

    def update_animation(self):
        self.frame_index += self.animation_speed
        
        # --- 死亡处理逻辑 ---
        if self.state == 'dead':
            # 如果播放到了死亡动画的最后一帧
            if self.frame_index >= len(self.animations['dead']):
                self.frame_index = len(self.animations['dead']) - 1 # 锁在最后一帧
                # 【新增】这里不立刻 kill()，而是把逻辑交给一个定时器
                if not hasattr(self, 'dead_timer'):
                    self.dead_timer = 0
                self.dead_timer += 1
                if self.dead_timer >= 120: # 躺 120 帧（2秒）后再消失
                    self.kill()          
            # 渲染代码...
            self.image = self.animations['dead'][int(self.frame_index)]
            return # 确保后面不会再运行其他代码
        
        if self.frame_index >= len(self.animations[self.state]):
            if self.is_dead:
                self.frame_index = len(self.animations[self.state]) - 1
                self.kill() 
            elif self.is_hurt:
                self.is_hurt = False
                self.state = 'walk'
                self.frame_index = 0
            elif self.state == 'attack':
                self.is_attacking = False
                self.has_dealt_damage = False
                self.state = 'idle'
                self.attack_cooldown = 45  
                self.frame_index = 0
            else:
                self.frame_index = 0 

        image = self.animations[self.state][int(self.frame_index)]
        
        if not self.facing_right:
            self.image = pygame.transform.flip(image, True, False)
        else:
            self.image = image

    def update(self, player):
        # 1. 核心：如果已经死亡，直接锁死在死亡状态，禁止执行任何其他逻辑！
        if self.is_dead:
            self.update_animation() # 只播放动画，不执行AI
            return # 【关键】直接跳出函数，后面所有的移动、攻击检测全都不跑了

        # 1. 受击判定
        if self.hp < self.last_hp and not self.is_dead:
            if self.hp <= 0:
                self.is_dead = True
                self.state = 'dead'
                self.frame_index = 0 # 确保从死亡的第一帧开始
            else:
                self.is_hurt = True
                self.state = 'hurt'
                self.frame_index = 0
            self.last_hp = self.hp

        # 2. AI 行为逻辑
        if not self.is_hurt:
            # 【逻辑修复 2：状态锁定】一旦开始攻击，无视其他所有指令，直到动画自然播放完毕！
            if self.state == 'attack':
                pass 
            # 攻击处于冷却状态
            elif self.attack_cooldown > 0:
                self.attack_cooldown -= 1
                if self.state != 'idle':
                    self.state = 'idle'
                    self.frame_index = 0
            # 正常思考状态
            else:
                if player:
                    if self.rect.centerx < player.rect.centerx:
                        self.facing_right = True
                    else:
                        self.facing_right = False
                        
                    distance = abs(self.rect.centerx - player.rect.centerx)
                    
                    if distance <= 60: 
                        # 【逻辑修复 3：重置帧】切入攻击时，强制从第 0 帧开始！
                        self.state = 'attack'
                        self.frame_index = 0
                        self.has_dealt_damage = False
                    else: 
                        if self.state != 'walk':
                            self.state = 'walk'
                            self.frame_index = 0
                            
                        if self.facing_right:
                            self.rect.x += self.speed
                        else:
                            self.rect.x -= self.speed

        # 3. 动画驱动伤害
        # 当动画播放到挥刀那一帧 (第 3 帧) 造成伤害
        if self.state == 'attack' and int(self.frame_index) == 3 and not self.has_dealt_damage:
            if player and self.rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                print(f"🪓 兽人重砍！造成 {self.attack_damage} 点伤害！")
            self.has_dealt_damage = True

        self.update_animation()

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