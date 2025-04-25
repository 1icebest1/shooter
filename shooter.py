import pygame
import os
import random
import math
from dataclasses import dataclass

pygame.init()

WIDTH = 1200
HEIGHT = 800
CELL_SIZE = 100
CHUNK_SIZE = 10 * CELL_SIZE
MAX_SLIMES = 100
SPAWN_INTERVAL = 2000
DAMAGE_INTERVAL = 1000

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("test nazar jak proekt")

def draw_message_box(screen, lines, x, y, width, height):
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height))
    pygame.draw.rect(screen, (200, 200, 200), (x, y, width, height), 3)
    font = pygame.font.Font(None, 36)
    total_height = len(lines) * font.get_height()
    current_y = y + (height - total_height) // 2
    for line in lines:
        text_surface = font.render(line, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + width // 2, current_y))
        screen.blit(text_surface, text_rect)
        current_y += font.get_height()

def is_wall(x, y, width, height):
    x = int(x)
    y = int(y)
    left = x // CELL_SIZE
    right = (x + width) // CELL_SIZE
    top = y // CELL_SIZE
    bottom = (y + height) // CELL_SIZE

    for cell_y in range(int(top), int(bottom) + 1):
        for cell_x in range(int(left), int(right) + 1):
            grid_x = cell_x * CELL_SIZE
            grid_y = cell_y * CELL_SIZE
            if world_map.get((grid_x, grid_y), 0) == 1:
                wall_zone = grid_y + CELL_SIZE * 0.3
                if y + height > grid_y and y < wall_zone:
                    return True
    return False

@dataclass
class HealthSystem:
    max_hearts: int
    current_hearts: int
    last_damage_time: int = 0

    def take_damage(self, amount):
        if pygame.time.get_ticks() - self.last_damage_time > DAMAGE_INTERVAL:
            self.current_hearts = max(0, self.current_hearts - amount)
            self.last_damage_time = pygame.time.get_ticks()

class Camera:
    def __init__(self, map_size):
        self.x = 0
        self.y = 0
        self.width = WIDTH
        self.height = HEIGHT
        self.map_width, self.map_height = map_size

    def apply(self, pos):
        return (pos[0] - self.x, pos[1] - self.y)

    def update(self, target):
        self.x = target.x + target.width // 2 - self.width // 2
        self.y = target.y + target.height // 2 - self.height // 2
        self.x = max(0, min(self.x, self.map_width - self.width))
        self.y = max(0, min(self.y, self.map_height - self.height))

class Player:
    def __init__(self, map_size):
        self.width = 60
        self.height = 80
        self.speed = 5
        self.map_width, self.map_height = map_size
        self.x = (10 * 10 * CELL_SIZE) // 2 - self.width // 2
        self.y = (10 * 10 * CELL_SIZE) // 2 - self.height // 2
        self.health = HealthSystem(5, 5)

@dataclass
class WeaponConfig:
    name: str
    damage: int
    fire_rate: float
    bullet_speed: int
    bullet_size: int
    bullet_color: tuple
    ammo_capacity: int
    spread: float = 0.0

class Weapon:
    def __init__(self, config, texture):
        self.config = config
        self.texture = texture
        self.max_ammo = config.ammo_capacity * 5
        self.current_ammo = config.ammo_capacity
        self.last_shot = 0

    def can_shoot(self):
        now = pygame.time.get_ticks()
        return (now - self.last_shot) > 1000 / self.config.fire_rate

    def shoot(self):
        if self.current_ammo > 0 and self.can_shoot():
            self.current_ammo -= 1
            self.last_shot = pygame.time.get_ticks()
            return True
        return False

    def add_ammo(self, amount):
        self.current_ammo = min(self.current_ammo + amount, self.max_ammo)

class Bullet:
    def __init__(self, x, y, direction, config):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = config.bullet_speed
        self.radius = config.bullet_size
        self.color = config.bullet_color
        self.damage = config.damage
        self.spread = random.uniform(-config.spread, config.spread)

class Item:
    def __init__(self, x, y, texture, original=None):
        self.x = x
        self.y = y
        self.texture = texture
        self.width = 30
        self.height = 30
        self.original = original

class AmmoItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, textures['ammo'])
        self.amount = 10

