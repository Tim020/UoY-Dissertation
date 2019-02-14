#!/usr/bin/env python3

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

if __name__ == '__main__':
    environment = simpy.RealtimeEnvironment()
    bridge = Bridge.Bridge(environment, 100, 1)
    total_sim_time = SIMULATION_LENGTH * (SIMULATION_FREQUENCY / TIME_STEP)
    environment.run(until=total_sim_time)
