from config import *

import math
import random
import time
import pygame
import sys
import os

all_sprites = pygame.sprite.Group()
pygame.init()
clock = pygame.time.Clock()
screen_size = (900, 500)
screen = pygame.display.set_mode(screen_size)

running = True
game_run = True
default_speed = 60
sprite_change_offset = 11
speed = default_speed
time_start = time.time()


def load_image(file_name, colorkey=None):
    fullname = file_name
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)

    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def calculate_sprite_change_offset():
    return max(sprite_change_offset - (speed // sprite_change_offset), 1)


def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


class MainCharacter(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(load_image(image), 5, 1)
        self.cur_frame = 0

        self.image = self.frames[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.default_y = screen_size[1] * SIZE_SKY - self.rect.h
        self.rect.y = self.default_y
        self.rect.x = 20

        self.is_jumping = False
        self.is_falling = False
        self.is_ultimate = True

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def jump(self):
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        if not self.is_falling:
            self.is_jumping = True

    def update(self):
        if self.is_jumping:
            self.rect = self.rect.move(0, -math.ceil(
                DINO_JUMP_SPEED * (self.rect.y - self.default_y + DINO_JUMP_HEIGNT) / 100 * (default_speed / speed)))
            if (self.rect.y - self.default_y + DINO_JUMP_HEIGNT) / 100 <= 0.1:
                self.is_jumping = False
                self.is_falling = True
        elif self.is_falling:
            if self.default_y - self.rect.y < DINO_FALL_SPEED:
                self.rect = self.rect.move(0, self.default_y - self.rect.y)
                self.is_falling = False
            else:
                c = (self.rect.y - self.default_y + DINO_JUMP_HEIGNT) / 100
                self.rect = self.rect.move(0, math.ceil(DINO_FALL_SPEED * (c if c < 0.9 else 1)))
        else:
            offset = calculate_sprite_change_offset()
            self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * offset)
            self.image = self.frames[self.cur_frame // offset]


class Object(pygame.sprite.Sprite):
    def __init__(self, image, step, x=None, y=None):
        super().__init__(all_sprites)
        self.image = load_image(image)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x if x else screen_size[0]
        self.rect.y = y if y else screen_size[1] * SIZE_SKY - self.rect.h
        self.step = -step

    def update(self):
        self.rect = self.rect.move(self.step, 0)

class DecorationObject(Object):
    def __init__(self, image, step, offset_y):
        super().__init__(image, step, screen_size[0] + random.randint(15, 30), None)
        self.rect.y = screen_size[1] * SIZE_SKY - ((self.rect.h + random.randint(5, 20)) * offset_y)


class Enemy(Object):
    def __init__(self, image, step, x=None, y=None):
        super().__init__(image, step, x, y)
        self.image = load_image(image)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x if x else screen_size[0]
        self.rect.y = y if y else screen_size[1] * SIZE_SKY - self.rect.h
        self.step = -step

        self.is_broken = False
        self.broken_direction = 0
        self.broken_speed = (-0.1 * random.randint(5, 10), 0.1 * random.randint(5, 10))
        self.broken_rotate_angle = random.randint(0, 60)

    def broke(self, direction):
        print(3)
        self.is_broken = True
        self.broken_direction = direction

    def update(self):
        global game_run
        if pygame.sprite.collide_mask(self, dino) and not self.is_broken:
            if dino.is_ultimate:
                self.broke(-1)
            else:
                game_run = False
        if self.is_broken:
            try:
                self.rect = self.rect.move([i * BROKE_ENEMY_SPEED * self.broken_direction for i in self.broken_speed])
                self.image = rot_center(self.image, self.broken_rotate_angle * -self.broken_direction)
                self.broken_rotate_angle -= 1
            except ValueError:
                pass
        else:
            self.rect = self.rect.move(self.step, 0)

    def get_far(self):
        return screen_size[0] - self.rect.x

    def is_hidden(self):
        return self.rect.x + self.rect.w < 0


class AnimateEnemy(Enemy):
    def __init__(self, image, step, x=None, y=None):
        self.frames = []
        self.cut_sheet(load_image(image), *animate_sprites[image.split('/')[-1]])
        self.cur_frame = 0
        super().__init__(image, step, x, y)
        self.image = self.frames[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        offset = calculate_sprite_change_offset()
        self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * offset)
        self.image = self.frames[self.cur_frame // offset]
        super().update()


class Bird(AnimateEnemy):
    def __init__(self, image, step, x=None, y=None):
        y = y if y else screen_size[1] * SIZE_SKY - dino.rect.h - random.randint(10, 30)
        super().__init__(image, step, x, y)


class Tornado(AnimateEnemy):
    def __init__(self, image, step, x=None, y=None):
        super().__init__(image, step, x, y)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        offset = calculate_sprite_change_offset()
        self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * offset)
        self.image = self.frames[self.cur_frame // offset]
        super().update()

    def check_colide(self, obj):
        if pygame.sprite.collide_mask(self, obj):
            obj.broke(random.choice([-1, 1]))



class Map:
    def __init__(self, screen, screen_size):
        self.screen = screen
        self.screen_size = screen_size
        self.enemies = []
        self.decoration = []
        self.tech_score = 0
        self.score = 0
        self.next_enemy_distance = self.calculate_next_enemy_distance()

        self.disaster = None

    def clear(self):
        self.screen.fill(COLOR_EARTH)
        pygame.draw.rect(self.screen, COLOR_SKY, (0, 0, self.screen_size[0], self.screen_size[1] * SIZE_SKY), 0)

    def update(self):
        self.clear()
        self.spawn_enemy()
        self.spawn_decoration()

        font = pygame.font.Font(None, 50)
        text = font.render(f"Счёт: {self.score}", True, (100, 255, 100))
        text_x = screen_size[0] - text.get_width()
        text_y = 0
        screen.blit(text, (text_x, text_y))

        for i, obj in enumerate(self.enemies.copy()):
            # obj.move()
            if obj.is_hidden():
                self.enemies.pop(i)
                all_sprites.remove(obj)
                if isinstance(obj, Tornado):
                    self.disaster = None
        # print(self.disaster)
        if self.disaster:
            for i in filter(lambda x: not isinstance(x, Tornado), self.enemies):
                self.disaster.check_colide(i)

    def random_select_next(self):
        self.score += 1

        path = 'src/enemy/'
        select = random.randint(1, 10)
        if select * random.randint(1, 5) == 5 and False:
            pass
        elif select == 1 and self.score >= TORNADO_SCORE_START and not self.disaster:
            self.disaster = Tornado(f'{path}tornado.png', SPEED_TORNADO)
            return self.disaster
        elif select < 4 and self.score >= BIRD_SCORE_START:
            return Bird(f'{path}bird.png', SPEED_BIRD)
        else:
            return Enemy(f'{path}{random.randint(1, 3)}.png', SPEED_CACTUS)

    def spawn_enemy(self):
        if self.enemies:
            if self.enemies[-1].get_far() >= self.next_enemy_distance:
                self.enemies.append(self.random_select_next())
                self.next_enemy_distance = self.calculate_next_enemy_distance()
        else:
            self.enemies.append(self.random_select_next())

    def spawn_decoration(self):
        if random.randint(1, 50) == 1:
            if random.randint(0, 1):
                self.decoration.append(DecorationObject(f"src/decoration/sky_{random.randint(1, 2)}.png", SPEED_CACTUS, random.randint(3, 5)))

    def calculate_next_enemy_distance(self):
        return random.randint(dino.rect.w * 4, DISTANCE_BETWEEN_ENEMY_MAX)

dino = MainCharacter("src/character/fox.png")
map = Map(screen, screen_size)
while running:
    if speed < MAX_GAME_SPEED:
        speed = int(default_speed + (time.time() - time_start))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_run:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    dino.jump()
                elif event.key == pygame.K_DOWN:
                    dino.is_ultimate = True
    if game_run:
        map.update()
        all_sprites.update()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(speed)
