#!/usr/bin/env python3

from decimal import *
from multiprocessing import Process, Queue
import os
import shutil
import simpy
import sys
import time

import Bridge
import Consts
import Display
import VehicleGarage


class Simulation(object):
    def __init__(self, env, finish_event, queue):
        self.env = env
        self.finish_event = finish_event
        self.queue = queue
        self.simulated_time = 0
        self.action = env.process(self.update(Consts.SIMULATION_FREQUENCY,
                                              Consts.TIME_STEP))
        self.bridge = Bridge.Bridge(Consts.SIMULATION_SEED,
                                    Consts.BRIDGE_LENGTH,
                                    Consts.BRIDGE_LANES, 1)
        # self.bridge.add_safetime_headway_zone_all_lanes(65, 80, 5)
        # self.bridge.add_speed_limited_zone_all_lanes(250, 450, 10)
        # self.bridge.add_point_detector_all_lanes(150, 1)
        # self.bridge.add_space_detector_all_lanes(100, 200, 5)
        # self.bridge.add_space_detector_all_lanes(250, 450, 5)
        self.garage = VehicleGarage.Garage(Consts.SIMULATION_SEED,
                                           Consts.SIMULATION_SHORT_SEED,
                                           Consts.CAR_PCT, Consts.TRUCK_PCT,
                                           33, 22, Consts.CAR_SPEED_VARIANCE,
                                           Consts.TRUCK_SPEED_VARIANCE)
        self._vehicle_timer = Decimal((60 * 60) / Consts.INFLOW_RATE)
        self._vehicle_count = Decimal(0)
        self._next_vehicle_in = Decimal(0)
        self._vehicle_failures = 0
        self._vehicles_per_hour = 0

    def update(self, frequency, time_step):
        while True:
            self.simulated_time += time_step
            if self._next_vehicle_in <= time_step:
                new_vehicle = self.garage.new_vehicle()
                if self.bridge.add_vehicle(new_vehicle):
                    self._vehicle_count += 1
                else:
                    self._vehicle_failures += 1
                    pass
                self._next_vehicle_in = self._vehicle_timer
            else:
                self._next_vehicle_in -= Decimal(time_step)

            self._vehicles_per_hour = int((self._vehicle_count / Decimal(self.simulated_time)) * 3600)

            self.bridge.update(time_step, self.simulated_time, self.queue)

            if self.simulated_time >= Consts.SIMULATION_LENGTH:
                self.finish_event.succeed()

            yield self.env.timeout(frequency)


def simulation_process(queue):
    print('Starting simulation with seed: {}'.format(Consts.SIMULATION_SEED))
    environment = simpy.RealtimeEnvironment()
    finish_event = environment.event()
    simulation = Simulation(environment, finish_event, queue)
    total_sim_time = Consts.SIMULATION_LENGTH * (
            Consts.SIMULATION_FREQUENCY / Consts.TIME_STEP)
    start_time = time.time()
    environment.run(until=finish_event)
    end_time = time.time()
    print('Simulation finished after {} seconds.'.format(int(end_time - start_time)))
    queue.put(False)

    simulation.bridge.write_detector_output()

    print('\tSimulated {} seconds and {} vehicles, {} veh/h'.
          format(int(simulation.simulated_time), simulation._vehicle_count,
                 simulation._vehicles_per_hour))

    print('\t[Bridge] {} calls, {} cars, {} trucks, {} inflow failures'.
          format(simulation.bridge._calls, simulation.bridge._cars,
                 simulation.bridge._trucks, simulation._vehicle_failures))

    print('\t[Garage] {} cars, {} trucks '.format(simulation.garage._cars,
                                                  simulation.garage._trucks))


def display_process(queue):
    display = Display.Display(1600, 900, Consts.BRIDGE_LENGTH,
                              Consts.BRIDGE_LANES)
    running = True
    start = time.time()
    while running:
        vehicle_data = queue.get()
        if type(vehicle_data) is list:
            display.paint(vehicle_data)
        elif vehicle_data is False:
            running = False
    end = time.time()
    print('Display finished after {} seconds.'.format(int(end - start)))
    display.cleanup()


def sink_process(queue):
    running = True
    while running:
        data = queue.get()
        if type(data) is bool and data is False:
            running = False


if __name__ == '__main__':
    if os.path.isdir('debug'):
        print('Removing old debug files')
        shutil.rmtree('debug')
    # If there is an argument given, treat it as the seed for the simulation
    if len(sys.argv) > 1:
        Consts.SIMULATION_SEED = int(sys.argv[1])
        Consts.SIMULATION_SHORT_SEED = Consts.SIMULATION_SEED >> (128 - 32)

    processes = []
    vehicle_queue = Queue()

    sim = Process(target=simulation_process, args=(vehicle_queue,))
    processes.append(sim)
    if os.getenv("HEADLESS") is None:
        disp = Process(target=display_process, args=(vehicle_queue,))
    else:
        disp = Process(target=sink_process, args=(vehicle_queue,))
    processes.append(disp)

    for process in processes:
        process.start()

    for process in processes:
        process.join()