class Inventory:
    def __init__(self):
        self.slots = [None] * 5
        self.selected = -1
        self.pos = (50, 30)
        self.slot_size = 50

    def add_item(self, item):
        if isinstance(item, AmmoItem):
            for slot in self.slots:
                if isinstance(slot, Weapon):
                    slot.add_ammo(item.amount)
                    return True
            return False
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = item
                return True
        return False

    def remove_item(self, slot):
        if 0 <= slot < len(self.slots):
            removed_item = self.slots[slot]
            self.slots[slot] = None
            return removed_item
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, (40, 40, 40), (self.pos[0] - 20, self.pos[1] - 20, 330, 90))
        for i in range(5):
            x = self.pos[0] + i * (self.slot_size + 10)
            y = self.pos[1]
            color = (200, 200, 0) if i == self.selected else (100, 100, 100)
            pygame.draw.rect(screen, color, (x, y, self.slot_size, self.slot_size), 3)
            if self.slots[i]:
                item = self.slots[i]
                if isinstance(item, Weapon):
                    screen.blit(pygame.transform.scale(item.texture, (40, 40)), (x + 5, y + 5))
                    font = pygame.font.Font(None, 18)
                    text = font.render(str(item.current_ammo), True, (255, 255, 255))
                    screen.blit(text, (x + 35, y + 35))
                else:
                    screen.blit(pygame.transform.scale(item.texture, (30, 30)), (x + 10, y + 10))

