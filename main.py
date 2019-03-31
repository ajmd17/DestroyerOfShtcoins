import pygame
from pygame.locals import *

import os
import re
import sys
import random

from math import sin

pygame.init()
coin_logos = os.listdir('./coins')

print("fut")

IDLE = 0
ALIVE = 1
DEAD = 2

MAX_DIFFICULTY = 10
BASE_RATE = 300
MAX_RATE = 30

class Image:
  def __init__(self, filename):
    self.position = (0, 0)
    self.img = pygame.image.load(filename)
    self.rect = self.img.get_rect()
    
  def size(self, w, h):
    self.img = pygame.transform.scale(self.img, (w, h))
    #self.rect = self.img.get_rect(width=w, height=h)
    
  def move(self, x, y):
    self.position = (self.position[0] + x, self.position[1] + y)

  def draw(self):
    game.screen.blit(self.img, self.position, self.rect)

#chset = Image('chset_8_12.png')
#chrect = chset.img.get_rect(width=8, height=12)

class Ship:
  def __init__(self, x, y):
    self.position = (x, y)
    self.img = Image('ship.png')
    self.tick = 0.0
    self.lasers = []
    self.laser_cooldown = 0;

  def move(self, x, y):
    self.position = (self.position[0] + x, self.position[1] + y)

  def shoot(self):
    if self.laser_cooldown != 0:
      return
    self.laser_cooldown = 20
    laser = Image('laser.png')
    laser.size(10, 30)
    laser.position = self.position
    self.lasers.append(laser)

  def update(self, dt):
    self.tick = self.tick + dt * 0.001
    self.position = (self.position[0], self.position[1] + (sin(self.tick*6)*0.2))
    if (self.laser_cooldown != 0):
        self.laser_cooldown -= 1

    for laser in self.lasers:
      laser.move(0, -10)
      print(self.laser_cooldown)
      if laser.position[1] < 0:
        self.lasers.pop(self.lasers.index(laser))
        
  def render(self, screen):
    for laser in self.lasers:
      laser.draw()
    screen.blit(self.img.img, (self.position[0] - (self.img.rect.w / 2), self.position[1] - self.img.rect.h), self.img.rect)


class Coin:
  def __init__(self, ticker, img, position, speed):
    self.position = position
    self.ticker = ticker
    self.img = img
    self.speed = speed

    if self.is_fork:
      self.rect = pygame.Surface((75, 75))
      self.rect.fill((250, 0, 0))

  @property
  def is_fork(self):
    return self.ticker in ['BSV', 'BCH', 'BTCP', 'BTG', 'BTD']

  def update(self, dt):
    self.position = (self.position[0], self.position[1] + self.speed * dt * 0.1) # TODO what to do when it hits the end? 
    # all bitcoin forks / clones "evil" and will make you lose points / lose the level if they get to the end: this includes Bitcoin Cash, Bitcoin SV, Bitcoin Gold, Bitcoin Private..... yaknow.. 
    
    # most coins just give you points when you shoot them. maybe they make you lose a heart if they touch you?

    # and BTC coins will make you lose 0.33 bitcoins when you shoot them! you start with 1 bitcoin, so you lose 0.33 three times, game over.

  def render(self, screen):
    if self.is_fork:
      r = 42
      glow_pos = (int(self.position[0] + 32), int(self.position[1] + 32))
      pygame.draw.circle(screen, (255, 0, 0, 100), glow_pos, r)
      #screen.blit(self.rect, )
    screen.blit(self.img.img, self.position, self.img.rect)

