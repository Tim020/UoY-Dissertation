#!/usr/bin/env python3

from decimal import *
import simpy
import sys

import Bridge
import Consts
import VehicleGarage


class Simulation(object):
    def __init__(self, env):
        self.env = env
        self.simulated_time = 0
        self.action = env.process(self.update(Consts.SIMULATION_FREQUENCY, Consts.TIME_STEP))
        self.bridge = Bridge.Bridge(Consts.SIMULATION_SEED, Consts.BRIDGE_LENGTH, 1)
        self.garage = VehicleGarage.Garage(Consts.SIMULATION_SHORT_SEED, Consts.CAR_PCT, Consts.TRUCK_PCT, 33, 22)
        self.vps = Decimal(Consts.INFLOW_RATE / 60 / 60)
        self._vehicle_timer = Decimal((60 * 60) / Consts.INFLOW_RATE)
        self._vehicle_count = Decimal(0)
        self._next_vehicle_in = Decimal(0)
        self._vehicle_failures = 0

    def update(self, frequency, time_step):
        while True:
            self.simulated_time += time_step
            # print('Update at {}, simulated time: {}s'.format(self.env.now, self.simulated_time))
            if self._next_vehicle_in <= 0:
                new_vehicle = self.garage.new_vehicle()
                if self.bridge.add_vehicle(new_vehicle):
                    # print('New vehicle added')
                    self._vehicle_count += 1
                else:
                    # print('Could not add new vehicle at this time')
                    self._vehicle_failures += 1
                    pass
                self._next_vehicle_in = self._vehicle_timer
            else:
                self._next_vehicle_in -= Decimal(time_step)
            self.bridge.update()

            yield self.env.timeout(frequency)


if __name__ == '__main__':
    # If there is an argument given, treat it as the seed for the simulation
    if len(sys.argv) > 1:
        Consts.SIMULATION_SEED = int(sys.argv[1])
        Consts.SIMULATION_SHORT_SEED = Consts.SIMULATION_SEED >> (128 - 32)

    print('Starting simulation with seed: {}'.format(Consts.SIMULATION_SEED))

    environment = simpy.RealtimeEnvironment()
    simulation = Simulation(environment)
    total_sim_time = Consts.SIMULATION_LENGTH * (Consts.SIMULATION_FREQUENCY / Consts.TIME_STEP)
    environment.run(until=total_sim_time)

    print(
        'Simulation Finished. Simulated {} seconds and {} vehicles, '
        '[bridge] {} calls, {} cars, {} trucks, [garage] {} cars, {} trucks '
        'and {} inflow failures'.format(simulation.simulated_time,
                                        simulation._vehicle_count,
                                        simulation.bridge._calls,
                                        simulation.bridge._cars,
                                        simulation.bridge._trucks,
                                        simulation.garage._cars,
                                        simulation.garage._trucks,
                                        simulation._vehicle_failures))
