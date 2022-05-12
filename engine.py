import pygame
import os
import sys
import math
from pygame.locals import *
from abc import ABC, abstractmethod
os.environ["SDL_VIDEO_CENTERED"] = "1"

root = os.path.dirname(__file__).replace("\\", "/")


class Game(ABC):
    def __init__(self, game_container):
        self.game_container = game_container

    @abstractmethod
    def check_events(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def render(self, screen):
        pass


class GameContainer:
    def __init__(self, width=320, height=220, scale=3, title="NilEngine"):
        self.screen_width = width
        self.screen_height = height
        self.scale = scale
        self.window_width = self.screen_width * self.scale
        self.window_height = self.screen_height * self.scale
        self.screen = pygame.Surface((self.screen_width, self.screen_height))
        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        self.title = title
        pygame.display.set_caption(self.title)
        self.running = False
        self.game = None
        self.fps = 0

    def run(self):
        if self.game == None:
            raise ValueError("Please set the game")
        target_fps = 60
        clock = pygame.time.Clock()

        self.running = True
        while self.running:
            dt = clock.tick(target_fps) * .001
            self.fps = clock.get_fps()
            self.game.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.game.check_events(event)
            self.screen.fill((0,0,0))
            self.game.render(self.screen)
            scaled_screen = pygame.transform.scale(self.screen, (self.window_width, self.window_height))
            self.window.blit(scaled_screen, (0,0))
            pygame.display.flip()
        pygame.quit()
        sys.exit(0)

    def set_game(self, game):
        self.game = game

    def get_window_size(self):
        return (self.window.width, self.window.height)

    def get_screen_size(self):
        return (self.screen.width, self.screen.height)

    def get_window(self):
        return self.window

    def get_screen(self):
        return self.screen


class State(ABC):
    def __init__(self, game_container, state_handler):
        self.game_container = game_container
        self.state_handler = state_handler

    @abstractmethod
    def check_events(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def render(self, screen):
        pass

    def reset(self):
        self.__init__(self.game_container, self.state_handler)


class StateHandler:
    def __init__(self, game_container):
        self.game_container = game_container
        self.states = {}
        self.current_state = ""

    def check_events(self, event):
        if not self.current_state == "":
            self.states[self.current_state].check_events(event)

    def update(self, dt):
        if not self.current_state == "":
            self.states[self.current_state].update(dt)

    def render(self, screen):
        if not self.current_state == "":
            self.states[self.current_state].render(screen)

    def set_state(self, tag, state):
        if not tag in self.states:
            self.states[tag] = state

    def set_current_state(self, tag):
        self.current_state = tag
        self.states[self.current_state].reset()

    def get_states(self):
        return self.states

    def get_current_state(self):
        return self.current_stat


class PhysicsObject(object):
    def __init__(self, x, y, width, height, offset):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.offset = offset
        self.rect = pygame.Rect(self.x, self.y, self.width-self.offset[2], self.height-self.offset[3])

    def get_collision_list(self, physics_objects):
        collision_list = []
        for obj in physics_objects:
            if self.rect.colliderect(obj.physics_obj.rect):
                collision_list.append(obj)
        return collision_list
    
    def check_events(self, event):
        pass

    def move(self, collision_objects, movement):
        self.rect.x += movement[0]
        collision_types = {"left":False,"right":False,"top":False,"bottom":False}
        for obj in self.get_collision_list(collision_objects):
            if movement[0] > 0:
                self.rect.right = obj.physics_obj.rect.left
                collision_types["right"] = True
            elif movement[0] < 0:
                self.rect.left = obj.physics_obj.rect.right
                collision_types["left"] = True

        self.rect.y += movement[1]
        for obj in self.get_collision_list(collision_objects):
            if movement[1] > 0:
                self.rect.bottom = obj.physics_obj.rect.top
                collision_types["bottom"] = True
            elif movement[1] < 0:
                self.rect.top = obj.physics_obj.rect.bottom
                collision_types["top"] = True

        return collision_types

    def render(self, screen):
        pygame.draw.rect(screen, (255,0,0), self.rect, 1)

    def get_pos(self):
        return [self.rect.x, self.rect.y]

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y


class Entity(ABC):
    def __init__(self, game_container, entity_handler, x, y, width, height, texture=None, offset=[0,0,0,0], speed=2, debug=False, tag="entity"):
        self.game_container = game_container
        self.entity_handler = entity_handler
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.texture = texture
        self.physics_obj = PhysicsObject(self.x, self.y, self.width, self.height, offset)
        self.vel = [0,0]
        self.speed = speed
        self.debug = debug
        self.offset = offset
        self.tag = tag
        self.dt = 0
        self.dir = {"left":False, "right":False, "up":False, "down":False}
        self.rect = pygame.Rect(self.physics_obj.rect.x-self.offset[0], self.physics_obj.rect.y-self.offset[1], self.width, self.height)

    def check_events(self, event):
        pass

    def update(self, dt):
        self.physics_obj.move(self.entity_handler.get_all_entities_except(self.tag), self.vel)

    def default_update(self, dt):
        self.rect.x = self.physics_obj.rect.x - self.offset[0]
        self.rect.y = self.physics_obj.rect.y - self.offset[1]
        self.dt = dt

    def render(self, screen):
        if self.texture == None:
            pygame.draw.rect(screen, (0,255,0), self.rect)
        else:
            screen.blit(self.texture, (self.rect.x, self.rect.y))

    def default_render(self, screen):
        if self.debug:
            self.physics_obj.render(screen)

    def set_pos(self, x, y):
        self.physics_obj.set_pos(x,y)

    def add_collision_obj(self, obj:[]):
        for o in obj:
            self.collision_objs.append(o)

    def remove_collision_obj(self, obj:[]):
        for o in obj:
            self.collision_objs.remove(o)


class EntityHandler:
    def __init__(self):
        self.entities = []

    def check_events(self, event):
        for entity in self.entities:
            entity.check_events(event)

    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)
            entity.default_update(dt)

    def render(self, screen):
        for entity in self.entities:
            entity.render(screen)
            entity.default_render(screen)

    def add_entity(self, entity):
        self.entities.append(entity)

    def remove_entity(self, entity):
        self.entities.remove(entity)

    def get_entities(self):
        return self.entities

    def get_entities_except(self, tag):
        entities = []
        for entity in self.entities:
            if entity.tag != tag:
                entities.append(entity)
        return entities

    def get_entity_by_tag(self, tag):
        for entity in self.entities:
            if entity.tag == tag:
                return entity
        return "ENTITY"
                
                

def crop(path, x, y, width, height):
    image = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    sheet = pygame.image.load(root + path)
    image.blit(sheet, (0,0), (x * width, y * height, width, height))
    return image


class Animation:
    def __init__(self, path, image_width, image_height, images, frame_duration, *color_keys):
        self.images = []
        self.color_keys = color_keys
        self.timer = 0
        self.frame_count = 0
        self.frame_duration = frame_duration
        for y in range(images[1]):
            for x in range(images[0]):
                image = crop(path, x, y, image_width, image_height)
                self.images.append(image)
        for image in self.images:
            for key in self.color_keys:
                for y in range(image.get_height()):
                    for x in range(image.get_width()):
                        if image.get_at((x,y)) == key:
                            image.set_at((x,y), (1,1,1))
            image.set_colorkey((1,1,1))

    def render_animation(self, screen, x, y, dt, flip):
        self.timer += dt
        current_frame = self.images[self.frame_count]
        real_frame_duration = 0
        try:
            real_frame_duration = self.frame_duration[self.frame_count]
        except:
            real_frame_duration = self.frame_duration
        if self.timer >= real_frame_duration:
            self.frame_count += 1
            self.timer = 0
        if self.frame_count >= len(self.images):
            self.frame_count = 0

        if flip:
            current_frame = pygame.transform.flip(current_frame, True, False)

        screen.blit(current_frame, (x,y))


class AnimationHandler:
    def __init__(self):
        self.animation_database = {}
        self.current_animation = ""
        self.flip = False

    def render(self, screen, x, y, dt):
        if self.current_animation not in self.animation_database:
            raise KeyError("Please set an animation before rendering")
        self.animation_database[self.current_animation].render_animation(screen, x, y, dt, self.flip)

    def get_animation_database(self):
        return self.animation_database

    def set_animation(self, tag, animation):
        if tag in self.animation_database:
            raise KeyError("Animation {} is already in self.animation_database".format(tag))
        self.animation_database[tag] = animation

    def set_current_animation(self, tag, flip=False):
        if not tag in self.animation_database:
            raise KeyError("Animation {} is already in self.animation_database".format(tag))
        self.current_animation = tag
        self.flip = flip

    def get_current_animation(self):
        return self.current_animation


class Font:
    default = pygame.image.load(root + "/engine_images/large_font.png")
    default_small = pygame.image.load(root + "/engine_images/small_font.png")
    def __init__(self, game_container, font_img=default, color=(255,255,255)):
        self.game_container = game_container
        self.font_img = font_img
        self.character_order = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','.','-',',',':','+','\'','!','?','0','1','2','3','4','5','6','7','8','9','(',')','/','_','=','\\','[',']','*','"','<','>',';']
        self.characters = {}
        alpha_color = (127,127,127)
        count = 0
        last_x = 0
        self.character_spacing = 2
        self.space_size = 4
        for x in range(self.font_img.get_width()):
            if self.font_img.get_at((x,0)) == alpha_color:
                width = x - last_x
                surf = pygame.Surface((width - 1, self.font_img.get_height()), pygame.SRCALPHA)
                surf = surf.convert_alpha()
                surf.blit(self.font_img, (0,0), (last_x + 1, 0, width, self.font_img.get_height()))
                self.characters[self.character_order[count]] = surf
                last_x = x
                count += 1
        for char in self.characters:
            for y in range(self.characters[char].get_height()):
                for x in range(self.characters[char].get_width()):
                    if self.characters[char].get_at((x,y)) == (255,0,0):
                        self.characters[char].set_at((x,y), color)
                        self.characters[char].set_colorkey((0,0,0))

    def render_text(self, screen, text, x, y):
        x_offset = 0
        for char in text:
            if char != " ":
                screen.blit(self.characters[char], (x + x_offset, y))
                x_offset += self.characters[char].get_width() + self.character_spacing
            else:
                x_offset += self.space_size

    def get_text_size(self, text):
        width = 0
        height = 0
        for char in text:
            if char != " ":
                width += self.characters[char].get_width() + self.character_spacing
                height = self.characters[char].get_height()
            else:
                width += self.space_size
        return (width, height)



