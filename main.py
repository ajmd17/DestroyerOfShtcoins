import pygame
from pygame.locals import *

import os
import re
import sys
import random

from math import sin

pygame.init()
coin_logos = os.listdir('./coins')

MAX_DIFFICULTY = 10
BASE_RATE = 300
MAX_RATE = 30
IMG_SIZE = 52
LASER_SPEED = 10
MAX_BOOST = 10

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

def format_btc_balance(n, render_plus=False):
  txt = "₿{:1.4f}".format(abs(n))
  if n < 0:
    txt = "-" + txt
  elif render_plus:
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

  def draw(self, frame_loc=(-1, -1), frame_dim=(-1, -1)):
    if frame_dim != (-1, -1):
      self.rect = self.img.get_rect(width=frame_dim[0], height=frame_dim[1])
    if frame_loc != (-1, -1):
      self.rect.topleft = frame_loc
      
    game.screen.blit(self.img, self.position, self.rect)

class SpriteSheet:
  def __init__(self, filename, frame_size, frame_amt=(1, 0)):
    self.img = Image(filename)
    self.frame_size = frame_size
    self.frame_amt = (frame_amt[0]-1, frame_amt[1]-1)
    self.frame_counter = [0, 0]

  def progress_frame(self):
    self.frame_counter[0] += 1
    # if frame counter x is greater than size x, increment y
    if self.frame_counter[0] > self.frame_amt[0]:
      self.frame_counter[1] += 1
      self.frame_counter[0] = 0
    # if frame counter y is greater than size y, reset counter
    if (self.frame_counter[1] > self.frame_amt[1]):
        self.frame_counter = [0, 0]

  def draw(self):
    self.img.draw((self.frame_counter[0]*self.frame_size[0], self.frame_counter[1]*self.frame_size[1]), self.frame_size)

class Star:
  def __init__(self):
    self.sprite = SpriteSheet('assetz/sh_star.png', (16, 16), (3, 1))
    
  def update(self):
    self.sprite.progress_frame()
  
  def move(self, x, y):
    self.sprite.img.move(x, y)

  def draw(self):
    self.sprite.draw()

class Stars:
  def __init__(self):
    self.ticks = 0
    self.ticks_wait = random.randrange(0, 40)
    self.stars_far = []
    self.stars_close = []

    for i in range(0, random.randrange(10, 20)):
      star = Star()
      for i in range(0, 2):
        star.update()
      star.move(random.randrange(0, 800), random.randrange(0, 600))
      self.stars_far.append(star)

    for i in range(0, random.randrange(10, 20)):
      star = Star()
      for i in range(0, 2):
        star.update()
      star.move(random.randrange(0, 800), random.randrange(0, 600))
      self.stars_close.append(star)

  def move(self, x, y):
    for star in self.stars_close:
      star.move(x, y)
      if star.sprite.img.position[1] > 600:
        self.stars_close.pop(self.stars_close.index(star))
        star = Star()
        for i in range(0, 2):
          star.update()
        star.move(random.randrange(0, 800), 0)
        self.stars_close.append(star)

  def update(self):
    if self.ticks != self.ticks_wait:
      self.ticks += 1
      return
    self.ticks = 0
    self.stars_far[random.randrange(0, len(self.stars_far))].update()
    self.stars_close[random.randrange(0, len(self.stars_close))].update()

  def draw(self):
    for star in self.stars_far:
      star.draw()
    for star in self.stars_close:
      star.draw()

