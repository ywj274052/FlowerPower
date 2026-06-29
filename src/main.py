import pygame
import sys
import math
import random
from settings import *
from player import Player, SeedShot

# ---------- 全局变量 ----------
game_state = "TITLE"
tutorial_timer = 0 
show_tutorial = True  

# ---------- 彗星类 ----------
class Comet(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 彗星大小
        self.size = 60
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        # 初始位置：屏幕右上角外部
        self.rect.x = SCREEN_WIDTH + 50
        self.rect.y = -100
        
        # 速度
        self.vx = -6
        self.vy = 4
        
        # 旋转角度
        self.angle = 0
        self.rotation_speed = 5  # 每帧旋转角度
        
        # 是否已经撞击
        self.has_crashed = False
        
        # ⭐ 拖尾粒子
        self.tail_particles = []
        
        # 更新彗星图像
        self.update_image()

    def update_image(self):
        """根据当前角度绘制彗星"""
        # 清空表面
        self.image.fill((0, 0, 0, 0))
        
        center_x = self.size
        center_y = self.size
        
        # ----- 彗星头部（发光的球） -----
        # 外发光
        for radius in range(30, 0, -3):
            alpha = 30 + int(40 * (radius / 30))
            color = (255, 200, 50, alpha)
            pygame.draw.circle(self.image, color, (center_x, center_y), radius)
        
        # 核心
        pygame.draw.circle(self.image, (255, 255, 220), (center_x, center_y), 20)
        pygame.draw.circle(self.image, (255, 220, 100), (center_x, center_y), 14)
        pygame.draw.circle(self.image, (255, 255, 255), (center_x, center_y), 8)
        
        # 高光
        pygame.draw.circle(self.image, (255, 255, 255, 150), (center_x - 6, center_y - 6), 5)
        
        # ----- 彗星尾巴（拖尾） -----
        # 主尾巴 - 三角形
        tail_length = 80
        tail_width_start = 25
        tail_width_end = 5
        
        # 尾巴方向：指向彗星运动方向的反方向
        # 因为彗星向右下飞，尾巴在左上方
        points = [
            (center_x, center_y),  # 尾部起点（彗星位置）
            (center_x - tail_length, center_y - tail_width_start),  # 尾巴上侧
            (center_x - tail_length - 20, center_y),  # 尾巴末端
            (center_x - tail_length, center_y + tail_width_start)  # 尾巴下侧
        ]
        
        # 主尾巴（半透明）
        pygame.draw.polygon(self.image, (255, 200, 50, 120), points)
        
        # 内层尾巴（更亮）
        inner_points = [
            (center_x - 10, center_y),
            (center_x - tail_length + 20, center_y - tail_width_start // 2),
            (center_x - tail_length, center_y),
            (center_x - tail_length + 20, center_y + tail_width_start // 2)
        ]
        pygame.draw.polygon(self.image, (255, 255, 200, 150), inner_points)
        
        # 尾巴光晕（细长发光）
        for i in range(3):
            alpha = 60 - i * 15
            offset = i * 15
            glow_points = [
                (center_x - offset, center_y),
                (center_x - tail_length - offset, center_y - tail_width_start + i * 4),
                (center_x - tail_length - 10 - offset, center_y),
                (center_x - tail_length - offset, center_y + tail_width_start - i * 4)
            ]
            pygame.draw.polygon(self.image, (255, 150, 50, alpha), glow_points)
        
        # ----- 旋转整个彗星 -----
        # 保存中心点
        center = (self.size, self.size)
        # 旋转
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        # 获取旋转后的矩形
        rotated_rect = rotated_image.get_rect(center=center)
        # 创建新表面
        new_image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        new_image.blit(rotated_image, rotated_rect.topleft)
        self.image = new_image

    def update(self):
        """更新彗星位置、旋转和拖尾"""
        if not self.has_crashed:
            # 移动
            self.rect.x += self.vx
            self.rect.y += self.vy
            
            # 旋转
            self.angle += self.rotation_speed
            if self.angle > 360:
                self.angle -= 360
            
            # 更新图像（旋转）
            self.update_image()
            
            # 生成拖尾粒子
            for _ in range(5):
                # 粒子在彗星尾部位置
                tail_x = self.rect.centerx - self.vx * 2 + random.randint(-15, 15)
                tail_y = self.rect.centery - self.vy * 2 + random.randint(-15, 15)
                self.tail_particles.append({
                    'x': tail_x,
                    'y': tail_y,
                    'life': random.randint(20, 40),
                    'max_life': 40,
                    'size': random.randint(4, 12),
                    'speed_x': random.uniform(-1, 1),
                    'speed_y': random.uniform(0.5, 2),
                    'color': random.choice([
                        (255, 200, 50),
                        (255, 150, 50),
                        (255, 100, 50),
                        (255, 200, 100)
                    ])
                })
            
            # 更新粒子
            for p in self.tail_particles[:]:
                p['life'] -= 1
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                p['size'] *= 0.97  # 逐渐缩小
                if p['life'] <= 0 or p['size'] < 0.5:
                    self.tail_particles.remove(p)
            
            # 限制粒子数量
            if len(self.tail_particles) > 200:
                self.tail_particles = self.tail_particles[-150:]
            
            # 检测是否撞击地面
            if self.rect.bottom >= GROUND_Y:
                self.has_crashed = True
                self.rect.bottom = GROUND_Y
                return "CRASH"
        
        return None

    def draw_tail(self, screen):
        """绘制彗星拖尾"""
        for p in self.tail_particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            color = (p['color'][0], p['color'][1], p['color'][2], alpha)
            size = max(1, p['size'])
            # 发光效果
            pygame.draw.circle(screen, color[:3], (int(p['x']), int(p['y'])), int(size))
            if size > 3:
                glow_color = (255, 200, 100, alpha // 3)
                pygame.draw.circle(screen, glow_color[:3], (int(p['x']), int(p['y'])), int(size * 2))

# ---------- 绘制函数 ----------
def draw_title_screen(screen):
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((34, 139, 34))
    screen.blit(background, (0, 0))
    
    try:
        title_font = pygame.font.Font(None, 180)
        subtitle_font = pygame.font.Font(None, 80)
        prompt_font = pygame.font.Font(None, 50)
    except:
        title_font = pygame.font.SysFont("Arial", 180)
        subtitle_font = pygame.font.SysFont("Arial", 80)
        prompt_font = pygame.font.SysFont("Arial", 50)
    
    title_text = title_font.render("FlowerPower", True, (255, 255, 255))
    shadow_text = title_font.render("FlowerPower", True, (0, 0, 0))
    shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH // 2 + 5, 255))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
    screen.blit(shadow_text, shadow_rect)
    screen.blit(title_text, title_rect)
    
    subtitle_text = subtitle_font.render("Bloom Guardian", True, (255, 215, 0))
    subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
    screen.blit(subtitle_text, subtitle_rect)
    
    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 500)))
    prompt_text = prompt_font.render("Press ENTER to Start", True, (255, 255, 200))
    prompt_text.set_alpha(alpha)
    prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 480))
    screen.blit(prompt_text, prompt_rect)
    
    draw_flower(screen, 150, SCREEN_HEIGHT - 100, (255, 200, 50))
    draw_flower(screen, 200, SCREEN_HEIGHT - 150, (255, 100, 150))
    draw_flower(screen, SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100, (255, 200, 50))
    draw_flower(screen, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150, (255, 100, 150))


