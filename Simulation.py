#!/usr/bin/env python3

import random
import simpy

import Bridge

# How often the simulation updates
SIMULATION_FREQUENCY = 2

# Length of simulation in seconds
SIMULATION_LENGTH = 10

# Simulation time step in seconds
TIME_STEP = 0.5

# Percentage distribution of cars and truck traffic
CAR_PCT = 80
TRUCK_PCT = 20

# Minimum distance to enforce between vehicles
MINUMUM_GAP = 2

# Length of the bridge for the simulation
BRIDGE_LENGTH = 200

# Seed used in this simulation - used to generate IDs of various things
SIMULATION_SEED = random.getrandbits(128)


class Simulation(object):
    def __init__(self, env):
        self.env = env
        self.simulated_time = 0
        self.action = env.process(self.update(SIMULATION_FREQUENCY, TIME_STEP))
        self.bridge = Bridge.Bridge(BRIDGE_LENGTH, 1)

    def update(self, frequency, time_step):
        while True:
            print('Update at {}, simulated time: {}s'.format(self.env.now,
                                                             self.simulated_time))

            self.bridge.update()

            self.simulated_time += time_step
            yield self.env.timeout(frequency)


if __name__ == '__main__':
    print('Starting simulation with seed: {}'.format(SIMULATION_SEED))
    environment = simpy.RealtimeEnvironment()
    simulation = Simulation(environment)
    total_sim_time = SIMULATION_LENGTH * (SIMULATION_FREQUENCY / TIME_STEP)
    environment.run(until=total_sim_time)
