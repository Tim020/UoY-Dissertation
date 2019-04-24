from faker import Faker
import numpy as np
import os
import random
import scipy.stats as stats

import Consts
from DriverModel import IDM, TruckPlatoon
from Utils import MixtureModel
from Vehicle import Car, Truck, PlatoonedTruck


class Garage(object):
    def __init__(self, seed, short_seed, car_pct, truck_pct, car_length,
                 truck_length, platoon_chance, min_platoon_length,
                 max_platoon_length, min_platoon_gap, max_platoon_gap):
        self._seed = seed
        self._short_seed = short_seed
        
        self._car_pct = car_pct
        self._car_velocities = None
        self._car_gaps = None
        self._car_length = car_length
        self._generated_car_velocities = []
        self._generated_car_gaps = []

        self._truck_pct = truck_pct
        self._truck_velocities = None
        self._truck_gaps = None
        self._truck_length = truck_length
        self._generated_truck_velocities = []
        self._generated_truck_gaps = []
        self._truck_unloaded_weights = None
        self._truck_loaded_weights = None
        self._truck_weights = None
        self._generated_truck_weights = []

        self._platoon_pct = platoon_chance
        self._min_platoon_length = min_platoon_length
        self._max_platoon_length = max_platoon_length
        self._platoon_lengths = random.Random(seed)
        self._min_platoon_gap = min_platoon_gap
        self._max_platoon_gap = max_platoon_gap
        self._platoon_gaps = random.Random(seed)

        self._random = random.Random(seed)
        self._uuid_generator = Faker()
        self._uuid_generator.seed_instance(seed)
        self._cars = 0
        self._trucks = 0
        self._truck_platoons = 0
        if Consts.DEBUG_MODE:
            self._debug_file = open('debug/garage.txt', 'w')

        path = 'output/{}{}'
        if os.path.isdir(path.format(self._seed, '')):
            counter = 0
            while os.path.isdir(path.format(self._seed, ':{}'.format(counter))):
                counter += 1
            self.path = path.format(self._seed, ':{}'.format(counter))
        else:
            self.path = path.format(self._seed, '')
            
    def configure_car_velocities(self, car_speed, car_speed_variance, car_speed_dist):
        car_min_speed = (1 - (car_speed_variance / 100))
        car_max_speed = (1 + (car_speed_variance / 100))
        if car_speed_variance > 0 and car_speed_dist == 0:
            car_std_speed = ((car_speed * car_max_speed) - (
                        car_speed * car_min_speed)) / 4
            self._car_velocities = stats.truncnorm(
                ((car_speed * car_min_speed) - car_speed) / car_std_speed,
                ((car_speed * car_max_speed) - car_speed) / car_std_speed,
                loc=car_speed, scale=car_std_speed)
        elif car_speed_variance == 0 or car_speed_dist == 1:
            self._car_velocities = stats.uniform(
                loc=(car_speed * car_min_speed),
                scale=(car_speed * car_max_speed) - car_speed)
        else:
            raise RuntimeError('Could not configure car velocities with the '
                               'given settings!')
        self._car_velocities.random_state = np.random.RandomState(
            seed=self._short_seed)
    
    def configure_car_gaps(self, car_gap, car_gap_variance, car_gap_dist):
        car_min_gap = (1 - (car_gap_variance / 100))
        car_max_gap = (1 + (car_gap_variance / 100))
        if car_gap_variance > 0 and car_gap_dist == 0:
            car_std_gap = ((car_gap * car_max_gap) - (
                        car_gap * car_min_gap)) / 4
            self._car_gaps = stats.truncnorm(
                ((car_gap * car_min_gap) - car_gap) / car_std_gap,
                ((car_gap * car_max_gap) - car_gap) / car_std_gap,
                loc=car_gap, scale=car_std_gap
            )
        elif car_gap_variance == 0 or car_gap_dist == 1:
            self._car_gaps = stats.uniform(
                loc=(car_gap * car_min_gap),
                scale=(car_gap * car_max_gap) - car_gap)
        else:
            raise RuntimeError('Could not configure car minimum gaps with the '
                               'given settings!')
        self._car_gaps.random_state = np.random.RandomState(
            seed=self._short_seed)

    def configure_truck_velocities(self, truck_speed, truck_speed_variance, truck_speed_dist):
        truck_min_speed = (1 - (truck_speed_variance / 100))
        truck_max_speed = (1 + (truck_speed_variance / 100))
        if truck_speed_variance > 0 and truck_speed_dist == 0:
            truck_std_speed = ((truck_speed * truck_max_speed) - (truck_speed * truck_min_speed)) / 4
            self._truck_velocities = stats.truncnorm(
                ((truck_speed * truck_min_speed) - truck_speed) / truck_std_speed,
                ((truck_speed * truck_max_speed) - truck_speed) / truck_std_speed,
                loc=truck_speed, scale=truck_std_speed)
        elif truck_speed_variance == 0 or truck_speed_dist == 1:
            self._truck_velocities = stats.uniform(
                loc=(truck_speed * truck_min_speed),
                scale=(truck_speed * truck_max_speed) - truck_speed)
        else:
            raise RuntimeError('Could not configure truck velocities with the '
                               'given settings!')
        self._truck_velocities.random_state = np.random.RandomState(
            seed=self._short_seed)

    def configure_truck_gaps(self, truck_gap, truck_gap_variance, truck_gap_dist):
        truck_min_gap = (1 - (truck_gap_variance / 100))
        truck_max_gap = (1 + (truck_gap_variance / 100))
        if truck_gap_variance > 0 and truck_gap_dist == 0:
            truck_std_gap = ((truck_gap * truck_max_gap) - (
                        truck_gap * truck_min_gap)) / 4
            self._truck_gaps = stats.truncnorm(
                ((truck_gap * truck_min_gap) - truck_gap) / truck_std_gap,
                ((truck_gap * truck_max_gap) - truck_gap) / truck_std_gap,
                loc=truck_gap, scale=truck_std_gap
            )
        elif truck_gap_variance == 0 or truck_gap_dist == 1:
            self._truck_gaps = stats.uniform(
                loc=(truck_gap * truck_min_gap),
                scale=(truck_gap * truck_max_gap) - truck_gap)
        else:
            raise RuntimeError('Could not configure truck minimum gaps with '
                               'the given settings!')
        self._truck_gaps.random_state = np.random.RandomState(
            seed=self._short_seed)

    def configure_truck_weights(self, unloaded_weight, loaded_weight,
                                unloaded_variance, loaded_variance):
        unloaded_min = (1 - (unloaded_variance / 100))
        unloaded_max = (1 + (unloaded_variance / 100))

        loaded_min = (1 - (loaded_variance / 100))
        loaded_max = (1 + (loaded_variance / 100))

        if unloaded_variance > 0:
            unloaded_std = ((unloaded_weight * unloaded_max) - (unloaded_weight * unloaded_min)) / 4
            self._truck_unloaded_weights = stats.truncnorm(
                ((unloaded_weight * unloaded_min) - unloaded_weight) / unloaded_std,
                ((unloaded_weight * unloaded_max) - unloaded_weight) / unloaded_std,
                loc=unloaded_weight, scale=unloaded_std
            )
        else:
            self._truck_unloaded_weights = stats.uniform(
                loc=(unloaded_weight * unloaded_min),
                scale=(unloaded_weight * unloaded_max) - unloaded_weight
            )
        self._truck_unloaded_weights.random_state = np.random.RandomState(
            seed=self._short_seed)

        if loaded_variance > 0:
            loaded_std = ((loaded_weight * loaded_max) - (loaded_weight * loaded_min)) / 4
            self._truck_loaded_weights = stats.truncnorm(
                ((loaded_weight * loaded_min) - loaded_weight) / loaded_std,
                ((loaded_weight * loaded_max) - loaded_weight) / loaded_std,
                loc=loaded_weight, scale=loaded_std
            )
        else:
            self._truck_loaded_weights = stats.uniform(
                loc=(loaded_weight * loaded_min),
                scale=(loaded_weight * loaded_max) - loaded_weight
            )
        self._truck_loaded_weights.random_state = np.random.RandomState(
            seed=self._short_seed)

        self._truck_weights = MixtureModel([self._truck_unloaded_weights,
                                            self._truck_loaded_weights])
        self._truck_weights.random_state = np.random.RandomState(
            seed=self._short_seed)

    def new_vehicle(self):
        if self._random.randint(0, 100) < self._car_pct:
            vel = float(self._car_velocities.rvs(1)[0])
            gap = float(self._car_gaps.rvs(1)[0])
            new_vehicle = Car(self._uuid_generator.uuid4(), vel, 0.73, 1.67,
                              gap, self._car_length, IDM, 2000)
            self._cars += 1
            self._generated_car_velocities.append(vel)
            self._generated_car_gaps.append(gap)
        else:
            vel = float(self._truck_velocities.rvs(1)[0])
            if self._random.randint(0, 100) < self._platoon_pct:
                new_vehicle = []
                platoon_gap = self._platoon_gaps.randint(self._min_platoon_gap,
                                                         self._max_platoon_gap)
                platoon_length = self._platoon_lengths.randint(
                    self._min_platoon_length, self._max_platoon_length)
                for i in range(platoon_length):
                    new_vehicle.append(
                        PlatoonedTruck(self._uuid_generator.uuid4(), vel,
                                       0.73, 1.67, 2, self._truck_length,
                                       TruckPlatoon, 44000, i == 0,
                                       platoon_gap))
                    self._trucks += 1
                self._truck_platoons += 1
            else:
                gap = float(self._truck_gaps.rvs(1)[0])
                weight = float(self._truck_weights.rvs(1)[0])
                new_vehicle = Truck(self._uuid_generator.uuid4(), vel, 0.73,
                                    1.67, gap, self._truck_length, IDM, weight)
                self._trucks += 1
                self._generated_truck_velocities.append(vel)
                self._generated_truck_gaps.append(gap)
                self._generated_truck_weights.append(weight)

        if Consts.DEBUG_MODE:
            if type(new_vehicle) is not list:
                self._debug_file.write('{}\n'.format(new_vehicle.__str__()))
            else:
                self._debug_file.write('[{}]\n'.format(','.join(x.__str__() for x in new_vehicle)))
        return new_vehicle

    def plot(self):
        os.makedirs(self.path, exist_ok=True)
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        rcParams['axes.titlepad'] = 40

        f, axarr = plt.subplots(2, 3, squeeze=False)

        if self._generated_car_velocities:
            axarr[0, 0].hist(self._generated_car_velocities, density=True, ec="k")
            axarr[0, 0].set_xlabel('Desired Car Velocity (m/s)')
            axarr[0, 0].set_ylabel('Density')
        if self._generated_car_gaps:
            axarr[0, 1].hist(self._generated_car_gaps, density=True, ec="k")
            axarr[0, 1].set_xlabel('Desired Car Minimum Gap (m)')
            axarr[0, 1].set_ylabel('Density')
        if self._generated_truck_velocities:
            axarr[1, 0].hist(self._generated_truck_velocities, density=True, ec="k")
            axarr[1, 0].set_xlabel('Desired Truck Velocity (m/s)')
            axarr[1, 0].set_ylabel('Density')
        if self._generated_truck_gaps:
            axarr[1, 1].hist(self._generated_truck_gaps, density=True, ec="k")
            axarr[1, 1].set_xlabel('Desired Truck Minimum Gap (m)')
            axarr[1, 1].set_ylabel('Density')
        if self._generated_truck_weights:
            axarr[1, 2].hist(self._generated_truck_weights, density=True, ec="k")
            axarr[1, 2].set_xlabel('Truck Wights (m)')
            axarr[1, 2].set_ylabel('Density')

        f.suptitle('Data from Vehicle Generation', fontsize=12, y=0.99)
        plt.subplots_adjust(top=0.85)
        plt.tight_layout()
        f.set_size_inches(16, 9)
        plt.savefig('{}/garage.png'.format(self.path), dpi=300)
        plt.close(f)
