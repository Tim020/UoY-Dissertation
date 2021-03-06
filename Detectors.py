from collections import defaultdict
import csv
import json
import os

import Consts


class Detector(object):
    def __init__(self, lane, time_interval):
        self.lane = lane
        self.time_interval = time_interval
        self.next_macro_update = self.time_interval
        self.microscopic_data = defaultdict(dict)
        self.macroscopic_data = defaultdict(dict)

        path = 'output/{}/{}{}/detectors/{}'

        if os.path.isdir(path.format(Consts.BASE_OUTPUT_DIR,
                                     Consts.SIMULATION_SEED, '', self.lane)):
            counter = 0
            while os.path.isdir(path.format(Consts.BASE_OUTPUT_DIR,
                                            Consts.SIMULATION_SEED,
                                            ':{}'.format(counter), self.lane)):
                counter += 1
            self.path = path.format(Consts.BASE_OUTPUT_DIR,
                                    Consts.SIMULATION_SEED,
                                    ':{}'.format(counter), self.lane)
        else:
            self.path = path.format(Consts.BASE_OUTPUT_DIR,
                                    Consts.SIMULATION_SEED, '', self.lane)

    def get_name(self):
        raise NotImplementedError

    def tick(self, time_step, simulated_time, vehicles):
        raise NotImplementedError

    def get_plot_labels(self):
        raise NotImplementedError

    def write_results(self):
        # JSON output
        os.makedirs(self.path, exist_ok=True)
        _file = open('{}/{}.json'.format(self.path, self.get_name()), 'w')
        results = {
            'micro': self.microscopic_data,
            'macro': self.macroscopic_data
        }
        _file.write(json.dumps(results))
        _file.close()

        # CSV output macroscopic
        _file = open('{}/{}_macro.csv'.format(self.path, self.get_name()), 'w')
        csvwriter = csv.writer(_file)
        count = 0
        for d in self.macroscopic_data:
            data = self.macroscopic_data[d]
            data['timestamp'] = d
            if count == 0:
                header = data.keys()
                csvwriter.writerow(header)
                count += 1
            csvwriter.writerow(data.values())
            del data['timestamp']
        _file.close()

    def plot(self):
        os.makedirs(self.path, exist_ok=True)
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        rcParams['axes.titlepad'] = 40

        if not list(self.macroscopic_data.keys()):
            return

        k = list(self.macroscopic_data.keys())[0]
        timestamps = []
        data_points = defaultdict(list)

        for d in self.macroscopic_data:
            timestamps.append(d)
            for key in self.macroscopic_data[d]:
                data_points[key].append(self.macroscopic_data[d][key])

        for plot in data_points:
            f, axarr = plt.subplots(1)

            axarr.plot(timestamps, data_points[plot])
            axarr.set_xlabel('Time (s)')
            axarr.set_ylabel(self.get_plot_labels()[plot])
            axarr.grid(False)

            plt.subplots_adjust(top=0.85)
            plt.tight_layout()
            f.set_size_inches(16, 9)
            plt.rcParams.update({'font.size': 16})
            plt.savefig('{}/{}-{}.png'.format(self.path, self.get_name(), plot),
                        dpi=300, bbox_inches='tight', pad_inches=0.15)
            plt.close(f)


def calc_harmonic_mean(data):
    if type(data) is not list:
        raise ValueError('Type of data should be list, got {}'.format(type(data)))
    total = 0
    for x in data:
        if x != 0:
            total += 1/x
    if total == 0:
        return 0
    else:
        return len(data) / total


class PointDetector(Detector):
    def __init__(self, lane, position, time_interval):
        super().__init__(lane, time_interval)
        self.position = position
        self.speeds = []
        self.vehicle_count = 0

    def get_name(self):
        return 'Point Detector: {}'.format(self.position)

    def tick(self, time_step, simulated_time, vehicles):
        for vehicle in vehicles:
            if vehicle.position >= self.position > vehicle.prev_position:
                self.microscopic_data[vehicle._id] = {
                    'timestamp': simulated_time,
                    'velocity': vehicle.velocity,
                    'time_headway': vehicle.get_safetime_headway()
                }
                self.speeds.append(vehicle.velocity)
                self.vehicle_count += 1

        if self.next_macro_update <= time_step:
            self.macroscopic_data[simulated_time] = {
                'time_mean_velocity': ((sum(self.speeds) / len(self.speeds))
                                       if self.speeds else 0),
                'space_mean_velocity': calc_harmonic_mean(self.speeds),
                'flow': int((3600 / self.time_interval) * self.vehicle_count)
            }
            self.speeds = []
            self.vehicle_count = 0
            self.next_macro_update = self.time_interval
        else:
            self.next_macro_update -= time_step

    def get_plot_labels(self):
        return {
            'time_mean_velocity': 'Time Mean Velocity (m/s)',
            'space_mean_velocity': 'Space Mean Velocity (m/s)',
            'flow': 'Flow (veh/h)'
        }