class Ship:
  def __init__(self, x, y):
    self.position = (x, y)
    self.next_position = (x, y)
    self.img = Image('ship.png')
    self.tick = 0.0
    self.mining_laser_power = 0.015
    self.mining_laser_cost = 0.0005
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
    laser.position = (self.position[0]+12, self.position[1]-48)
    self.lasers.append(laser)
    laser = Image('laser.png')
    laser.size(10, 30)
    laser.position = (self.position[0]-24, self.position[1]-48)
    self.lasers.append(laser)

    game.sounds['shoot'].play()

  def update(self, dt):
    self.tick = self.tick + dt * 0.001
    self.position = (min(game.width - self.img.rect.w/2, max(self.img.rect.w/2, lerp(self.position[0], self.next_position[0], dt*0.003))), self.position[1])
    
    if game.boost <= 0.001 or game.boost == MAX_BOOST:
      self.next_position = (self.next_position[0], self.next_position[1] + (sin(self.tick*6)*0.2))
      self.position = (self.position[0], self.position[1] + (sin(self.tick*6)*0.2))

    if (self.laser_cooldown != 0):
        self.laser_cooldown -= 1

    for laser in self.lasers:
      laser.move(0, -LASER_SPEED)

      if game.current_level.check_laser_intersection(laser.position) or laser.position[1] <= 0:
        if laser in self.lasers: # not been cleared
          self.lasers.remove(laser)
        
  def render(self, screen):
    for laser in self.lasers:
      laser.draw()

    boost_perc =  max(0.0, min(1.0, game.boost / MAX_BOOST))
    screen.blit(self.img.img, (self.position[0] - (self.img.rect.w / 2), (lerp(self.position[1], self.position[1] - 55, boost_perc)) - self.img.rect.h), self.img.rect)


class EventBox:
  def __init__(self):
    self.messages = []
  
  def update(self, dt):
    for msg in self.messages:
      msg['countdown'] -= 0.01 * dt

      if msg['countdown'] <= 0:
        self.messages.remove(msg)

  def add_msg(self, msg, color=(0, 255, 0)):
    if len(self.messages) == 10:
      self.messages.pop()

    rect = pygame.Surface((125, 25))
    rect.fill(color)
    rect.set_alpha(75)
    self.messages.append({ 'rect': rect, 'msg': msg, 'countdown': 45 })

  def render(self, screen):
    y_pos = game.height
    for i in range(len(self.messages), 0, -1):
      msg = self.messages[i - 1]

      box_x = game.width - msg['rect'].get_width() - 20
      y_pos -= msg['rect'].get_height() + 3
      box_y = y_pos

      screen.blit(msg['rect'], (box_x, box_y))
      putstr(msg['msg'], box_x, box_y)



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

    if self.is_fork or self.is_bitconnect:
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
    return self.ticker in ['BSV', 'BCH', 'BAB', 'BTCP', 'BTG', 'BCD', 'BTCD']

  def update(self, dt):
    if self.is_fork or self.is_bitconnect:
      self.alpha_counter = self.alpha_counter + (dt * 0.0085 * self.alpha_counter_update_speed)
      self.rect.set_alpha(max(80, 255 *  sin(self.alpha_counter) * 0.5 + 0.5))
    self.position = (self.position[0], self.position[1] + (self.speed * dt * 0.1) * game.speed)

  def render(self, screen):
    putstr(self.ticker, self.position[0] + (self.img.rect.w / 2) - (text_width(self.ticker) / 2), self.position[1] - 17)
    if self.is_fork or self.is_bitconnect:
      r = int(self.rect.get_width() / 2)
      glow_pos = (int(self.position[0] - ((self.rect.get_width() - self.img.rect.w) / 2)), int(self.position[1] - ((self.rect.get_height() - self.img.rect.h) / 2)))
      pygame.draw.circle(self.rect, (255, 85, 50), (r, r), r)
      screen.blit(self.rect, glow_pos)
    screen.blit(self.img.img, self.position, self.img.rect)
    txt = format_btc_balance(self.reward, True)
    putstr(txt, self.position[0] + (self.img.rect.w / 2) - (text_width(txt) / 2), self.position[1] + (self.img.rect.h) + 5)

