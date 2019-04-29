#!/usr/bin/env python3

'''
Motivation needed to complete this project, go Charmander!

              _.--""`-..
            ,'          `.
          ,'          __  `.
         /|          " __   \
        , |           / |.   .
        |,'          !_.'|   |
      ,'             '   |   |
     /              |`--'|   |
    |                `---'   |
     .   ,                   |                       ,".
      ._     '           _'  |                    , ' \ `
  `.. `.`-...___,...---""    |       __,.        ,`"   L,|
  |, `- .`._        _,-,.'   .  __.-'-. /        .   ,    \
-:..     `. `-..--_.,.<       `"      / `.        `-/ |   .
  `,         """"'     `.              ,'         |   |  ',,
    `.      '            '            /          '    |'. |/
      `.   |              \       _,-'           |       ''
        `._'               \   '"\                .      |
           |                '     \                `._  ,'
           |                 '     \                 .'|
           |                 .      \                | |
           |                 |       L              ,' |
           `                 |       |             /   '
            \                |       |           ,'   /
          ,' \               |  _.._ ,-..___,..-'    ,'
         /     .             .      `!             ,j'
        /       `.          /        .           .'/
       .          `.       /         |        _.'.'
        `.          7`'---'          |------"'_.'
       _,.`,_     _'                ,''-----"'
   _,-_    '       `.     .'      ,\
   -" /`.         _,'     | _  _  _.|
    ""--'---"""""'        `' '! |! /
                            `" " -'
'''

import csv
from decimal import *
import json
from multiprocessing import Process, Queue, Pipe
import os
import shutil
import simpy
import sys
import time

import Road
import Consts
import Display
import VehicleGarage


