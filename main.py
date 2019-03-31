import pygame
from pygame.locals import *

import os
import re
import random

from math import sin

pygame.init()
coin_logos = os.listdir('./coins')

IDLE = 0
ALIVE = 1
DEAD = 2

class Image:
  def __init__(self, filename):
    self.position = (0, 0)
    self.img = pygame.image.load(filename)
    self.rect = self.img.get_rect()
    
  def set_size(self, width, height):
    self.rect = self.img.get_rect(width=width, height=height)
    
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
        print("whop")
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

  def is_fork(self):
    return self.ticker in ['BSV', 'BCH', 'BTCP', 'BTG', 'BTD']

  def update(self, dt):
    self.position = (self.position[0], self.position[1] + self.speed * dt * 0.1) # TODO what to do when it hits the end? 
    # all bitcoin forks / clones "evil" and will make you lose points / lose the level if they get to the end: this includes Bitcoin Cash, Bitcoin SV, Bitcoin Gold, Bitcoin Private..... yaknow.. 
    
    # most coins just give you points when you shoot them. maybe they make you lose a heart if they touch you?

    # and BTC coins will make you lose 0.33 bitcoins when you shoot them! you start with 1 bitcoin, so you lose 0.33 three times, game over.

  def render(self, screen):
    screen.blit(self.img.img, self.position, self.img.rect)

class Level:
  def __init__(self, difficulty, screen_size, on_lose_life):
    self.difficulty = difficulty
    self.screen_size = screen_size
    self.on_lose_life = on_lose_life
    self.coins = []
    self.spawn_coins()

  @property
  def density(self): # number of 'coins' per level
    # TODO check this up and make it good
    return (self.difficulty + 1) * 2

  @property
  def coin_speed_multiplier(self):
    return 1 + ((self.difficulty - 1) * 0.033)

  def advance(self):
    return Level(self.difficulty + 1)

  def spawn_coins(self):
    x_counter = 0
    y_counter = 0
    for img_file in coin_logos:
      print(img_file)
      #if random.randrange(0, 2) != 1:
      #  continue

      img = Image("./coins/" + img_file)
      img.set_size(64, 64)

      x_pos = 0

      per_row = (3, 4)

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

      if match is not None:
        coin = Coin(match[1].upper(), img, (x_pos-32, y_pos), random.randrange(3, 6)*0.1) # TODO speed
        self.coins.append(coin)

        x_counter = x_counter + 1

  def update(self, dt):
    w, h = pygame.display.get_surface().get_size()
    
    for coin in self.coins:
      coin.update(dt)
      # check out of bounds
      if coin.position[1] > h:
        if coin.is_fork():
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

    self.current_level = Level(1, (w, h), self.on_lose_life)
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
      if (self.ship.position[0] - (self.ship.img.rect.w/2)) > 0:
        self.ship.move(-1 * (dt * 0.1), 0)
    elif key_move_right and not key_move_left:
      if (self.ship.position[0] + (self.ship.img.rect.w/2)) < self.width:
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