class Level:
  def __init__(self, difficulty, screen_size, on_lose_life):
    self.difficulty = difficulty
    self.screen_size = screen_size
    self.on_lose_life = on_lose_life
    self.coins = []
    self.spawn_coin_counter = self.coin_spawn_rate
    self.spawn_coins()
    self.btc_reward_accum_pos = 0.0
    self.btc_reward_accum_neg = 0.0
    self.btc_reward_timer_pos = 0.0
    self.btc_reward_timer_neg = 0.0

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
      if (laser_pos[1] <= coin.position[1]) and (laser_pos[0] <= coin.position[0] + (coin.img.rect.w)) and (laser_pos[0] >= coin.position[0]):
        # move the btc from the coin over to your balance!
        reward_before = coin.reward
        coin.reward = max(0, coin.reward - game.ship.mining_laser_power)
        to_add = reward_before - coin.reward
        game.btc_balance += to_add
        #color = (0, 255, 0)
        #if to_add < 0:
        #  color = (255, 0, 0)
        #game.event_box.add_msg(format_btc_balance(to_add, True), color)
        if to_add > 0:
          self.btc_reward_accum_pos += to_add
          game.sounds['coin'].play()
        elif to_add < 0:
          self.btc_reward_accum_neg += -1 * to_add
          game.sounds['hurt'].play()

        if game.btc_balance >= game.current_level.btc_balance_target:
          game.current_screen = LevelUpScreen()
          return False

        if coin.reward == 0:
          if coin.is_btc:
            game.stats.num_btc_destroyed += 1
          elif coin.is_bitconnect or coin.is_fork:
            game.stats.num_sour_coins_destroyed += 1
          else:
            game.stats.num_shtcoins_destroyed += 1

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

    coin = Coin(img_file.split('.')[0].upper(), img, (x_pos-(IMG_SIZE/2), y_pos), random.randrange(2, 10)*0.1)
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
      ticker = img_file.split('.')[0].upper()

      if ticker != 'BTC' and random.randrange(0, 2) != 1:
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

      coin = Coin(ticker, img, (x_pos-(IMG_SIZE/2), y_pos), random.randrange(2, 10)*0.1)
      self.coins.append(coin)

      x_counter = x_counter + 1

  def update(self, dt):
    w, h = pygame.display.get_surface().get_size()

    self.btc_reward_timer_pos += dt*0.01
    self.btc_reward_timer_neg += dt*0.01

    if self.btc_reward_timer_pos >= 12:
      if self.btc_reward_accum_pos > 0:
        game.event_box.add_msg(format_btc_balance(self.btc_reward_accum_pos, True), (0, 255, 0))
        self.btc_reward_accum_pos = 0.0
  
      self.btc_reward_timer_pos = 0.0

    if self.btc_reward_timer_neg >= 8:
      if self.btc_reward_accum_neg > 0:
        game.event_box.add_msg(format_btc_balance(-1 * self.btc_reward_accum_neg, True), (255, 0, 0))
        self.btc_reward_accum_neg = 0.0

      self.btc_reward_timer_neg = 0.0

    self.spawn_coin_counter = self.spawn_coin_counter - dt * 0.1

    if self.spawn_coin_counter <= 0.0:
      self.spawn_coin()
      self.spawn_coin_counter = self.coin_spawn_rate
    
    for coin in self.coins:
      coin.update(dt)
      # check out of bounds
      if coin.position[1] > h:
        if coin.is_fork or coin.is_bitconnect:
          # lose 1 life.
          self.on_lose_life() # TODO: explanation.

        self.coins.remove(coin)

  def render(self, screen):
    for coin in self.coins:
      coin.render(screen)

class Button:
  def __init__(self, text, x, y, onclick):
    self.text = text
    self.position = (x, y)
    self.onclick = onclick
    
    self.rect = pygame.Surface((self.width, self.height))
    self.rect.fill((120, 120, 120))

  @property
  def padding(self):
    return (20, 10)

  @property
  def width(self):
    return text_width(self.text) + (self.padding[0]*2)

  @property
  def height(self):
    return text_height(self.text) + (self.padding[1] * 2)

  @property
  def is_hover(self):
    mpos = pygame.mouse.get_pos()
    x = self.position[0] - (self.width / 2)
    y = self.position[1] - (self.height / 2)
    return (mpos[0] > x and mpos[0] < x + self.width) and (mpos[1] > y and mpos[1] < y + self.height)

  @property
  def is_clicked(self):
    if self.is_hover and pygame.mouse.get_pressed()[0]:
      return True
    return False

  def render(self, screen):
    if self.is_hover:
      self.rect.fill((155, 155, 155))
    else:
      self.rect.fill((120, 120, 120))
    screen.blit(self.rect, (self.position[0] - (self.width / 2), self.position[1] - (self.height / 2)))
    left_border = pygame.Surface((2, self.height))
    left_border.fill((180, 180, 180))
    screen.blit(left_border, (self.position[0] - (self.width / 2), self.position[1] - (self.height / 2)))
    top_border = pygame.Surface((self.width, 2))
    top_border.fill((180, 180, 180))
    screen.blit(top_border, (self.position[0] - (self.width / 2), self.position[1] - (self.height/2)))
    right_border = pygame.Surface((2, self.height))
    right_border.fill((90, 90, 90))
    screen.blit(right_border, (self.position[0] + (self.width / 2), self.position[1] - (self.height / 2)))
    bottom_border = pygame.Surface((self.width + 2, 2))
    bottom_border.fill((90, 90, 90))
    screen.blit(bottom_border, (self.position[0] - (self.width / 2), self.position[1] + (self.height/2)))
    putstr(self.text, self.position[0] - (self.width / 2) + self.padding[0], self.position[1] - (self.height / 2) + self.padding[1])

