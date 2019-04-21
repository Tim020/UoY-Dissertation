import math
import os
import pygame
from pygame.locals import DOUBLEBUF
import time

import Consts


class Display(object):

    def __init__(self, W, H, bridge_length, bridge_lanes):
        pygame.init()

        self.bridge_length = bridge_length
        self.bridge_lanes = bridge_lanes
        self.bridge_tile_length = 16

        base_path = os.path.abspath(os.path.dirname(__file__))
        self.road = pygame.image.load(os.path.join(base_path, 'resources', "road.png"))
        self.road = pygame.transform.scale(self.road, (int((self.road.get_size()[0] * 3)), int((self.road.get_size()[1] * 3))))

        self.road_top = pygame.image.load(os.path.join(base_path, 'resources', "road_top.png"))
        self.road_top = pygame.transform.scale(self.road_top, (int((self.road_top.get_size()[0] * 3)), int((self.road_top.get_size()[1] * 3))))

        self.road_bottom = pygame.image.load(os.path.join(base_path, 'resources', "road_bottom.png"))
        self.road_bottom = pygame.transform.scale(self.road_bottom, (int((self.road_bottom.get_size()[0] * 3)), int((self.road_bottom.get_size()[1] * 3))))

        self.road_single = pygame.image.load(os.path.join(base_path, 'resources', "road_single.png"))
        self.road_single = pygame.transform.scale(self.road_single, (int((self.road_single.get_size()[0] * 3)), int((self.road_single.get_size()[1] * 3))))

        assert(self.road.get_size() == self.road_top.get_size() == self.road_bottom.get_size() == self.road_single.get_size())

        self.car = pygame.image.load(os.path.join(base_path, 'resources', "car.png"))
        self.car = pygame.transform.scale(self.car, (int(self.car.get_size()[0] >> 3), int(self.car.get_size()[1] >> 3)))

        self.truck = pygame.image.load(os.path.join(base_path, 'resources', "truck.png"))
        self.truck = pygame.transform.scale(self.truck, (int(self.truck.get_size()[0] >> 1), int(self.truck.get_size()[1] >> 1)))

        self.truck_platoon = pygame.image.load(os.path.join(base_path, 'resources', "truck_platoon.png"))
        self.truck_platoon = pygame.transform.scale(self.truck_platoon, (int(self.truck_platoon.get_size()[0] >> 1), int(self.truck_platoon.get_size()[1] >> 1)))

        disp_info = pygame.display.Info()
        desired_width = max(W, math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0])
        scale_factor = 1
        if desired_width > disp_info.current_w:
            scale_factor = math.ceil(desired_width / disp_info.current_w)

        self.road = pygame.transform.scale(self.road, (int((self.road.get_size()[0] / scale_factor)), int((self.road.get_size()[1] / scale_factor))))
        self.road_top = pygame.transform.scale(self.road_top, (int((self.road_top.get_size()[0] / scale_factor)), int((self.road_top.get_size()[1] / scale_factor))))
        self.road_bottom = pygame.transform.scale(self.road_bottom, (int((self.road_bottom.get_size()[0] / scale_factor)), int((self.road_bottom.get_size()[1] / scale_factor))))
        self.road_single = pygame.transform.scale(self.road_single, (int((self.road_single.get_size()[0] / scale_factor)), int((self.road_single.get_size()[1] / scale_factor))))

        self.car = pygame.transform.scale(self.car, (int(self.car.get_size()[0] / scale_factor), int(self.car.get_size()[1] / scale_factor)))
        self.truck = pygame.transform.scale(self.truck, (int(self.truck.get_size()[0] / scale_factor), int(self.truck.get_size()[1] / scale_factor)))
        self.truck_platoon = pygame.transform.scale(self.truck_platoon, (int(self.truck_platoon.get_size()[0] / scale_factor), int(self.truck_platoon.get_size()[1] / scale_factor)))

        W = math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0]
        H = (self.bridge_lanes * self.road.get_size()[1]) + 20
        self.bridge_pixels = math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0]

        self.lane_positions = []
        for lane_num in range(self.bridge_lanes):
            self.lane_positions.append(int(10 + (lane_num * self.road.get_size()[1]) + (self.road.get_size()[1] / 4)))
            self.lane_positions.append(int(10 + (lane_num * self.road.get_size()[1]) + self.road.get_size()[1] - (self.road.get_size()[1] / 4)))

        self.screen = pygame.display.set_mode((W + 20, H), DOUBLEBUF)

        self.road = self.road.convert_alpha()
        self.road_top = self.road_top.convert_alpha()
        self.road_bottom = self.road_bottom.convert_alpha()
        self.road_single = self.road_single.convert_alpha()
        self.car = self.car.convert_alpha()
        self.truck = self.truck.convert_alpha()
        self.truck_platoon = self.truck_platoon.convert_alpha()

        self.background = pygame.Surface((W + 20, H))
        self.road_surface = pygame.Surface((W + 20, self.bridge_lanes * self.road.get_size()[1]))
        self.background.fill((0, 128, 0))
        for lane_num in range(self.bridge_lanes):
            for tile_num in range(math.ceil(self.bridge_length / self.bridge_tile_length) + 2):
                if self.bridge_lanes == 1:
                    self.background.blit(self.road_single, (10 + ((tile_num - 1) * self.road_single.get_size()[0]), (lane_num * self.road_single.get_size()[1]) + 10))
                    self.road_surface.blit(self.road_single, (10 + ((tile_num - 1) * self.road_single.get_size()[0]), (lane_num * self.road_single.get_size()[1])))
                elif lane_num == 0:
                    self.background.blit(self.road_top, (10 + ((tile_num - 1) * self.road_top.get_size()[0]), (lane_num * self.road_top.get_size()[1]) + 10))
                    self.road_surface.blit(self.road_top, (10 + ((tile_num - 1) * self.road_top.get_size()[0]), (lane_num * self.road_top.get_size()[1])))
                elif lane_num == self.bridge_lanes - 1:
                    self.background.blit(self.road_bottom, (10 + ((tile_num - 1) * self.road_bottom.get_size()[0]), (lane_num * self.road_bottom.get_size()[1]) + 10))
                    self.road_surface.blit(self.road_bottom, (10 + ((tile_num - 1) * self.road_bottom.get_size()[0]), (lane_num * self.road_bottom.get_size()[1])))
                else:
                    self.background.blit(self.road, (10 + ((tile_num - 1) * self.road.get_size()[0]), (lane_num * self.road.get_size()[1]) + 10))
                    self.road_surface.blit(self.road, (10 + ((tile_num - 1) * self.road.get_size()[0]), (lane_num * self.road.get_size()[1])))

        self.screen.blit(self.background, (0, 0))
        pygame.display.update()

        pygame.display.set_caption('Traffic Simulation Tool')

        self.vehicles = {}
        self.all = pygame.sprite.RenderUpdates()
        Display.Vehicle.containers = self.all
        self.remaining_time = 0
        self.simulated_time = 0

    def paint(self, vehicle_data, conn):
        t = time.time()
        for _ in pygame.event.get():
            pass

        self.all.clear(self.screen, self.background)

        v_keys = []
        for i, lane in enumerate(vehicle_data):
            for vehicle in lane:
                v_keys.append(vehicle[2])
                l = i if i < self.bridge_lanes else (i * -1) + (self.bridge_lanes - 1)
                if l >= 0:
                    x_position = int((vehicle[1] / self.bridge_length) * self.bridge_pixels) + 10
                else:
                    x_position = int(((self.bridge_length - vehicle[1]) / self.bridge_length) * self.bridge_pixels) - 10
                if vehicle[0] == 'Car':
                    if l >= 0:
                        sprite = self.car
                        x_position = x_position - sprite.get_size()[0]
                    else:
                        sprite = pygame.transform.flip(self.car, True, False)
                elif vehicle[0] == 'Truck':
                    if l >= 0:
                        sprite = self.truck
                        x_position = x_position - sprite.get_size()[0]
                    else:
                        sprite = pygame.transform.flip(self.truck, True, False)
                elif vehicle[0] == 'Platooned Truck':
                    if l >= 0:
                        sprite = self.truck_platoon
                        x_position = x_position - sprite.get_size()[0]
                    else:
                        sprite = pygame.transform.flip(self.truck_platoon, True, False)
                y_position = int(self.lane_positions[i] - (sprite.get_size()[1] / 2))
                if vehicle[2] not in self.vehicles:
                    self.vehicles[vehicle[2]] = Display.Vehicle(sprite)

                self.vehicles[vehicle[2]].update_position(x_position, y_position)

        remove_keys = []
        for k in self.vehicles:
            if k not in v_keys:
                remove_keys.append(k)
        for k in remove_keys:
            obj = self.vehicles.pop(k)
            obj.kill()

        updates = self.all.draw(self.screen)
        pygame.display.update(updates)

        if Consts.FORCE_DISPLAY_FREQ:
            if conn:
                conn.send(time.time() - t)

        while conn.poll():
            data = conn.recv()
            self.remaining_time = data[0]
            self.simulated_time = data[1]

        pygame.display.set_caption('Traffic Simulation Tool | {:.5f} | {:.5f} s | {:.5f} s'.format(time.time() - t, self.remaining_time, self.simulated_time))

    def cleanup(self):
        pygame.quit()

    class Vehicle(pygame.sprite.Sprite):
        def __init__(self, sprite):
            pygame.sprite.Sprite.__init__(self, self.containers)
            self.image = sprite
            self.rect = self.image.get_rect()

        def update_position(self, xpos, ypos):
            self.rect.x = xpos
            self.rect.y = ypos