class Level:
  def __init__(self, difficulty, screen_size, on_lose_life):
    self.difficulty = difficulty
    self.screen_size = screen_size
    self.on_lose_life = on_lose_life
    self.coins = []
    self.spawn_coin_counter = self.coin_spawn_rate
    self.spawn_coins()

  @property
  def density(self): # number of 'coins' per level
    # TODO check this up and make it good
    return (self.difficulty + 1) * 2

  @property
  def coin_speed_multiplier(self):
    return 1 + ((self.difficulty - 1) * 0.033)

  @property
  def coin_spawn_rate(self):
    if self.difficulty == 1:
      return 300
    elif self.difficulty <= 3:
      return 200
    elif self.difficulty <= 5:
      return 150
    elif self.difficulty <= 7:
      return 125
    elif self.difficulty == 8:
      return 100
    elif self.difficulty == 9:
      return 85
    elif self.difficulty == 10:
      return 65

    #a = self.difficulty / MAX_DIFFICULTY
    #return BASE_RATE * (1 - a) + MAX_RATE * a

  def advance(self):
    return Level(self.difficulty + 1)

  def spawn_coin(self):
    idx = random.randrange(0, len(coin_logos))
    img_file = coin_logos[idx]
    match = re.search(r"^([A-Za-z]*)_logo\.png$", img_file)

    if match is not None:
      img = Image("./coins/" + img_file)
      img.size(64, 64)

      x_pos = random.randrange(img.rect.w/2, self.screen_size[0] - img.rect.w)
      y_pos = 0 - img.rect.h

      coin = Coin(match.group().upper(), img, (x_pos-32, y_pos), random.randrange(3, 6)*0.1)
      self.coins.append(coin)
    

  def spawn_coins(self):
    per_row = (1, 2)
    if self.difficulty < 3:
      per_row = (2, 3)
    else:
      per_row = (3, 4)

    x_counter = 0
    y_counter = 0

    for img_file in coin_logos:
      if random.randrange(0, 2) != 1:
        continue
      if self.difficulty < 4:
        if y_counter > 2:
          break
      elif self.difficulty < 6:
        if y_counter > 3:
          break
      elif self.difficulty < 8:
        if y_counter > 4:
          break

      img = Image("./coins/" + img_file)
      img.size(64, 64)

      x_pos = 0

      if y_counter % 2 == 0:
        if x_counter != 0 and x_counter % per_row[0] == 0:
          x_counter = 0
          y_counter = y_counter + 1
      else:
        if x_counter != 0 and x_counter % per_row[1] == 0:
          x_counter = 0
          y_counter = y_counter + 1

      if y_counter % 2 == 0:
        section_w = self.screen_size[0]/per_row[0]
        x_pos = (x_counter * section_w) + (section_w/2)
      else:
        section_w = self.screen_size[0]/per_row[1]
        x_pos = (x_counter * section_w) + (section_w/2)
      y_pos = y_counter * 64

      match = re.search(r"^([A-Za-z]*)_logo\.png$", img_file)
      print(match.group())

      if match is not None:
        coin = Coin(match.group().upper(), img, (x_pos-32, y_pos), random.randrange(3, 6)*0.1)
        self.coins.append(coin)

        x_counter = x_counter + 1

  def update(self, dt):
    w, h = pygame.display.get_surface().get_size()

    self.spawn_coin_counter = self.spawn_coin_counter - dt * 0.1

    if self.spawn_coin_counter <= 0.0:
      self.spawn_coin()
      self.spawn_coin_counter = self.coin_spawn_rate
    
    for coin in self.coins:
      coin.update(dt)
      # check out of bounds
      if coin.position[1] > h:
        if coin.is_fork:
          # lose 1 life.
          self.on_lose_life() # TODO: explanation.

        self.coins.remove(coin)

  def render(self, screen):
    for coin in self.coins:
      coin.render(screen)


class Game:
  def __init__(self):
    screen_info = pygame.display.Info()
    self.screen = pygame.display.set_mode((800, 600))
    w, h = pygame.display.get_surface().get_size()
    #pygame.display.toggle_fullscreen()

    self.width = w
    self.height = h

    self.current_level = Level(10, (w, h), self.on_lose_life)
    self.ship = Ship((w / 2), h - 15)
    self.state = IDLE

    self.num_lives = 3

    self.life_icon = Image('./lightning.png')

    self.running = True

  def on_lose_life(self): #todo explanation argument
    self.num_lives = self.num_lives - 1

    if self.num_lives == 0:
      # TODO game over
      self.num_lives = 3

  def check_events(self, dt):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.running = False
    
    keystate = pygame.key.get_pressed()

    key_move_left = keystate[K_LEFT] or keystate[K_a]
    key_move_right = keystate[K_RIGHT] or keystate[K_d]
    key_shoot = keystate[K_SPACE]

    if key_move_left and not key_move_right:
      if (self.ship.position[0] - (self.ship.img.rect.w / 2)) > 0:
        self.ship.move(-1 * (dt * 0.1), 0)
    elif key_move_right and not key_move_left:
      if (self.ship.position[0] + (self.ship.img.rect.w / 2)) < self.width:
        self.ship.move(dt * 0.1, 0)
    elif key_shoot:
      game.ship.shoot()
    else:
      pass

  def update(self, dt):
    self.ship.update(dt)
    self.current_level.update(dt)
  
  def render(self):
    self.screen.fill((255, 255, 255))
    self.current_level.render(self.screen)
    self.ship.render(self.screen)

    for i in range(0, self.num_lives):
      self.screen.blit(self.life_icon.img, (30 + (45 * i), self.height - 50), self.life_icon.rect)

    pygame.display.flip()


game = Game()
clock = pygame.time.Clock()
while game.running:
  dt = clock.tick(60)
  game.check_events(dt)
  game.update(dt)
  game.render()