class Screen:
  def __init__(self):
    self.buttons = []
    w, h = self.screen_size
    self.width = w
    self.height = h
    self.cooloff = 0

  def add_button(self, btn):
    self.buttons.append(btn)
  
  def remove_button(self, btn):
    self.buttons.pop(self.buttons.index(btn))

  @property
  def screen_size(self):
    return pygame.display.get_surface().get_size()

  def update(self, dt):
    self.cooloff += 0.01*dt
    left_click = pygame.mouse.get_pressed()[0]

    for btn in self.buttons:
      if self.cooloff > 1 and left_click and btn.is_hover:
        btn.onclick()

  def render(self, screen):
    for btn in self.buttons:
      btn.render(screen)

class StartScreen(Screen):
  def __init__(self):
    super().__init__()

    self.coins = []
    self.spawn_coin_counter = 0.0
    self.logo = Image("assetz/start1.png")
    self.logo.size(232, 52)
    self.logo.move(self.width/2-116, 160)

    #self.add_button()
    self.play_button = Button("Play!", self.width/2, self.height/2, self.play_button_click)
    self.add_button(self.play_button)
    self.about_button = Button("About", self.width/2, self.height/2 + 45, self.about_button_click)
    self.add_button(self.about_button)

  def play_button_click(self):
    game.current_screen = TutorialScreen()

  def about_button_click(self):
    game.current_screen = AboutScreen()

  def spawn_coin(self):
    idx = random.randrange(0, len(coin_logos))
    img_file = coin_logos[idx]

    img = Image("./coins/" + img_file)
    img.size(IMG_SIZE, IMG_SIZE)

    x_pos = random.randrange(img.rect.w/2, self.screen_size[0] - img.rect.w)
    y_pos = 0 - img.rect.h

    coin = Coin(img_file.split('.')[0].upper(), img, (x_pos-(IMG_SIZE/2), y_pos), random.randrange(2, 10)*0.1)
    self.coins.append(coin)

  def update(self, dt):
    super().update(dt)

    self.spawn_coin_counter = self.spawn_coin_counter - dt * 0.1

    if self.spawn_coin_counter <= 0.0:
      self.spawn_coin()
      self.spawn_coin_counter = 400

    for coin in self.coins:
      coin.update(dt)

      # check out of bounds
      if coin.position[1] > self.height:
        self.coins.remove(coin)

  def render(self, screen):
    for coin in self.coins:
      coin.render(screen)
    super().render(screen)
    self.logo.draw()

class YouDiedScreen(Screen):
  def __init__(self):
    super().__init__()

    self.restart_button = Button("Restart", self.width/2, self.height/2, self.restart_game)
    self.add_button(self.restart_button)

    self.quit_button = Button("Quit", self.width/2, self.height/2 + self.restart_button.height + 15, self.quit_game)
    self.add_button(self.quit_button)
  
  def restart_game(self):
    game.setup_game()
    game.current_screen = None

  def quit_game(self):
    game.current_screen = StartScreen()

  def render(self, screen):
    super().render(screen)

    putstr("Mission Failed", (self.width/2) - (text_width("Mission Failed")/2), 150)
    putstr("Unfortunately, you let too many sour coins get away!", (self.width/2) - (text_width("Unfortunately, you let too many sour coins get away!")/2), 175)
    putstr("Try again?", (self.width/2) - (text_width("Try again?")/2), 200)