def draw_flower(screen, x, y, color):
    pygame.draw.circle(screen, color, (x, y - 12), 10)
    pygame.draw.circle(screen, color, (x + 12, y), 10)
    pygame.draw.circle(screen, color, (x, y + 12), 10)
    pygame.draw.circle(screen, color, (x - 12, y), 10)
    pygame.draw.circle(screen, (255, 255, 0), (x, y), 8)


def draw_comet_scene(screen, comet, background):
    """绘制彗星坠落场景"""
    screen.blit(background, (0, 0))
    pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
    pygame.draw.rect(screen, BROWN, (0, GROUND_Y, SCREEN_WIDTH, 5))
    
    # 先画拖尾粒子
    comet.draw_tail(screen)
    
    # 再画彗星本体
    screen.blit(comet.image, comet.rect)
    
    try:
        font = pygame.font.Font(None, 40)
    except:
        font = pygame.font.SysFont("Arial", 40)
    
    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 300)))
    warning_text = font.render("⚠️ A Blight Comet is falling!", True, (255, 100, 100))
    warning_text.set_alpha(alpha)
    warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(warning_text, warning_rect)


def draw_shake_effect(screen, background, comet, shake_frames):
    """绘制屏幕震动效果"""
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    
    screen.blit(background, (offset_x, offset_y))
    pygame.draw.rect(screen, GREEN, (offset_x, GROUND_Y + offset_y, SCREEN_WIDTH, GROUND_HEIGHT))
    pygame.draw.rect(screen, BROWN, (offset_x, GROUND_Y + offset_y, SCREEN_WIDTH, 5))
    
    # 画拖尾和彗星
    comet.draw_tail(screen)
    screen.blit(comet.image, (comet.rect.x + offset_x, comet.rect.y + offset_y))
    
    flash_alpha = min(255, (60 - shake_frames) * 8)
    if flash_alpha > 0:
        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        flash.fill((255, 255, 255))
        flash.set_alpha(flash_alpha // 2)
        screen.blit(flash, (0, 0))
    
    try:
        font = pygame.font.Font(None, 60)
    except:
        font = pygame.font.SysFont("Arial", 60)
    
    if shake_frames > 30:
        impact_text = font.render("💥 CRASH!", True, (255, 200, 50))
        impact_rect = impact_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(impact_text, impact_rect)


def draw_ui(screen, player):
    """绘制UI（HP条、弹药、飞行能量）"""
    try:
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
    except:
        font = pygame.font.SysFont("Arial", 36)
        small_font = pygame.font.SysFont("Arial", 24)
    
    # ==========================================
    # ⭐ HP 条
    # ==========================================
    hp_bar_width = 300
    hp_bar_height = 25
    hp_bar_x = 20
    hp_bar_y = 20
    
    # 背景
    pygame.draw.rect(screen, (50, 50, 50), (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
    
    # HP 颜色（绿色 → 黄色 → 红色）
    hp_progress = player.get_hp_progress()
    if hp_progress > 0.5:
        color = (0, 255, 0)  # 绿色
    elif hp_progress > 0.25:
        color = (255, 255, 0)  # 黄色
    else:
        color = (255, 0, 0)  # 红色
    
    # 填充
    fill_width = int(hp_bar_width * hp_progress)
    pygame.draw.rect(screen, color, (hp_bar_x + 2, hp_bar_y + 2, fill_width - 4, hp_bar_height - 4))
    
    # 边框
    pygame.draw.rect(screen, WHITE, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 2)
    
    # HP 文字
    hp_text = font.render(f"❤️ HP: {player.hp}/{player.max_hp}", True, WHITE)
    screen.blit(hp_text, (hp_bar_x + 10, hp_bar_y + 2))
    
    # HP 百分比（右侧）
    percent_text = small_font.render(f"{player.get_hp_percent()}%", True, WHITE)
    percent_rect = percent_text.get_rect(right=hp_bar_x + hp_bar_width - 10, centery=hp_bar_y + hp_bar_height // 2)
    screen.blit(percent_text, percent_rect)
    
    # ==========================================
    # 飞行能量条（放在 HP 条下方）
    # ==========================================
    fly_bar_width = 150
    fly_bar_height = 15
    fly_bar_x = 20
    fly_bar_y = hp_bar_y + hp_bar_height + 10
    
    pygame.draw.rect(screen, (50, 50, 50), (fly_bar_x, fly_bar_y, fly_bar_width, fly_bar_height))
    
    fly_progress = player.get_fly_progress()
    if fly_progress > 0:
        fill_width = int(fly_bar_width * fly_progress)
        if fly_progress < 0.5:
            color = BLUE
        else:
            color = (255, 200, 0)
        pygame.draw.rect(screen, color, (fly_bar_x + 2, fly_bar_y + 2, fill_width - 4, fly_bar_height - 4))
    
    pygame.draw.rect(screen, WHITE, (fly_bar_x, fly_bar_y, fly_bar_width, fly_bar_height), 2)
    fly_text = small_font.render("✈️ FLY", True, WHITE)
    screen.blit(fly_text, (fly_bar_x + 5, fly_bar_y - 1))
    
    # 飞行状态
    if player.is_flying:
        status_text = small_font.render("✈️ FLYING", True, (100, 200, 255))
        screen.blit(status_text, (fly_bar_x + fly_bar_width + 10, fly_bar_y - 2))
    
    # ==========================================
    # 种子弹药
    # ==========================================
    seed_y = fly_bar_y + fly_bar_height + 15
    seed_text = font.render(f"🌱 Seeds: {player.seed_count}/{SEED_SHOT_MAX}", True, WHITE)
    screen.blit(seed_text, (20, seed_y))
    
    # ==========================================
    # 回血状态
    # ==========================================
    if player.is_healing:
        heal_text = small_font.render("💚 Healing...", True, LIGHT_GREEN)
        screen.blit(heal_text, (20, seed_y + 35))
    
    # ==========================================
    # 受伤闪红边框（低血量时）
    # ==========================================
    if player.get_hp_progress() < 0.25 and not player.is_healing:
        # 红色闪烁警告边框
        alpha = 50 + int(50 * abs(pygame.time.get_ticks() / 200 % 2 - 1))
        warning = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        warning.fill((255, 0, 0, alpha))
        screen.blit(warning, (0, 0))

def draw_tutorial_text(screen):
    """绘制教程文字（游戏开始时显示）"""
    try:
        font = pygame.font.Font(None, 32)
        small_font = pygame.font.Font(None, 24)
    except:
        font = pygame.font.SysFont("Arial", 32)
        small_font = pygame.font.SysFont("Arial", 24)
    
    # 半透明背景
    bg_width = 400
    bg_height = 180
    bg_x = SCREEN_WIDTH // 2 - bg_width // 2
    bg_y = SCREEN_HEIGHT - 200
    
    # 背景框
    bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 160))
    pygame.draw.rect(bg_surface, (255, 255, 255, 60), (0, 0, bg_width, bg_height), 2)
    screen.blit(bg_surface, (bg_x, bg_y))
    
    # 标题
    title_text = font.render("🎮 Controls", True, (255, 215, 0))
    screen.blit(title_text, (bg_x + 20, bg_y + 10))
    
    # 操作提示
    controls = [
        ("←/→", "Move"),
        ("Space", "Jump"),
        ("W", "Fly"),
        ("X", "Seed Shot (Ranged)")
    ]
    
    y_offset = 50
    for key, action in controls:
        # 按键（金色）
        key_text = small_font.render(key, True, (255, 200, 50))
        screen.blit(key_text, (bg_x + 20, bg_y + y_offset))
        
        # 动作（白色）
        action_text = small_font.render(f"→ {action}", True, (220, 220, 220))
        screen.blit(action_text, (bg_x + 100, bg_y + y_offset))
        
        y_offset += 25
    
    # 闪烁提示：按 H 测试受伤
    alpha = 100 + int(155 * abs(math.sin(pygame.time.get_ticks() / 500)))
    hint_text = small_font.render("Press H to test damage", True, (255, 100, 100))
    hint_text.set_alpha(alpha)
    screen.blit(hint_text, (bg_x + 20, bg_y + y_offset + 5))       

def draw_game_over_screen(screen, player):
    """绘制 Game Over 画面"""
    # 半透明黑色遮罩
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(180)
    screen.blit(overlay, (0, 0))
    
    try:
        title_font = pygame.font.Font(None, 120)
        big_font = pygame.font.Font(None, 80)
        medium_font = pygame.font.Font(None, 50)
        small_font = pygame.font.Font(None, 36)
    except:
        title_font = pygame.font.SysFont("Arial", 120)
        big_font = pygame.font.SysFont("Arial", 80)
        medium_font = pygame.font.SysFont("Arial", 50)
        small_font = pygame.font.SysFont("Arial", 36)
    
    # GAME OVER 标题
    game_over_text = title_font.render("GAME OVER", True, RED)
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(game_over_text, game_over_rect)
    
    # 死亡信息
    dead_text = big_font.render("💀 You have died!", True, WHITE)
    dead_rect = dead_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
    screen.blit(dead_text, dead_rect)
    
    # 最终 HP
    hp_text = medium_font.render(f"HP: {player.hp} / {player.max_hp}", True, RED)
    hp_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
    screen.blit(hp_text, hp_rect)
    
    # 重新开始提示（闪烁）
    alpha = 128 + int(127 * abs(math.sin(pygame.time.get_ticks() / 400)))
    restart_text = medium_font.render("Press R to Restart", True, (255, 255, 200))
    restart_text.set_alpha(alpha)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
    screen.blit(restart_text, restart_rect)
    
    # 退出提示
    quit_text = small_font.render("Press ESC to Quit", True, (128, 128, 128))
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, 560))
    screen.blit(quit_text, quit_rect)


