import math
import pygame
from pygame.locals import DOUBLEBUF
import time


class Display(object):
    def __init__(self, W, H, bridge_length, bridge_lanes):
        pygame.init()

        self.bridge_length = bridge_length
        self.bridge_lanes = bridge_lanes
        self.bridge_tile_length = 16

        self.road = pygame.image.load("road.png")
        self.road = pygame.transform.scale(self.road, (int((self.road.get_size()[0] * 3)), int((self.road.get_size()[1] * 3))))

        self.road_top = pygame.image.load("road_top.png")
        self.road_top = pygame.transform.scale(self.road_top, (int((self.road_top.get_size()[0] * 3)), int((self.road_top.get_size()[1] * 3))))

        self.road_bottom = pygame.image.load("road_bottom.png")
        self.road_bottom = pygame.transform.scale(self.road_bottom, (int((self.road_bottom.get_size()[0] * 3)), int((self.road_bottom.get_size()[1] * 3))))

        self.road_single = pygame.image.load("road_single.png")
        self.road_single = pygame.transform.scale(self.road_single, (int((self.road_single.get_size()[0] * 3)), int((self.road_single.get_size()[1] * 3))))

        assert(self.road.get_size() == self.road_top.get_size() == self.road_bottom.get_size() == self.road_single.get_size())

        self.car = pygame.image.load("car.png")
        self.car = pygame.transform.scale(self.car, (int(self.car.get_size()[0] >> 3), int(self.car.get_size()[1] >> 3)))

        self.truck = pygame.image.load("truck.png")
        self.truck = pygame.transform.scale(self.truck, (int(self.truck.get_size()[0] >> 1), int(self.truck.get_size()[1] >> 1)))

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

        W = math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0]
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

        self.background = pygame.Surface((W + 20, H))
        self.background.fill((0, 128, 0))
        for lane_num in range(self.bridge_lanes):
            for tile_num in range(math.ceil(self.bridge_length / self.bridge_tile_length) + 2):
                if self.bridge_lanes == 1:
                    self.background.blit(self.road_single, (10 + ((tile_num - 1) * self.road_single.get_size()[0]), 10 + (lane_num * self.road_single.get_size()[1])))
                elif lane_num == 0:
                    self.background.blit(self.road_top, (10 + ((tile_num - 1) * self.road_top.get_size()[0]), 10 + (lane_num * self.road_top.get_size()[1])))
                elif lane_num == self.bridge_lanes - 1:
                    self.background.blit(self.road_bottom, (10 + ((tile_num - 1) * self.road_bottom.get_size()[0]), 10 + (lane_num * self.road_bottom.get_size()[1])))
                else:
                    self.background.blit(self.road, (10 + ((tile_num - 1) * self.road.get_size()[0]), 10 + (lane_num * self.road.get_size()[1])))

        pygame.display.set_caption('Traffic Simulation Tool')

    def paint(self, vehicle_data):
        t = time.time()
        for _ in pygame.event.get():
            pass

        self.screen.blit(self.background,  (0, 0))

        updates = []
        for i, lane in enumerate(vehicle_data):
            for vehicle in lane:
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
                y_position = int(self.lane_positions[i] - (sprite.get_size()[1] / 2))
                updates.append(self.screen.blit(sprite, (x_position, y_position)))

        pygame.display.update(updates)
        pygame.display.set_caption('Traffic Simulation Tool | {:.2f}'.format(time.time() - t))

    def cleanup(self):
        pygame.quit()
