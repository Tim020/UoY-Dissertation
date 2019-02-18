from faker import Faker
import numpy as np
import random
import scipy.stats as stats

import Consts
from DriverModel import IDM
from Vehicle import Car, Truck


class Garage(object):
    def __init__(self, seed, short_seed, car_pct, truck_pct, car_speed,
                 truck_speed, car_speed_variance, truck_speed_variance):
        self._car_pct = car_pct
        car_min = (1 - (car_speed_variance / 100))
        car_max = (1 + (car_speed_variance / 100))
        self._car_velocities = stats.truncnorm(
            ((car_speed * car_min) - car_speed) / 4,
            ((car_speed * car_max) - car_speed) / 4,
            loc=car_speed, scale=4)
        self._car_velocities.random_state = np.random.RandomState(
            seed=short_seed)

        self._truck_pct = truck_pct
        truck_min = (1 - (truck_speed_variance / 100))
        truck_max = (1 + (truck_speed_variance / 100))
        self._truck_velocities = stats.truncnorm(
            ((truck_speed * truck_min) - truck_speed) / 4,
            ((truck_speed * truck_max) - truck_speed) / 4,
            loc=truck_speed, scale=4)
        self._truck_velocities.random_state = np.random.RandomState(
            seed=short_seed)

        self._random = random.Random(seed)
        self._uuid_generator = Faker()
        self._uuid_generator.seed_instance(seed)
        self._cars = 0
        self._trucks = 0
        if Consts.DEBUG_MODE:
            self._debug_file = open('debug/garage.txt', 'w')

    def new_vehicle(self):
        if self._random.randint(0, 99) < self._car_pct:
            vel = float(self._car_velocities.rvs(1)[0])
            new_vehicle = Car(self._uuid_generator.uuid4(), vel, 2, 3, 2, 2,
                              IDM)
            self._cars += 1
        else:
            vel = float(self._truck_velocities.rvs(1)[0])
            new_vehicle = Truck(self._uuid_generator.uuid4(), vel, 1, 2, 2, 4,
                                IDM)
            self._trucks += 1

        if Consts.DEBUG_MODE:
            self._debug_file.write('{}\n'.format(new_vehicle.__str__()))
            self._debug_file.write('{}\n'.format(new_vehicle.__str__()))
        return new_vehicle
