from collections import defaultdict
import csv
import json
import math
import matplotlib
import os


class Detector(object):
    def __init__(self, lane, time_interval):
        self.lane = lane
        self.time_interval = time_interval
        self.next_macro_update = self.time_interval
        self.microscopic_data = defaultdict(dict)
        self.macroscopic_data = defaultdict(dict)

    def get_name(self):
        raise NotImplementedError

    def tick(self, time_step, simulated_time, vehicles):
        raise NotImplementedError

    def get_plot_labels(self):
        raise NotImplementedError

    def write_results(self):
        # JSON output
        os.makedirs('debug/bridge/detectors/{}'.
                    format(self.lane), exist_ok=True)
        _file = open('debug/bridge/detectors/{}/{}.txt'.
                     format(self.lane, self.get_name()), 'w')
        results = {
            'micro': self.microscopic_data,
            'macro': self.macroscopic_data
        }
        _file.write(json.dumps(results))
        _file.close()

        # CSV output macroscopic
        _file = open('debug/bridge/detectors/{}/{}_macro.csv'.
                     format(self.lane, self.get_name()), 'w')
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
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        rcParams['axes.titlepad'] = 40

        k = list(self.macroscopic_data.keys())[0]
        data_keys = list(self.macroscopic_data[k].keys())
        f, axarr = plt.subplots(math.ceil(len(data_keys) / 2),
                                math.ceil(len(data_keys) / 2), squeeze=False)

        timestamps = []
        data_points = defaultdict(list)

        for d in self.macroscopic_data:
            timestamps.append(d)
            for key in self.macroscopic_data[d]:
                data_points[key].append(self.macroscopic_data[d][key])

        count = 0
        for plot in sorted(data_points):
            axarr[count % 2, count // 2].plot(timestamps, data_points[plot])
            axarr[count % 2, count // 2].set_xlabel('Time (s)')
            axarr[count % 2, count // 2].set_ylabel(self.get_plot_labels()[plot])
            axarr[count % 2, count // 2].grid(True)
            count += 1

        if count != math.pow(math.ceil(len(data_keys) / 2), 2):
            for x in range(math.ceil(len(data_keys) / 2)):
                for y in range(math.ceil(len(data_keys) / 2)):
                    if (x + (y * math.ceil(len(data_keys) / 2))) >= count:
                        axarr[y, x].axis('off')

        f.suptitle('Data from {}'.format(self.get_name()), fontsize=12, y=0.99)
        plt.subplots_adjust(top=0.85)
        plt.tight_layout()
        f.set_size_inches(16, 9)
        plt.savefig('debug/bridge/detectors/{}/{}.png'.format(self.lane, self.get_name()), dpi=300)


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
                'space_mean_velocity': ((len(self.speeds) / sum((1/x) for x in self.speeds))
                                        if self.speeds else 0),
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
                average_velocity = sum(velocities) / len(velocities)
                space_velocity = len(velocities) / sum((1/x) for x in velocities)

                gaps = vehicle_data['space_headway']
                average_gap = sum(gaps) / len(gaps)

                self.microscopic_data[vehicle._id] = {
                    'average_time_mean_velocity': average_velocity,
                    'average_space_mean_velocity': space_velocity,
                    'average_space_headway': average_gap
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
                'time_mean_velocity': ((sum(velocities) / len(velocities))
                                       if velocities else 0),
                'space_mean_velocity': ((len(velocities) / sum((1/x) for x in velocities))
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
            'time_mean_velocity': 'Time Mean Velocity (m/s)',
            'space_mean_velocity': 'Space Mean Velocity (m/s)',
            'density': 'Flow (veh/km)',
            'weight_load': 'Weight Load (kg)'
        }


class BridgeDetector(Detector):
    def __init__(self, time_interval):
        super().__init__('Bridge', time_interval)

    def get_name(self):
        return 'Bridge Detector'

    def tick(self, time_step, simulated_time, vehicles):
        if self.next_macro_update <= time_step:
            weight_load = []
            velocities = []
            for vehicle in vehicles:
                weight_load.append(vehicle.weight)
                velocities.append(vehicle.velocity)

            self.macroscopic_data[simulated_time] = {
                'time_mean_velocity': ((sum(velocities) / len(velocities))
                                       if velocities else 0),
                'space_mean_velocity': ((len(velocities) / sum((1 / x) for x in velocities))
                                        if velocities else 0),
                'weight_load': sum(weight_load)
            }

            self.next_macro_update = self.time_interval
        else:
            self.next_macro_update -= time_step

    def get_plot_labels(self):
        return {
            'time_mean_velocity': 'Time Mean Velocity (m/s)',
            'space_mean_velocity': 'Space Mean Velocity (m/s)',
            'weight_load': 'Weight Load (kg)'
        }