class UIButton:
    def default_click_func():
        print("{} has been clicked".format(__class__))
        
    def __init__(self, game_container, x, y, width, height, color=(100,100,100), click_func=default_click_func, text="", text_color=(255,255,255), centered=False, scale=1, border_radius=3):
        self.game_container = game_container
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.click_func = click_func
        self.scale = scale
        self.text =  text
        self.hovering = False
        self.centered = centered
        self.border_radius = border_radius
        self.font = Font(self.game_container, color=text_color)
        self.color = color
        if centered:
            self.x -= int(width / 2 * scale)
            self.y -= int(height / 2 * scale)


    def render(self, screen):
        current_color = self.color
        if self.text != "":
            text_size = self.font.get_text_size(self.text)
            if text_size[0] > self.width:
                self.x += int(self.width / 2 * self.scale)
                self.width = text_size[0]
                self.x -= int(text_size[0] / 2)
            if text_size[1] > self.height:
                self.height += int(self.height / 2 * self.scale)
                self.height = text_size[1]
                self.y -= int(text_size[1] / 2)
        surf = pygame.Surface((self.width, self.height))
        pygame.draw.rect(surf, current_color, (0, 0, self.width, self.height), border_radius=self.border_radius)
        if self.text != "":
            text_size = self.font.get_text_size(self.text)
            text_x = math.ceil(self.width / 2) - math.ceil(text_size[0] / 2) + 1
            text_y = math.ceil(self.height / 2) - math.ceil(text_size[1] / 2) + 2
            self.font.render_text(surf, self.text, text_x, text_y)
        if self.hovering:
            surf_overlay = surf.copy()
            for y in range(surf_overlay.get_height()):
                for x in range(surf_overlay.get_width()):
                    if surf_overlay.get_at((x,y)) != (0,0,0):
                        surf_overlay.set_at((x,y), (255,255,255))
            surf_overlay.set_colorkey((0,0,0))
            surf_overlay.set_alpha(75)
            surf.blit(surf_overlay, (0,0))
        surf.set_colorkey((0,0,0))
        scaled_surf = pygame.transform.scale(surf, (self.width * self.scale, self.height * self.scale))
        screen.blit(scaled_surf, (self.x, self.y))

    def update(self, dt):
        mouse_x = int(pygame.mouse.get_pos()[0] / self.game_container.scale)
        mouse_y = int(pygame.mouse.get_pos()[1] / self.game_container.scale)
        mouse_rect = pygame.Rect(mouse_x, mouse_y, 1, 1)
        rect = pygame.Rect(self.x, self.y, self.width * self.scale, self.height * self.scale)

        self.hovering = False
        if rect.colliderect(mouse_rect):
            self.hovering = True

    def check_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.hovering:
                    self.click_func()

class UIButtonHandler:
    def __init__(self):
        self.buttons = {}

    def check_events(self, event):
        for button in self.buttons.values():
            button.check_events(event)

    def render(self, screen):
        for button in self.buttons.values():
            button.render(screen)

    def update(self, dt):
        for button in self.buttons.values():
            button.update(dt) 

    def set_button(self, tag, button):
        self.buttons[tag] = button

    def get_button(self, tag):
        return self.buttons[tag]