class Simulation(object):
    def __init__(self, env, finish_event, queue, conn, configuration):
        self.env = env
        self.finish_event = finish_event
        self.queue = queue
        self.conn = conn
        self.simulated_time = 0
        self.action = env.process(self.update(Consts.SIMULATION_FREQUENCY,
                                              Consts.TIME_STEP))
        self.road = Road.Road(Consts.SIMULATION_SEED,
                              Consts.ROAD_LENGTH,
                              Consts.BRIDGE_LANES,
                              Consts.SAFETIME_HEADWAY)
        if configuration:
            self.road.configure(configuration)

        if Consts.PLATOON_ADJUSTMENT:
            print('Adjusting car and truck percentage to account for platoons')
            print('Config car percentage : {} | Config truck percentage: {}'.format(Consts.CAR_PCT, Consts.TRUCK_PCT))
            avg_platoon_length = (Consts.MAX_PLATOON_LENGTH + Consts.MIN_PLATOON_LENGTH) / 2
            car_pct, truck_pct = Simulation.adjust_truck_percentage(Consts.TRUCK_PCT, Consts.TRUCK_PCT, Consts.PLATOON_CHANCE, avg_platoon_length)
            Consts.CAR_PCT = car_pct
            Consts.TRUCK_PCT = truck_pct
            print('Adjusted car percentage : {} | Adjusted truck percentage: {}'.format(car_pct, truck_pct))

        # self.road.add_safetime_headway_zone_all_lanes(245, 255, 10)
        # self.road.add_speed_limited_zone_all_lanes(250, 450, 10)
        # self.road.add_speed_limited_zone_all_lanes(75, 125, 10)
        # self.road.add_point_detector_all_lanes(150, 10)
        # self.road.add_space_detector_all_lanes(100, 200, 10)
        # self.road.add_space_detector_all_lanes(250, 450, 5)

        self.garage = VehicleGarage.Garage(Consts.SIMULATION_SEED,
                                           Consts.SIMULATION_SHORT_SEED,
                                           Consts.CAR_PCT, Consts.TRUCK_PCT,
                                           Consts.CAR_LENGTH,
                                           Consts.TRUCK_LENGTH,
                                           Consts.PLATOON_CHANCE,
                                           Consts.MIN_PLATOON_LENGTH,
                                           Consts.MAX_PLATOON_LENGTH,
                                           Consts.MIN_PLATOON_GAP,
                                           Consts.MAX_PLATOON_GAP)
        self.garage.configure_car_velocities(Consts.CAR_SPEED,
                                             Consts.CAR_SPEED_VARIANCE,
                                             Consts.CAR_SPEED_DISTRIBUTION)
        self.garage.configure_car_gaps(Consts.CAR_MINIMUM_GAP,
                                       Consts.CAR_GAP_VARIANCE,
                                       Consts.CAR_GAP_DISTRIBUTION)
        self.garage.configure_truck_velocities(Consts.TRUCK_SPEED,
                                               Consts.TRUCK_SPEED_VARIANCE,
                                               Consts.TRUCK_SPEED_DISTRIBUTION)
        self.garage.configure_truck_gaps(Consts.TRUCK_MINIMUM_GAP,
                                         Consts.TRUCK_GAP_VARIANCE,
                                         Consts.TRUCK_GAP_DISTRIBUTION)
        self.garage.configure_truck_weights(Consts.TRUCK_UNLOADED_WEIGHT,
                                            Consts.TRUCK_LOADED_WEIGHT,
                                            Consts.TRUCK_UNLOADED_WEIGHT_VARIANCE,
                                            Consts.TRUCK_LOADED_WEIGHT_VARIANCE)
        self._vehicle_timer = Decimal((60 * 60) / Consts.INFLOW_RATE)
        self._vehicle_count = Decimal(0)
        self._next_vehicle_in = Decimal(0)
        self._vehicle_failures = 0
        self._vehicles_per_hour = 0
        self.last_freq = 0
        self.last_t = 0
        self.queued_vehicles = []

    @staticmethod
    def adjust_truck_percentage(orig_truck, truck_pct, plat_pct,
                                plat_len):
        num_trucks = truck_pct * ((100 - plat_pct) / 100)
        num_plat = truck_pct * (plat_pct / 100) * plat_len
        cars = 100 - truck_pct
        if (num_trucks + num_plat) / (num_trucks + num_plat + cars) > (orig_truck / 100):
            return Simulation.adjust_truck_percentage(orig_truck,
                                                      truck_pct - 0.1,
                                                      plat_pct, plat_len)
        else:
            return 100 - int(truck_pct), int(truck_pct)

    def update(self, frequency, time_step):
        self.last_t = (Consts.SIMULATION_LENGTH - self.simulated_time) * (frequency / Consts.TIME_STEP)
        while True:
            self.simulated_time += time_step
            if self._next_vehicle_in <= time_step:
                lane = None
                if self.queued_vehicles:
                    lane, new_vehicle = self.queued_vehicles.pop(0)
                else:
                    new_vehicle = self.garage.new_vehicle()
                status, lane, num_vehicles = self.road.add_vehicle(new_vehicle, lane)
                if status:
                    self._vehicle_count += num_vehicles
                else:
                    self._vehicle_failures += num_vehicles
                    self.queued_vehicles.append((lane, new_vehicle))
                self._next_vehicle_in = self._vehicle_timer
            else:
                self._next_vehicle_in -= Decimal(time_step)

            assert(len(self.queued_vehicles) <= 1)

            self._vehicles_per_hour = int((self._vehicle_count / Decimal(self.simulated_time)) * 3600)

            self.road.update(time_step, self.simulated_time, self.queue)

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
            else:
                t = (Consts.SIMULATION_LENGTH - self.simulated_time) * (
                            frequency / Consts.TIME_STEP)
                if self.last_t - t > 1:
                    self.last_t = t
                    sys.stdout.write("\r\033[K")
                    sys.stdout.write("\rTime Remaining: {:.5f}s".format(t))
                    sys.stdout.flush()

            yield self.env.timeout(frequency)