class Slime:
    ANIMATIONS = {'up': [], 'down': [], 'left': [], 'right': []}
    ANIMATION_SPEED = 15
    DETECTION_RADIUS = 3 * CHUNK_SIZE

    @classmethod
    def load_textures(cls):
        directions = ['up', 'down', 'left', 'right']
        for direction in directions:
            cls.ANIMATIONS[direction] = [
                pygame.transform.scale(
                    pygame.image.load(f"slime/{direction}/slime{i}.png").convert_alpha(),
                    (60, 80))
                for i in range(1, 5)
            ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.direction = random.choice(["up", "down", "left", "right"])
        self.move_counter = 0
        self.anim_counter = 0
        self.anim_frame = 0
        self.width = 60
        self.height = 80
        self.health = HealthSystem(3, 3)
        self.is_chasing = False

    def move(self, player_x, player_y):
        self.move_counter += 1
        self.anim_counter += 1

        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.hypot(dx, dy)

        if distance < self.DETECTION_RADIUS:
            self.is_chasing = True
            if distance > 50:
                norm = math.hypot(dx, dy) or 1
                move_x = dx / norm * self.speed
                move_y = dy / norm * self.speed

                prev_x, prev_y = self.x, self.y
                self.x += move_x
                self.y += move_y

                if is_wall(self.x, self.y, self.width, self.height):
                    self.x, self.y = prev_x, prev_y
                    self.direction = random.choice(["up", "down", "left", "right"])
                else:
                    if abs(move_x) > abs(move_y):
                        self.direction = "right" if move_x > 0 else "left"
                    else:
                        self.direction = "down" if move_y > 0 else "up"
        else:
            self.is_chasing = False
            if self.move_counter % 100 == 0:
                self.direction = random.choice(["up", "down", "left", "right"])

            if self.move_counter % 5 == 0:
                prev_x, prev_y = self.x, self.y
                if self.direction == "up":
                    self.y -= self.speed
                elif self.direction == "down":
                    self.y += self.speed
                elif self.direction == "left":
                    self.x -= self.speed
                elif self.direction == "right":
                    self.x += self.speed

                if is_wall(self.x, self.y, self.width, self.height):
                    self.x, self.y = prev_x, prev_y
                    self.direction = random.choice(["up", "down", "left", "right"])

        if self.anim_counter % self.ANIMATION_SPEED == 0:
            self.anim_frame = (self.anim_frame + 1) % 4

    def draw(self, screen, camera):
        screen.blit(self.ANIMATIONS[self.direction][self.anim_frame], camera.apply((self.x, self.y)))
        for i in range(self.health.current_hearts):
            heart_pos = camera.apply((self.x + i * 20 - 15, self.y - 30))
            screen.blit(textures['heart'], heart_pos)

textures = {
    'grass1': pygame.transform.scale(pygame.image.load("texture/land/grass1.png").convert(), (CELL_SIZE, CELL_SIZE)),
    'grass2': pygame.transform.scale(pygame.image.load("texture/land/grass2.png").convert(), (CELL_SIZE, CELL_SIZE)),
    'flower': pygame.transform.scale(pygame.image.load("texture/decor/flower.png").convert_alpha(), (40, 30)),
    'rock': pygame.transform.scale(pygame.image.load("texture/decor/rock.png").convert_alpha(), (50, 50)),
    'pistol': pygame.transform.scale(pygame.image.load("texture/weapons/pistol.png").convert_alpha(), (80, 60)),
    'ak47': pygame.transform.scale(pygame.image.load("texture/weapons/ak-47.png").convert_alpha(), (100, 50)),
    'red_orb': pygame.transform.scale(pygame.image.load("texture/items/red_orb.png").convert_alpha(), (30, 30)),
    'heart': pygame.transform.scale(pygame.image.load("texture/items/heart.png").convert_alpha(), (30, 30)),
    'ammo': pygame.transform.scale(pygame.image.load("texture/items/ammo.png").convert_alpha(), (30, 30))
}

WEAPONS = {
    'pistol': WeaponConfig(name="Pistol", damage=2, fire_rate=2, bullet_speed=15, bullet_size=4,
                           bullet_color=(255, 60, 60), ammo_capacity=12, spread=0.1),
    'ak47': WeaponConfig(name="AK-47", damage=1, fire_rate=10, bullet_speed=20, bullet_size=3,
                         bullet_color=(255, 165, 0), ammo_capacity=30, spread=0.3)
}

Slime.load_textures()
MAP_SIZE = (10 * 10 * CELL_SIZE, 10 * 10 * CELL_SIZE)
world_map = {}
decorations = {}
items_on_ground = []
slimes = []
bullets = []
last_spawn_time = pygame.time.get_ticks() - SPAWN_INTERVAL

for chunk_x in range(10):
    for chunk_y in range(10):
        chunk_type = random.choices([0, 1], weights=[95, 5])[0]
        for x_in_chunk in range(10):
            for y_in_chunk in range(10):
                x = chunk_x * 10 * CELL_SIZE + x_in_chunk * CELL_SIZE
                y = chunk_y * 10 * CELL_SIZE + y_in_chunk * CELL_SIZE
                world_map[(x, y)] = random.choices([0, 1], weights=([99, 1] if chunk_type == 1 else [95, 5]))[0]

                if world_map[(x, y)] == 0:
                    spawn_chance = random.random()
                    if spawn_chance < 0.005:
                        weapon_name = random.choice(list(WEAPONS.keys()))
                        items_on_ground.append(Item(
                            x + CELL_SIZE // 2,
                            y + CELL_SIZE // 2,
                            textures[weapon_name],
                            Weapon(WEAPONS[weapon_name], textures[weapon_name])
                        ))
                    elif spawn_chance < 0.03:
                        items_on_ground.append(AmmoItem(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    elif random.random() < 0.1:
                        decorations[(x, y)] = random.choice(['flower', 'rock'])

player_frames = {
    "down": [pygame.transform.scale(pygame.image.load(f"chart/down/player{i}.png").convert_alpha(), (60, 80)) for i in range(1, 5)],
    "up": [pygame.transform.scale(pygame.image.load(f"chart/up/player{i}.png").convert_alpha(), (60, 80)) for i in range(1, 5)],
    "left": [pygame.transform.scale(pygame.image.load(f"chart/left/player{i}.png").convert_alpha(), (60, 80)) for i in range(1, 5)],
    "right": [pygame.transform.scale(pygame.image.load(f"chart/right/player{i}.png").convert_alpha(), (60, 80)) for i in range(1, 5)]
}

player = Player(MAP_SIZE)
camera = Camera(MAP_SIZE)
inventory = Inventory()
inventory.add_item(Weapon(WEAPONS['pistol'], textures['pistol']))
inventory.add_item(Weapon(WEAPONS['ak47'], textures['ak47']))

start_time = pygame.time.get_ticks()
killed_slimes = 0

running = True
clock = pygame.time.Clock()
current_frame = 0
last_update = pygame.time.get_ticks()
animation_speed = 0.15
current_direction = "down"
auto_fire = False
game_over = False
game_over_time = 0

while running:
    dt = clock.tick(60)
    screen.fill((135, 206, 235))
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if inventory.pos[1] <= my <= inventory.pos[1] + 64:
                    for i in range(5):
                        slot_x = inventory.pos[0] + i * (64 + 10)
                        if slot_x <= mx <= slot_x + 64:
                            inventory.selected = i

                if event.button == 1:
                    auto_fire = True
                if event.button == 3:
                    if inventory.selected != -1:
                        weapon = inventory.slots[inventory.selected]
                        if isinstance(weapon, Weapon):
                            if weapon.config.name != "Pistol":
                                weapon.current_ammo = weapon.config.ammo_capacity

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                auto_fire = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    for item in items_on_ground[:]:
                        distance = math.hypot(
                            player.x + player.width / 2 - (item.x + item.width / 2),
                            player.y + player.height / 2 - (item.y + item.height / 2)
                        )
                        if distance < 50:
                            if isinstance(item, Item) and isinstance(item.original, Weapon):
                                if inventory.add_item(item.original):
                                    items_on_ground.remove(item)
                                    break
                            else:
                                if inventory.add_item(item):
                                    items_on_ground.remove(item)
                                    break

                if event.key == pygame.K_q and inventory.selected != -1:
                    dropped_item = inventory.remove_item(inventory.selected)
                    if dropped_item:
                        drop_x = player.x + player.width // 2 - 15
                        drop_y = player.y + player.height // 2 - 15
                        items_on_ground.append(Item(drop_x, drop_y, dropped_item.texture, dropped_item))

    if not game_over:
        if len(slimes) < MAX_SLIMES and current_time - last_spawn_time > SPAWN_INTERVAL:
            new_x = random.randint(max(0, int(player.x) - 500), min(MAP_SIZE[0], int(player.x) + 500))
            new_y = random.randint(max(0, int(player.y) - 500), min(MAP_SIZE[1], int(player.y) + 500))
            slimes.append(Slime(new_x, new_y))
            last_spawn_time = current_time

        keys = pygame.key.get_pressed()
        prev_x, prev_y = player.x, player.y
        is_moving = False

        if keys[pygame.K_a]:
            player.x -= player.speed
            current_direction = "left"
            is_moving = True
        if keys[pygame.K_d]:
            player.x += player.speed
            current_direction = "right"
            is_moving = True
        if keys[pygame.K_w]:
            player.y -= player.speed
            current_direction = "up"
            is_moving = True
        if keys[pygame.K_s]:
            player.y += player.speed
            current_direction = "down"
            is_moving = True

        if is_wall(player.x, player.y, player.width, player.height):
            player.x, player.y = prev_x, prev_y
        player.x = max(0, min(MAP_SIZE[0] - player.width, player.x))
        player.y = max(0, min(MAP_SIZE[1] - player.height, player.y))

        if auto_fire and inventory.selected != -1:
            selected_item = inventory.slots[inventory.selected]
            if isinstance(selected_item, Weapon) and selected_item.shoot():
                angle = {"right": 0, "left": 180, "up": 90, "down": 270}[current_direction]
                radian_angle = math.radians(angle + selected_item.config.spread * 10)
                bx = player.x + player.width // 2 + math.cos(radian_angle) * 20
                by = player.y + player.height // 2 - math.sin(radian_angle) * 20
                bullets.append(Bullet(bx, by, current_direction, selected_item.config))

    camera.update(player)

    for y in range(0, MAP_SIZE[1], CELL_SIZE):
        for x in range(0, MAP_SIZE[0], CELL_SIZE):
            if (x < camera.x - CELL_SIZE
                    or x > camera.x + camera.width + CELL_SIZE
                    or y < camera.y - CELL_SIZE
                    or y > camera.y + camera.height + CELL_SIZE):
                continue

            texture = 'grass2' if world_map.get((x, y), 0) else 'grass1'
            screen.blit(textures[texture], camera.apply((x, y)))

            if (x, y) in decorations:
                decor_type = decorations[(x, y)]
                pos = (x + CELL_SIZE // 2 - 15, y + CELL_SIZE - 40)
                screen.blit(textures[decor_type], camera.apply(pos))

    for item in items_on_ground:
        screen.blit(item.texture, camera.apply((item.x, item.y)))

    for bullet in bullets[:]:
        dx = 0
        dy = 0
        speed = bullet.speed
        if bullet.direction == "right":
            dx = speed
        elif bullet.direction == "left":
            dx = -speed
        elif bullet.direction == "up":
            dy = -speed
        elif bullet.direction == "down":
            dy = speed

        dx += math.cos(math.radians(bullet.spread)) * speed * 0.1
        dy += math.sin(math.radians(bullet.spread)) * speed * 0.1

        bullet.x += dx
        bullet.y += dy

        bullet_rect = pygame.Rect(bullet.x - bullet.radius, bullet.y - bullet.radius,
                                  bullet.radius * 2, bullet.radius * 2)
        pygame.draw.circle(
            screen,
            bullet.color,
            camera.apply((int(bullet.x), int(bullet.y))),
            bullet.radius
        )

        for slime in slimes[:]:
            slime_rect = pygame.Rect(slime.x, slime.y, slime.width, slime.height)
            if bullet_rect.colliderect(slime_rect):
                slime.health.take_damage(bullet.damage)
                if slime.health.current_hearts <= 0:
                    slimes.remove(slime)
                    killed_slimes += 1
                try:
                    bullets.remove(bullet)
                except ValueError:
                    pass
                break

        if bullet.x < 0 or bullet.x > MAP_SIZE[0] or bullet.y < 0 or bullet.y > MAP_SIZE[1]:
            bullets.remove(bullet)

    if not game_over:
        for slime in slimes:
            slime.move(player.x, player.y)
            slime.draw(screen, camera)

        for slime in slimes:
            slime_rect = pygame.Rect(slime.x, slime.y, slime.width, slime.height)
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            if slime_rect.colliderect(player_rect):
                player.health.take_damage(1)

    if not game_over:
        now = pygame.time.get_ticks()
        if is_moving and now - last_update > animation_speed * 1000:
            current_frame = (current_frame + 1) % 4
            last_update = now
        screen.blit(player_frames[current_direction][current_frame], camera.apply((player.x, player.y)))

    inventory.draw(screen)
    for i in range(player.health.current_hearts):
        screen.blit(textures['heart'], (10 + i * 35, 10))

    if player.health.current_hearts <= 0 and not game_over:
        game_over = True
        game_over_time = pygame.time.get_ticks()

    if game_over:
        box_width = 400
        box_height = 200
        x = WIDTH // 2 - box_width // 2
        y = HEIGHT // 2 - box_height // 2

        elapsed_time = pygame.time.get_ticks() - start_time
        minutes = elapsed_time // 60000
        seconds = (elapsed_time % 60000) // 1000
        time_str = f"{minutes}:{seconds:02d}"

        lines = [
            "Game Over! Player has died.",
            f"Time Survived: {time_str}",
            f"Slimes Killed: {killed_slimes}"
        ]

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        draw_message_box(screen, lines, x, y, box_width, box_height)

    if current_time == 5000:
        SPAWN_INTERVAL -= 500
    if current_time == 20000:
        SPAWN_INTERVAL -= 500
        DAMAGE_INTERVAL -= 100
    if current_time == 30000:
        SPAWN_INTERVAL -= 500
        DAMAGE_INTERVAL -= 300
    if current_time == 60000:
        SPAWN_INTERVAL -= 450
        DAMAGE_INTERVAL -= 400

    pygame.display.flip()

    if game_over:
        while pygame.time.get_ticks() - game_over_time < 5000:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    exit()
            pygame.time.wait(1000)
        running = False

pygame.quit()
