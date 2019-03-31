import pygame
from pygame.locals import *

import os
import re
import sys
import random

from math import sin

pygame.init()
coin_logos = os.listdir('./coins')

IDLE = 0
ALIVE = 1
DEAD = 2

MAX_DIFFICULTY = 10
BASE_RATE = 300
MAX_RATE = 30
IMG_SIZE = 48

def lerp(x, y, a):
  return x * (1 - a) + y * a

chset = pygame.image.load('./assetz/chset_8_12.png')
chrect = chset.get_rect(width=8, height=12)

def text_width(text):
  return 8 * len(text)

def text_height(text):
  return 12 * len(text.split("\n"))

def putchar(ch, x, y):
    chrect = chset.get_rect()

    if (ch >= 'K' and ch <= 'T'):
      chrect.topleft = ((ord(ch)-ord('K'))*8, 12)
    elif (ch >= 'U' and ch <= 'Z'):
      chrect.topleft = ((ord(ch)-ord('U'))*8, 24)
    else:
      chrect.topleft = ((ord(ch)-ord('A'))*8, 0)
    
    if (ch == '!'):
      chrect.topleft = (6*8, 24)
    elif (ch == '?'):
      chrect.topleft = (7*8, 24)
    elif (ch == '-'):
      chrect.topleft = (8*8, 24)
    elif (ch == ' '):
      chrect.topleft = (9*8, 24)
    elif (ch == '₿'):
      chrect.topleft = (0*8, 48)
    elif (ch == '.'):
      chrect.topleft = (1*8, 48)
    elif (ch == ','):
      chrect.topleft = (2*8, 48)
    elif (ch == '/'):
      chrect.topleft = (3*8, 48)
    elif (ch == '+'):
      chrect.topleft = (4*8, 48)

    if (ch >= '0' and ch <= '9'):
      chrect.topleft = ((ord(ch)-ord('0'))*8, 36)
    
    chrect.width = 8
    chrect.height = 12

    game.screen.blit(chset, (x, y), chrect)

def putstr(string, sx, sy):
    for ch in string.upper():
      putchar(ch, sx, sy)
      sx += 8

def format_btc_balance(n):
  txt = "B{:1.4f}".format(abs(n))
  if n < 0:
    txt = "-" + txt
  else:
    txt = "+" + txt

  return txt