def simulation_process(queue, conn, configuration, res, conf):
    print('Starting simulation with seed: {}'.format(Consts.SIMULATION_SEED))
    environment = simpy.RealtimeEnvironment(strict=False)
    finish_event = environment.event()
    simulation = Simulation(environment, finish_event, queue, conn, configuration)
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
    if os.getenv("HEADLESS"):
        print('\r')
    print('Simulation finished after {} seconds.'.format(int(end_time - start_time)))
    if queue:
        queue.put(False)
    if conn:
        while conn.poll():
            conn.recv()

    print('\tSimulated {} seconds and {} vehicles, {} veh/h'.
          format(int(simulation.simulated_time), simulation._vehicle_count,
                 simulation._vehicles_per_hour))

    print('\t[Bridge] {} calls, {} cars, {} trucks, {} inflow failures'.
          format(simulation.road._calls, simulation.road._cars,
                 simulation.road._trucks, simulation._vehicle_failures))

    pct_car = int(100 * (simulation.road._cars / (simulation.road._cars + simulation.road._trucks)))
    pct_truck = int(100 * (simulation.road._trucks / (simulation.road._cars + simulation.road._trucks)))
    print('\t[Bridge] {}% cars, {}% trucks'.format(pct_car, pct_truck))

    print('\t[Garage] {} cars, {} trucks, {} truck platoons'.
          format(simulation.garage._cars, simulation.garage._trucks,
                 simulation.garage._truck_platoons))

    res.append({
        'configuration_file': conf,
        'seed': Consts.SIMULATION_SEED,
        'time': int(simulation.simulated_time),
        'vehicles': simulation._vehicle_count,
        'flow': simulation._vehicles_per_hour,
        'cars': simulation.garage._cars,
        'trucks': simulation.garage._trucks,
        'truck_platoons': simulation.garage._truck_platoons,
        'car_pct': Consts.CAR_PCT,
        'truck_pct': Consts.TRUCK_PCT,
        'actual_car_pct': pct_car,
        'actual_truck_pct': pct_truck,
        'platoon_pct': Consts.PLATOON_CHANCE,
        'average_weight': simulation.road.road_detector.average_weight()
    })

    print('Writing detector output...')
    simulation.road.write_detector_output()
    print('Rendering detector graphs...')
    simulation.road.plot_detector_output()
    print('Rendering vehicle garage graphs...')
    simulation.garage.plot()
    print('Creating copy of the configuration file...')
    shutil.copy(conf, 'output/{}/{}'.format(Consts.BASE_OUTPUT_DIR, Consts.SIMULATION_SEED))
    print('Finished generating output to "output/{}/{}"'.format(Consts.BASE_OUTPUT_DIR, Consts.SIMULATION_SEED))


def display_process(queue, conn):
    display = Display.Display(1600, 900, Consts.ROAD_LENGTH,
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


if __name__ == '__main__':
    def run_simulation():
        Consts.configure_random()

        if Consts.MULTI_LANE:
            Consts.INFLOW_RATE = Consts.INFLOW_RATE * Consts.BRIDGE_LANES * 2

        for i in range(Consts.NUM_RUNS):
            if i != 0:
                Consts.generate_seed()

            print("\nStarting run {} of {}".format(i + 1, Consts.NUM_RUNS))

            if os.getenv("HEADLESS") is None:
                processes = []
                vehicle_queue = Queue()
                conns = Pipe(True)
                disp = Process(target=display_process, args=(vehicle_queue,
                                                             conns[1],))
                sim = Process(target=simulation_process, args=(vehicle_queue,
                                                               conns[0],
                                                               config,
                                                               results, conf))

                processes.append(sim)
                processes.append(disp)

                for process in processes:
                    process.start()

                for process in processes:
                    process.join()
            else:
                Consts.FORCE_DISPLAY_FREQ = False
                simulation_process(None, None, config, results, conf)

    if os.path.isdir('debug'):
        print('Removing old debug files\n')
        shutil.rmtree('debug')

    config = None
    results = []
    conf = None

    if len(sys.argv) > 1:
        Consts.BASE_OUTPUT_DIR = sys.argv[1]
        if len(sys.argv) >= 2:
            for arg in sys.argv[2:]:
                if os.path.isfile(arg):
                    conf = arg
                    f = open(arg)
                    config = json.loads(f.read())
                    f.close()
                    print('\nStarting simulation with config: {}'.format(arg))
                    Consts.load_from_json(config)
                    run_simulation()
                else:
                    print('Argument was not a file. Not sure what to do here, '
                          'so skipping argument: {}!'.format(arg))
                    continue
            else:
                run_simulation()
    else:
        run_simulation()

    counter = 0
    os.makedirs('output/global/{}/'.format(Consts.BASE_OUTPUT_DIR), exist_ok=True)
    while os.path.isfile('output/global/{}/simulation_{}.csv'.format(Consts.BASE_OUTPUT_DIR, counter)):
        counter += 1
    path = 'output/global/{}/simulation_{}.csv'.format(Consts.BASE_OUTPUT_DIR, counter)

    _file = open(path, 'w')
    csvwriter = csv.writer(_file)
    count = 0
    for d in results:
        if count == 0:
            header = d.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(d.values())
    _file.close()

    print('Written run results to: {}'.format(path))
