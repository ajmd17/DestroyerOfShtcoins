import pygame
from pygame.locals import *

import os
import re

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
    
  def size(self, width, height):
    self.rect = self.img.get_rect(width, height)
    
  def move(self, x, y):
    self.position = (x, y)

  def draw(self):
    game.screen.blit(self.img, self.position, self.rect)

#chset = Image('chset_8_12.png')
#chrect = chset.img.get_rect(width=8, height=12)

class Ship:
  def __init__(self, x, y):
    self.position = (x, y)
    self.img = Image('ship.png')
    self.tick = 0.0

  def move(self, x, y):
    self.position = (self.position[0] + x, self.position[1] + y)

  def shoot(self):
    pass

  def update(self, dt):
    self.tick = self.tick + dt * 0.001
    self.position = (self.position[0], self.position[1] + (sin(self.tick*6)*0.2))

  def render(self, screen):
    screen.blit(self.img.img, (self.position[0] - (self.img.rect.w / 2), self.position[1] - self.img.rect.h), self.img.rect)


class Coin:
  def __init__(self, ticker, img, speed):
    self.position = (0, 0) # TODO make random X and Y at top of screen
    self.ticker = ticker
    self.img = img
    self.speed = speed

  
  def update(self):
    self.position[1] = self.position - self.speed # TODO what to do when it hits the end? 
    # all bitcoin forks / clones "evil" and will make you lose points / lose the level if they get to the end: this includes Bitcoin Cash, Bitcoin SV, Bitcoin Gold, Bitcoin Private..... yaknow.. 
    
    # most coins just give you points when you shoot them. maybe they make you lose a heart if they touch you?

    # and BTC coins will make you lose 0.33 bitcoins when you shoot them! you start with 1 bitcoin, so you lose 0.33 three times, game over.

  def render(self, screen):
    screen.blit(self.img.img, self.position, self.img.rect)

class Level:
  def __init__(self, difficulty):
    self.difficulty = difficulty
    self.coins = []

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
    for img_file in coin_logos:
      coin = Coin(re.search(img_file, "^([A-Za-z]*)_logo\.png$"), Image(img_file), 1) # TODO speed
      self.coins.append(coin)

  def render(self, screen):
    for coin in self.coins:
      coin.render(screen)


class Game:
  def __init__(self):
    screen_info = pygame.display.Info()
    self.screen = pygame.display.set_mode((600, 400))
    w, h = pygame.display.get_surface().get_size()
    #pygame.display.toggle_fullscreen()

    self.width = w
    self.height = h

    self.current_level = Level(1)
    self.ship = Ship((w / 2), h - 15)
    self.state = IDLE

    self.running = True

  def check_events(self, dt):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.running = False
    
    keystate = pygame.key.get_pressed()

    key_move_left = keystate[K_LEFT] or keystate[K_a]
    key_move_right = keystate[K_RIGHT] or keystate[K_d]

    if key_move_left and not key_move_right:
      if (self.ship.position[0] - (self.ship.img.rect.w/2)) > 0:
        self.ship.move(-1 * (dt * 0.1), 0)
    elif key_move_right and not key_move_left:
      if (self.ship.position[0] + (self.ship.img.rect.w/2)) < self.width:
        self.ship.move(dt * 0.1, 0)
    else:
      pass

  def update(self, dt):
    self.ship.update(dt)

  
  def render(self):
    self.screen.fill((255, 255, 255))
    self.current_level.render(self.screen)
    self.ship.render(self.screen)
    pygame.display.flip()


game = Game()
clock = pygame.time.Clock()
while game.running:
  dt = clock.tick(60)
  game.check_events(dt)
  game.update(dt)
  game.render()