class TutorialScreen(Screen):
  def __init__(self):
    super().__init__()

    self.play_button = Button("OK!", self.width/2, self.offset+(25 * len(self.tutorial_text))+60, self.play_button_click)
    self.add_button(self.play_button)
  
  def play_button_click(self):
    game.setup_game()
    game.current_screen = None

  @property
  def offset(self):
    return 100

  @property
  def tutorial_text(self):
    return [
      "Destroy coins to collect ₿. Do not destroy Bitcoins though, you will lose ₿!",
      "Reach the target ₿ goal to complete the level. Found in the top right corner.",
      "Do not let the sour coins escape! They emit a red glow.",
      "Letting three sour coins slip from your grasp is game over."
      "",
      "",
      "Control your ship",
      "A or Left Arrow - Move left",
      "D or Right Arrow - Move right",
      "W or Up Arrow - Accelerate forward",
      "Space bar - Fire lasers"
    ]

  def render(self, screen):
    super().render(screen)

    tutorial_text = self.tutorial_text
    putstr("How to Play", (self.width/2) - (text_width("How to Play")/2), self.offset)

    count = 1
    for s in tutorial_text:
      putstr(s, (self.width/2) - (text_width(s) / 2), self.offset + (count * 25))
      count += 1

class AboutScreen(Screen):
  def __init__(self):
    super().__init__()

    self.back_button = Button("Back to Menu", self.width/2, self.offset+(25 * len(self.about_text))+60, self.back_button_click)
    self.add_button(self.back_button)
  
  def back_button_click(self):
    game.current_screen = StartScreen()

  @property
  def offset(self):
    return 100

  @property
  def about_text(self):
    return [
      "This game was made by brothers Andrew and Ethan MacDonald in 2019 for Game Jam Challenge",
      "Programming by Andrew and Ethan",
      "Pixel art and font designed by Ethan",
      "Coin logos from github.com/atomiclabs/cryptocurrency-icons",
      "",
      "",
      "github.com/ajmd17",
      "github.com/emd22",
      "",
      "We both hope you enjoy this game!"
    ]

  def render(self, screen):
    super().render(screen)

    about_text = self.about_text
    putstr("About This Game", (self.width/2) - (text_width("About This Game")/2), self.offset)

    count = 1
    for s in about_text:
      putstr(s, (self.width/2) - (text_width(s) / 2), self.offset + (count * 25))
      count += 1

class LevelUpScreen(Screen):
  def __init__(self):
    super().__init__()

    self.skip_timer = 0.0
    self.next_level = game.current_level.difficulty + 1
    self.current_btc_target = game.current_level.btc_balance_target

    if self.has_won:
      self.back_button = Button("Back to Menu", self.width/2, 350, self.back_button_click)
      self.add_button(self.back_button)
  
  def back_button_click(self):
    game.current_screen = StartScreen()

  @property
  def has_won(self):
    return self.next_level > MAX_DIFFICULTY
  
  def update(self, dt):
    super().update(dt)

    if not self.has_won:
      self.skip_timer += 0.01*dt

      if self.skip_timer >= 30:
        game.setup_game(self.next_level)
        game.current_screen = None

  def render(self, screen):
    super().render(screen)

    if self.has_won:
      putstr("You won!!!", (self.width/2) - (text_width("You won!!!")/2), 150)
      putstr("Since this round, you have...", (self.width/2) - (text_width("Since this round, you have...")/2), 175)
      putstr("Destroyed " + str(game.stats.num_shtcoins_destroyed) + " sh-tcoins", (self.width/2) - (text_width("Destroyed " + str(game.stats.num_shtcoins_destroyed) + " sh-tcoins")/2), 200)
      putstr("Destroyed " + str(game.stats.num_sour_coins_destroyed) + " sour coins", (self.width/2) - (text_width("Destroyed " + str(game.stats.num_sour_coins_destroyed) + " sour coins")/2), 225)
      putstr("Destroyed " + str(game.stats.num_btc_destroyed) + " bitcoins", (self.width/2) - (text_width("Destroyed " + str(game.stats.num_btc_destroyed) + " bitcoins")/2), 250)
      putstr("Give yourself a pat on the back!", (self.width/2) - (text_width("Give yourself a pat on the back!")/2), 300)
      
    else:
      putstr("Level Cleared!", (self.width/2) - (text_width("Level Cleared!")/2), 150)
      putstr("Goal of " + format_btc_balance(self.current_btc_target) + " reached", (self.width/2) - (text_width("Goal of " + format_btc_balance(self.current_btc_target) + " reached")/2), 175)
      putstr("You are now on Level " + str(self.next_level), (self.width/2) - (text_width("You are now on Level " + str(self.next_level))/2), 200)

