import pygame
import os
import random
pygame.font.init()

WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((HEIGHT, WIDTH))
pygame.display.set_caption("Space Invaders")

RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))


class Item:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def collision(self, obj):
        return collide(obj, self)


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, laser_speed):
        self.y += laser_speed

    def off_screen(self):
        return not (HEIGHT >= self.y >= 0)

    def collision(self, obj):
        return collide(obj, self)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, laser_speed, obj):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(laser_speed)
            if laser.off_screen():
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


active_items = []


class Player(Ship):
    def __init__(self, x, y, health):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.score = 0

    def move_lasers(self, laser_speed, objs):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(laser_speed)
            if laser.off_screen():
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        self.score += 1
                        item = Item(obj.x, obj.y, YELLOW_LASER)
                        active_items.append(item)
                        objs.remove(obj)
                        self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)

    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height()+10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 200, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10,
                          self.ship_img.get_width() * (self.health/self.max_health), 10))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x-22, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def main():
    run = True
    lost = False
    fps = 60
    level = 0
    lives = 3
    lost_timer = 0
    main_font = pygame.font.SysFont("comicsans", 50)
    lost_font = pygame.font.SysFont("comicsans", 60)
    enemies = []
    wave_intensity = 0
    enemy_speed = 1
    player_speed = 3
    p_laser_speed = 8
    e_laser_speed = 8

    item_perks = [1, 2, 3, 4, 5]

    player = Player(300, 600, 100)

    clock = pygame.time.Clock()

    def redraw_window():
        WIN.blit(BG, (0, 0))

        lives_level = main_font.render(f"Lives: {lives}", 1, (200, 100, 100))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        score_label = main_font.render(f"Score: {player.score}", 1, (100, 100, 200))

        WIN.blit(lives_level, (10, 10))
        WIN.blit(level_label, (WIDTH-level_label.get_width()-10, 10))
        WIN.blit(score_label, ((WIDTH/2)-score_label.get_width()/2, 10))

        for e in enemies:
            e.draw(WIN)

        player.draw(WIN)

        for a in active_items[:]:
            a.draw(WIN)

        if lost:
            lost_label = lost_font.render(f"You Lost!!!", 1, (200, 80, 80))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        pygame.display.update()

    while run:
        clock.tick(fps)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_timer += 1

        if lost:
            if lost_timer > 2*fps:
                active_items.clear()
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_intensity += 5
            for i in range(wave_intensity):
                enemy = Enemy(random.randrange(100, WIDTH-100),
                              random.randrange(-1500, -100),
                              random.choice(["red", "green", "blue"]),
                              100)
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player.x > 0:
            player.x -= player_speed
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and player.y < HEIGHT - player.get_height()-25:
            player.y += player_speed
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and player.y > 0:
            player.y -= player_speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player.x + player.get_width() < WIDTH:
            player.x += player_speed
        if keys[pygame.K_SPACE]:
            player.shoot()

        for i in active_items[:]:
            if collide(i, player):
                c = random.choice(item_perks)
                if c == 1:
                    player_speed += 1
                elif c == 2:
                    e_laser_speed += 0.5
                elif c == 3:
                    lives += 1
                elif c == 4:
                    p_laser_speed += 1
                elif c == 5:
                    lives = 1
                active_items.remove(i)

        for enemy in enemies[:]:
            enemy.move(enemy_speed)
            enemy.move_lasers(e_laser_speed, player)

            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 50
                player.score += 1
                enemies.remove(enemy)

            if enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-p_laser_speed, enemies)


def main_menu():
    title_font = pygame.font.SysFont("comicsans", 50)
    run = True
    while run:
        WIN.blit(BG, (0, 0))
        title_label = title_font.render("Press The Mouse To Begin...", 1, (255, 255, 255))
        WIN.blit(title_label, (WIDTH/2-title_label.get_width()/2, HEIGHT/2-title_label.get_height()/2))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

        pygame.display.update()


main_menu()