# ---------- 主函数 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("FlowerPower")
    clock = pygame.time.Clock()
    
    global game_state, tutorial_timer, show_tutorial 

    tutorial_timer = 0
    show_tutorial = True
    
    background = pygame.image.load(BACKGROUND_FILE).convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    
    player = None
    comet = None
    shake_frames = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # ⭐ Game Over 状态：按 R 重启
                if game_state == "GAME_OVER" and event.key == pygame.K_r:
                    print("🔄 重新开始游戏！")
                    game_state = "TITLE"
                    player = None
                    comet = None

                if event.key == pygame.K_h and game_state == "PLAYING":
                    if player:
                        result = player.take_damage(10)
                        if result == "GAME_OVER":
                            print("💀 玩家死亡！游戏结束！")
                            game_state = "GAME_OVER"  # ⭐ 切换到 Game Over 状态
                
                if game_state == "TITLE" and event.key == pygame.K_RETURN:
                    print("☄️ 彗星坠落事件启动！")
                    game_state = "COMET"
                    comet = Comet()
                    player = Player(100, GROUND_Y - 128)
        
        # ----- 更新 -----
        if game_state == "COMET":
            if comet:
                result = comet.update()
                if result == "CRASH":
                    print("💥 彗星撞击地面！屏幕震动！")
                    game_state = "SHAKE"
                    shake_frames = 60
        
        elif game_state == "SHAKE":
            shake_frames -= 1
            if shake_frames <= 0:
                print("🎮 游戏开始！")
                game_state = "PLAYING"
        
        elif game_state == "PLAYING":
            if player:
                player.update()

                if show_tutorial:
                    tutorial_timer += 1
                    if tutorial_timer >= 300:  # 5秒（60fps × 5）
                        show_tutorial = False
                # 如果玩家死亡，切换到 Game Over
                if player.is_dead:
                    game_state = "GAME_OVER"
        
        # ----- 渲染 -----
        if game_state == "TITLE":
            draw_title_screen(screen)
        
        elif game_state == "COMET":
            if comet:
                draw_comet_scene(screen, comet, background)
        
        elif game_state == "SHAKE":
            if comet:
                draw_shake_effect(screen, background, comet, shake_frames)
        
        elif game_state == "PLAYING":
            screen.blit(background, (0, 0))
            pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
            
            if player:
                for seed in player.seed_shots:
                    seed.draw_trail(screen)
                for seed in player.seed_shots:
                    screen.blit(seed.image, seed.rect)
                player.draw_heal_particles(screen)
                screen.blit(player.image, player.rect)
                if player.is_attacking:
                    hitbox = player.create_attack_hitbox()
                    pygame.draw.rect(screen, RED, hitbox, 2)
                draw_ui(screen, player)

                 # 画教程文字（游戏开始时显示）
                if show_tutorial:
                    draw_tutorial_text(screen)
        
        #  Game Over 画面 
        elif game_state == "GAME_OVER":
            # 保留游戏背景
            screen.blit(background, (0, 0))
            pygame.draw.rect(screen, GREEN, (0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT))
            if player:
                screen.blit(player.image, player.rect)
            draw_game_over_screen(screen, player)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
