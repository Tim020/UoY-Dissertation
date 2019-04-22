#!/usr/bin/env python3

'''
Motivation needed to complete this project, go Charmander!

               _,........__
            ,-'            "`-.
          ,'                   `-.
        ,'                        \
      ,'                           .
      .'\               ,"".       `
     ._.'|             / |  `       \
     |   |            `-.'  ||       `.
     |   |            '-._,'||       | \
     .`.,'             `..,'.'       , |`-.
     l                       .'`.  _/  |   `.
     `-.._'-   ,          _ _'   -" \  .     `
`."""""'-.`-...,---------','         `. `....__.
.'        `"-..___      __,'\          \  \     \
\_ .          |   `""""'    `.           . \     \
  `.          |              `.          |  .     L
    `.        |`--...________.'.        j   |     |
      `._    .'      |          `.     .|   ,     |
         `--,\       .            `7""' |  ,      |
            ` `      `            /     |  |      |    _,-'"""`-.
             \ `.     .          /      |  '      |  ,'          `.
              \  v.__  .        '       .   \    /| /              \
               \/    `""\"""""""`.       \   \  /.''                |
                `        .        `._ ___,j.  `/ .-       ,---.     |
                ,`-.      \         ."     `.  |/        j     `    |
               /    `.     \       /         \ /         |     /    j
              |       `-.   7-.._ .          |"          '         /
              |          `./_    `|          |            .     _,'
              `.           / `----|          |-............`---'
                \          \      |          |
               ,'           )     `.         |
                7____,,..--'      /          |
                                  `---.__,--.'
'''

from decimal import *
from multiprocessing import Process, Queue, Pipe
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
    def __init__(self, env, finish_event, queue, conn):
        self.env = env
        self.finish_event = finish_event
        self.queue = queue
        self.conn = conn
        self.simulated_time = 0
        self.action = env.process(self.update(Consts.SIMULATION_FREQUENCY,
                                              Consts.TIME_STEP))
        self.bridge = Bridge.Bridge(Consts.SIMULATION_SEED,
                                    Consts.BRIDGE_LENGTH,
                                    Consts.BRIDGE_LANES, 1)
        # self.bridge.add_safetime_headway_zone_all_lanes(245, 255, 10)
        # self.bridge.add_speed_limited_zone_all_lanes(250, 450, 10)
        # self.bridge.add_speed_limited_zone_all_lanes(75, 125, 10)
        self.bridge.add_point_detector_all_lanes(150, 60)
        self.bridge.add_space_detector_all_lanes(100, 200, 60)
        # self.bridge.add_space_detector_all_lanes(250, 450, 5)
        self.garage = VehicleGarage.Garage(Consts.SIMULATION_SEED,
                                           Consts.SIMULATION_SHORT_SEED,
                                           Consts.CAR_PCT, Consts.TRUCK_PCT,
                                           Consts.CAR_SPEED,
                                           Consts.TRUCK_SPEED,
                                           Consts.CAR_SPEED_VARIANCE,
                                           Consts.TRUCK_SPEED_VARIANCE,
                                           Consts.PLATOON_CHANCE,
                                           Consts.MIN_PLATOON_LENGTH,
                                           Consts.MAX_PLATOON_LENGTH,
                                           Consts.MIN_PLATOON_GAP,
                                           Consts.MAX_PLATOON_GAP)
        self._vehicle_timer = Decimal((60 * 60) / Consts.INFLOW_RATE)
        self._vehicle_count = Decimal(0)
        self._next_vehicle_in = Decimal(0)
        self._vehicle_failures = 0
        self._vehicles_per_hour = 0
        self.last_freq = 0

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

            if self.conn and Consts.FORCE_DISPLAY_FREQ:
                self.last_freq = frequency
                new_frequency = frequency
                while self.conn.poll():
                    # Never go faster than the desired update frequency
                    new_frequency = max(self.conn.recv(),
                                        Consts.SIMULATION_FREQUENCY)

                if (abs(((self.last_freq + new_frequency) / 2) - frequency) / frequency) * 100 > 10:
                    frequency = new_frequency

            elif frequency != Consts.SIMULATION_FREQUENCY:
                frequency = Consts.SIMULATION_FREQUENCY

            if self.conn:
                self.conn.send(((Consts.SIMULATION_LENGTH - self.simulated_time) * (frequency / Consts.TIME_STEP), self.simulated_time))

            yield self.env.timeout(frequency)


def simulation_process(queue, conn):
    print('Starting simulation with seed: {}'.format(Consts.SIMULATION_SEED))
    environment = simpy.RealtimeEnvironment(strict=False)
    finish_event = environment.event()
    simulation = Simulation(environment, finish_event, queue, conn)
    total_sim_time = Consts.SIMULATION_LENGTH * (
            Consts.SIMULATION_FREQUENCY / Consts.TIME_STEP)

    print('Estimated simulation run time: {} seconds'.format(total_sim_time))
    if Consts.FORCE_DISPLAY_FREQ:
        print('[WARNING] Forcing simulation to sync with display. '
              'Simulation may take longer than estimated')

    start_time = time.time()
    environment.sync()
    environment.run(until=finish_event)
    end_time = time.time()
    print('Simulation finished after {} seconds.'.format(int(end_time - start_time)))
    if queue:
        queue.put(False)
    if conn:
        while conn.poll():
            conn.recv()

    simulation.bridge.write_detector_output()

    print('\tSimulated {} seconds and {} vehicles, {} veh/h'.
          format(int(simulation.simulated_time), simulation._vehicle_count,
                 simulation._vehicles_per_hour))

    print('\t[Bridge] {} calls, {} cars, {} trucks, {} inflow failures'.
          format(simulation.bridge._calls, simulation.bridge._cars,
                 simulation.bridge._trucks, simulation._vehicle_failures))

    print('\t[Garage] {} cars, {} trucks, {} truck platoons'.
          format(simulation.garage._cars, simulation.garage._trucks,
                 simulation.garage._truck_platoons))


def display_process(queue, conn):
    display = Display.Display(1600, 900, Consts.BRIDGE_LENGTH,
                              Consts.BRIDGE_LANES)
    running = True
    start = time.time()
    while running:
        vehicle_data = queue.get()
        if type(vehicle_data) is list:
            display.paint(vehicle_data, conn)
        elif vehicle_data is False:
            running = False
            while conn.poll():
                conn.recv()
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

    if not Consts.SINGLE_LANE:
        Consts.INFLOW_RATE = Consts.INFLOW_RATE * Consts.BRIDGE_LANES * 2

    if os.getenv("HEADLESS") is None:
        processes = []
        vehicle_queue = Queue()
        conns = Pipe(True)
        disp = Process(target=display_process, args=(vehicle_queue,
                                                     conns[1],))
        sim = Process(target=simulation_process, args=(vehicle_queue,
                                                       conns[0],))

        processes.append(sim)
        processes.append(disp)

        for process in processes:
            process.start()

        for process in processes:
            process.join()
    else:
        Consts.FORCE_DISPLAY_FREQ = False
        simulation_process(None, None)
