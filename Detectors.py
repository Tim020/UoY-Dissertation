from collections import defaultdict
import json
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

    def write_results(self):
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

                gaps = vehicle_data['space_headway']
                average_gap = sum(gaps) / len(gaps)

                self.microscopic_data[vehicle._id] = {
                    'average_velocity': average_velocity,
                    'average_space_headway': average_gap
                }

        if self.next_macro_update <= time_step:
            velocities = []
            weights = []
            for vehicle in vehicles:
                if vehicle._id in self.in_progress_vehicles:
                    velocities.append(vehicle.velocity)
                    weights.append(vehicle.weight)

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
