import math
import random
import pygame
from pygame.locals import DOUBLEBUF


class Display(object):
    def __init__(self, W, H, bridge_length, bridge_lanes):
        pygame.init()

        self.bridge_length = bridge_length
        self.bridge_lanes = bridge_lanes
        self.bridge_tile_length = 16

        self.road = pygame.image.load("road_2.png")
        self.road = pygame.transform.scale(self.road, (int((self.road.get_size()[0] * 3)), int((self.road.get_size()[1] * 3))))
        self.car = pygame.image.load("car2.png")
        self.car = pygame.transform.scale(self.car, (int(self.car.get_size()[0] >> 3), int(self.car.get_size()[1] >> 3)))
        self.truck = pygame.image.load("truck.png")
        self.truck = pygame.transform.scale(self.truck, (int(self.truck.get_size()[0] >> 1), int(self.truck.get_size()[1] >> 1)))

        disp_info = pygame.display.Info()
        desired_width = max(W, math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0])
        scale_factor = 1
        if desired_width > disp_info.current_w:
            scale_factor = math.ceil(desired_width / disp_info.current_w)

        self.road = pygame.transform.scale(self.road, (int((self.road.get_size()[0] / scale_factor)), int((self.road.get_size()[1] / scale_factor))))
        self.car = pygame.transform.scale(self.car, (int(self.car.get_size()[0] / scale_factor), int(self.car.get_size()[1] / scale_factor)))
        self.truck = pygame.transform.scale(self.truck, (int(self.truck.get_size()[0] / scale_factor), int(self.truck.get_size()[1] / scale_factor)))

        W = math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0]
        self.bridge_pixels = math.ceil(bridge_length / self.bridge_tile_length) * self.road.get_size()[0]

        self.lane_positions = []
        for lane_num in range(self.bridge_lanes):
            self.lane_positions.append(int(10 + (lane_num * self.road.get_size()[1]) + (self.road.get_size()[1] / 4)))
            self.lane_positions.append(int(10 + (lane_num * self.road.get_size()[1]) + self.road.get_size()[1] - (self.road.get_size()[1] / 4)))

        self.screen = pygame.display.set_mode((W + 20, H))

    def paint(self, vehicle_data):
        for _ in pygame.event.get():
            pass

        self.screen.fill((0, 128, 0))
        pygame.display.update()
        for lane_num in range(self.bridge_lanes):
            for tile_num in range(math.ceil(self.bridge_length / self.bridge_tile_length)):
                self.screen.blit(self.road, (10 + (tile_num * self.road.get_size()[0]), 10 + (lane_num * self.road.get_size()[1])))

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
                        x_position = x_position + sprite.get_size()[0]
                elif vehicle[0] == 'Truck':
                    if l >= 0:
                        sprite = self.truck
                        x_position = x_position - sprite.get_size()[0]
                    else:
                        sprite = pygame.transform.flip(self.truck, True, False)
                        x_position = x_position + sprite.get_size()[0]
                y_position = int(self.lane_positions[i] - (sprite.get_size()[1] / 2))
                self.screen.blit(sprite, (x_position, y_position))

        # blit
        pygame.display.flip()

    def cleanup(self):
        pygame.quit()