# sound stuff
class dummysound:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return dummysound()
    file = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'assetz', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print ('Warning, unable to load, %s' % file)
    return dummysound()

class Stats():
  def __init__(self):
    self.num_shtcoins_destroyed = 0
    self.num_btc_destroyed = 0
    self.num_sour_coins_destroyed = 0

class Game():
  def __init__(self):
    screen_info = pygame.display.Info()
    self.screen = pygame.display.set_mode((800, 600))
    w, h = pygame.display.get_surface().get_size()

    self.width = w
    self.height = h

    self.ship = Ship((w / 2), h - 15)
    self.stars = Stars()

    start_screen = StartScreen()
    self.current_screen = start_screen

    self.setup_game()

    self.life_icon = Image('./assetz/lightning.png')
    self.event_box = EventBox()

    self.sounds = {}

    for k in ['levelup', 'hurt', 'hurt2', 'coin', 'shoot']:
      self.sounds[k] = load_sound(k + '.wav')

    self.running = True

  def setup_game(self, level=1):
    if level == 1:
      self.stats = Stats()

    self.current_level = Level(level, (self.width, self.height), self.on_lose_life)
    self.dead = False
    self.num_lives = 3
    self.btc_balance = 0.0
    self.btc_laser_cost_accum = 0.0
    self.btc_laser_cost_timer = 0.0
    self.boost = 0.0
    self.ship.lasers = []

  @property
  def speed(self):
    return 1.0 + max(0.0, min(self.boost, 1.55))

  @property
  def playing(self):
    return (self.current_screen is None) and (not self.dead)

  def on_lose_life(self):
    self.sounds['hurt2'].play()
    self.num_lives = self.num_lives - 1

    if self.num_lives == 0:
      self.current_screen = YouDiedScreen()

  def check_events(self, dt):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.running = False
    
    keystate = pygame.key.get_pressed()

    if self.playing:

      key_move_left = keystate[K_LEFT] or keystate[K_a]
      key_move_right = keystate[K_RIGHT] or keystate[K_d]
      key_shoot = keystate[K_SPACE]

      if keystate[K_UP] or keystate[K_w]:
        self.boost = min(MAX_BOOST, self.boost + (dt * 0.008))
      else:
        self.boost = max(0, self.boost - dt * 0.01)

      if key_move_left and not key_move_right:
        if (self.ship.position[0] - (self.ship.img.rect.w / 2)) > 0:
          self.ship.move(-1 * (dt * 0.3), 0)
      elif key_move_right and not key_move_left:
        if (self.ship.position[0] + (self.ship.img.rect.w / 2)) < self.width:
          self.ship.move(dt * 0.3, 0)
      else:
        pass

      if key_shoot:
        game.ship.shoot()

        if game.btc_balance > 0:
          to_sub = (game.btc_balance * game.ship.mining_laser_cost)
          self.btc_laser_cost_accum += to_sub
          game.btc_balance = max(0, game.btc_balance - to_sub)

  def update(self, dt):
    if self.current_screen is not None:
      self.current_screen.update(dt)
    else:
      self.btc_laser_cost_timer += dt* 0.01
      if self.btc_laser_cost_timer >= 10:
        self.btc_laser_cost_timer = 0.0

        if self.btc_laser_cost_accum > 0.0:
          game.event_box.add_msg(format_btc_balance(-1 * self.btc_laser_cost_accum, True), (255, 0, 0))
          self.btc_laser_cost_accum = 0.0

      self.ship.update(dt)
      self.current_level.update(dt)
      self.event_box.update(dt)

      self.stars.move(0, dt*0.01)
      self.stars.update()
  
  def render(self):
    self.screen.fill((0, 0, 0))

    if self.current_screen is not None:
      self.current_screen.render(self.screen)
    else:
      self.stars.draw()
      self.current_level.render(self.screen)
      self.ship.render(self.screen)
      self.event_box.render(self.screen)

      for i in range(0, self.num_lives):
        self.screen.blit(self.life_icon.img, (30 + (45 * i), self.height - 50), self.life_icon.rect)

      putstr("level " + str(self.current_level.difficulty) + " / " + str(MAX_DIFFICULTY), 20, 10)
      putstr("mining laser power: " + format_btc_balance(self.ship.mining_laser_power) + "  /  mining laser cost: " + str(self.ship.mining_laser_cost * 100) + "%", 20, 25)

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