class SpaceDetector(Detector):
    def __init__(self, lane, start, end, time_interval):
        super().__init__(lane, time_interval)
        self.start = start
        self.end = end
        self.vehicle_count = 0
        self.in_progress_vehicles = defaultdict(lambda: defaultdict(list))

    def get_name(self):
        return 'Space Detector: {}-{}'.format(self.start, self.end)

    def tick(self, time_step, simulated_time, vehicles):
        for vehicle in vehicles:
            if self.end > vehicle.position >= self.start:
                self.in_progress_vehicles[vehicle._id]['velocity'].append(
                    vehicle.velocity)
                self.in_progress_vehicles[vehicle._id]['space_headway'].append(
                    vehicle.gap)
            elif vehicle._id in self.in_progress_vehicles:
                vehicle_data = self.in_progress_vehicles.pop(vehicle._id)

                velocities = vehicle_data['velocity']
                gaps = vehicle_data['space_headway']

                self.microscopic_data[vehicle._id] = {
                    'space_mean_velocity': ((sum(velocities) / len(velocities))
                                            if velocities else 0),
                    'average_space_headway': ((sum(gaps) / len(gaps))
                                              if gaps else 0)
                }

        if self.next_macro_update <= time_step:
            velocities = []
            weights = []
            num_vehicles = 0
            for vehicle in vehicles:
                if vehicle._id in self.in_progress_vehicles:
                    velocities.append(vehicle.velocity)
                    weights.append(vehicle.weight)
                    num_vehicles += 1

            assert(num_vehicles == len(self.in_progress_vehicles))

            self.macroscopic_data[simulated_time] = {
                'space_mean_velocity': ((sum(velocities) / len(velocities))
                                       if velocities else 0),
                'density': ((len(self.in_progress_vehicles) / ((self.end - self.start) / 1000))
                            if self.in_progress_vehicles else 0),
                'weight_load': sum(weights)
            }

            self.next_macro_update = self.time_interval
        else:
            self.next_macro_update -= time_step

    def get_plot_labels(self):
        return {
            'space_mean_velocity': 'Space Mean Velocity (m/s)',
            'density': 'Flow (veh/km)',
            'weight_load': 'Weight Load (kg)'
        }


class RoadDetector(Detector):
    def __init__(self, time_interval):
        super().__init__('road', time_interval)

    def get_name(self):
        return 'Bridge Detector'

    def average_weight(self):
        weights = []
        for k in self.macroscopic_data:
            weights.append(self.macroscopic_data[k]['weight_load'])
        if weights:
            return sum(weights) / len(weights)
        else:
            return 0

    def tick(self, time_step, simulated_time, vehicles):
        if self.next_macro_update <= time_step:
            weight_load = []
            velocities = []
            for vehicle in vehicles:
                weight_load.append(vehicle.weight)
                velocities.append(vehicle.velocity)

            self.macroscopic_data[simulated_time] = {
                'space_mean_velocity': ((sum(velocities) / len(velocities))
                                       if velocities else 0),
                'weight_load': sum(weight_load)
            }

            self.next_macro_update = self.time_interval
        else:
            self.next_macro_update -= time_step

    def get_plot_labels(self):
        return {
            'space_mean_velocity': 'Space Mean Velocity (m/s)',
            'weight_load': 'Weight Load (kg)'
        }

    def write_results(self):
        # JSON output
        os.makedirs(self.path, exist_ok=True)
        _file = open('{}/{}.json'.format(self.path, self.get_name()), 'w')
        results = {
            'macro': self.macroscopic_data
        }
        _file.write(json.dumps(results))
        _file.close()

        # CSV output macroscopic
        _file = open('{}/{}_macro.csv'.format(self.path, self.get_name()), 'w')
        csvwriter = csv.writer(_file)
        count = 0
        for d in self.macroscopic_data:
            data = self.macroscopic_data[d]
            data['timestamp'] = d
            if count == 0:
                header = data.keys()
                csvwriter.writerow(header)
                count += 1
            csvwriter.writerow(data.values())
            del data['timestamp']
        _file.close()