class Image:
  def __init__(self, filename):
    self.position = (0, 0)
    self.img = pygame.image.load(filename)
    self.rect = self.img.get_rect()
    
  def size(self, w, h):
    self.img = pygame.transform.scale(self.img, (w, h))
    self.rect = self.img.get_rect()
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
    self.next_position = (x, y)
    self.img = Image('ship.png')
    self.tick = 0.0
    self.mining_laser_power = 0.03
    self.lasers = []
    self.laser_cooldown = 0

  def move(self, x, y):
    self.next_position = (self.next_position[0] + x, self.next_position[1] + y)

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
    self.position = (min(game.width - self.img.rect.w/2, max(self.img.rect.w/2, lerp(self.position[0], self.next_position[0], min(1.0, self.tick*0.003)))), self.position[1])
    self.next_position = (self.next_position[0], self.next_position[1] + (sin(self.tick*6)*0.2))
    self.position = (self.position[0], self.position[1] + (sin(self.tick*6)*0.2))
    if (self.laser_cooldown != 0):
        self.laser_cooldown -= 1

    for laser in self.lasers:
      laser.move(0, -10)

      if game.current_level.check_laser_intersection(laser.position) or laser.position[1] >= game.height:
        if laser in self.lasers: # not been cleared
          self.lasers.remove(laser)
        
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

    self.reward = random.randrange(360, 900) * 0.0001

    if self.is_bitconnect:
      self.reward = random.randrange(855, 2500) * 0.0001

    if self.is_btc:
      self.reward = -0.33

    if self.is_fork:
      #self.reward = random.randrange(65, 300) * 0.0001
      self.alpha_counter_update_speed = random.randrange(3, 10) * 0.1
      self.alpha_counter = 0.0
      self.rect = pygame.Surface((IMG_SIZE + 16, IMG_SIZE + 16))
      self.rect.fill((255, 255, 255))
      self.rect.set_colorkey((255, 255, 255))
      self.rect.set_alpha(35)

  @property
  def is_btc(self):
    return self.ticker == 'BTC'
  
  @property
  def is_bitconnect(self):
    return self.ticker == 'BCC'

  @property
  def is_fork(self):
    return self.ticker in ['BSV', 'BCH', 'BTCP', 'BTG', 'BTD']

  def update(self, dt):
    if self.is_fork:
      self.alpha_counter = self.alpha_counter + (dt * 0.0085 * self.alpha_counter_update_speed)
      self.rect.set_alpha(max(80, 255 *  sin(self.alpha_counter) * 0.5 + 0.5))
    self.position = (self.position[0], self.position[1] + self.speed * dt * 0.1)

  def render(self, screen):
    if self.is_fork:
      r = int(self.rect.get_width() / 2)
      glow_pos = (int(self.position[0] - ((self.rect.get_width() - self.img.rect.w) / 2)), int(self.position[1] - ((self.rect.get_height() - self.img.rect.h) / 2)))
      pygame.draw.circle(self.rect, (255, 85, 50), (r, r), r)
      screen.blit(self.rect, glow_pos)
    screen.blit(self.img.img, self.position, self.img.rect)
    txt = "₿{:1.4f}".format(abs(self.reward))
    if self.reward < 0:
      txt = "-" + txt
    else:
      txt = "+" + txt
    putstr(txt, self.position[0] + (self.img.rect.w / 2) - (text_width(txt) / 2), self.position[1] + (self.img.rect.h / 2) - (text_height(txt) / 2))

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
  def btc_balance_target(self):
    if self.difficulty == 1:
      return 1.0
    elif self.difficulty == 2:
      return 1.25
    elif self.difficulty == 3:
      return 1.5
    elif self.difficulty == 4:
      return 1.75
    elif self.difficulty == 5:
      return 2
    elif self.difficulty == 6:
      return 2.5
    elif self.difficulty == 7:
      return 3
    elif self.difficulty == 8:
      return 4
    elif self.difficulty == 9:
      return 5
    elif self.difficulty == 10:
      return 10

  @property
  def coin_speed_multiplier(self):
    return 1 + ((self.difficulty - 1) * 0.033)

  @property
  def coin_spawn_rate(self):
    if self.difficulty == 1:
      return 150
    elif self.difficulty <= 3:
      return 125
    elif self.difficulty <= 5:
      return 100
    elif self.difficulty <= 7:
      return 85
    elif self.difficulty == 8:
      return 75
    elif self.difficulty == 9:
      return 65
    elif self.difficulty == 10:
      return 55

    #a = self.difficulty / MAX_DIFFICULTY
    #return BASE_RATE * (1 - a) + MAX_RATE * a

  def next(self):
    if self.difficulty == MAX_DIFFICULTY:
      # TODO: you won!
      return Level(1, self.screen_size, self.on_lose_life)

    return Level(self.difficulty + 1, self.screen_size, self.on_lose_life)

  def check_laser_intersection(self, laser_pos):
    for coin in self.coins:
      if (laser_pos[1] <= coin.position[1] + coin.img.rect.h) and (laser_pos[0] <= coin.position[0] + (coin.img.rect.w)) and (laser_pos[0] >= coin.position[0]):
        # move the btc from the coin over to your balance!
        reward_before = coin.reward
        coin.reward = max(0, coin.reward - game.ship.mining_laser_power)
        game.btc_balance += reward_before - coin.reward

        if game.btc_balance >= game.current_level.btc_balance_target:
          game.btc_balance = 0.0
          game.num_lives = 3
          game.current_level = game.current_level.next()
          game.ship.lasers = []
          return False

        if coin.reward == 0:
          self.coins.remove(coin)

        return True

    return False

  def spawn_coin(self):
    idx = random.randrange(0, len(coin_logos))
    img_file = coin_logos[idx]

    img = Image("./coins/" + img_file)
    img.size(IMG_SIZE, IMG_SIZE)

    x_pos = random.randrange(img.rect.w/2, self.screen_size[0] - img.rect.w)
    y_pos = 0 - img.rect.h

    coin = Coin(img_file.split('_')[0].upper(), img, (x_pos-(IMG_SIZE/2), y_pos), random.randrange(3, 6)*0.1)
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
      img.size(IMG_SIZE, IMG_SIZE)

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

      coin = Coin(img_file.split('_')[0].upper(), img, (x_pos-(IMG_SIZE/2), y_pos), random.randrange(3, 6)*0.1)
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

    self.width = w
    self.height = h

    self.current_level = Level(1, (w, h), self.on_lose_life)
    self.ship = Ship((w / 2), h - 15)
    self.state = IDLE

    self.num_lives = 3
    self.btc_balance = 0.0

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
        self.ship.move(-1 * (dt * 0.35), 0)
    elif key_move_right and not key_move_left:
      if (self.ship.position[0] + (self.ship.img.rect.w / 2)) < self.width:
        self.ship.move(dt * 0.35, 0)
    else:
      pass

    if key_shoot:
      game.ship.shoot()

  def update(self, dt):
    self.ship.update(dt)
    self.current_level.update(dt)
  
  def render(self):
    self.screen.fill((0, 0, 0))
    self.current_level.render(self.screen)
    self.ship.render(self.screen)

    for i in range(0, self.num_lives):
      self.screen.blit(self.life_icon.img, (30 + (45 * i), self.height - 50), self.life_icon.rect)

    putstr("level " + str(self.current_level.difficulty) + " / " + str(MAX_DIFFICULTY), 20, 10)
    putstr("mining laser power: " + format_btc_balance(self.ship.mining_laser_power), 20, 25)

    btc_balance_text = format_btc_balance(self.btc_balance)
    putstr(btc_balance_text, self.width - text_width(btc_balance_text) - 20, 10)

    btc_goal_text = "goal: " + format_btc_balance(self.current_level.btc_balance_target)
    putstr(btc_goal_text, self.width - text_width(btc_goal_text) - 20, 25)

    pygame.display.flip()


game = Game()
clock = pygame.time.Clock()
while game.running:
  dt = clock.tick(60)
  game.check_events(dt)
  game.update(dt)
  game.render()