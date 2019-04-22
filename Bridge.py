import os
import random

import Consts
from Detectors import PointDetector, SpaceDetector, BridgeDetector
import Vehicle


def flatten(s):
    if s == []:
        return s
    if isinstance(s[0], list):
        return flatten(s[0]) + flatten(s[1:])
    return s[:1] + flatten(s[1:])


class SafetimeHeadwayZone(object):
    def __init__(self, start, end, time):
        self.start = start
        self.end = end
        self.time = time


class SpeedLimitedZone(object):
    def __init__(self, start, end, speed):
        self.start = start
        self.end = end
        self.speed = speed


class Bridge(object):
    def __init__(self, seed, length, lanes, safetime_headway):
        self.length = length
        self.lanes = lanes
        self.safetime_headway = safetime_headway
        self.vehicles = []
        self.headway_zones = []
        self.speed_restricted_zones = []
        self.point_detectors = []
        self.space_detectors = []
        self.lane_queues = []
        for i in range(self.lanes * 2):
            self.headway_zones.append([])
            self.vehicles.append([])
            self.speed_restricted_zones.append([])
            self.point_detectors.append([])
            self.space_detectors.append([])
            self.lane_queues.append([])
        self._random = random.Random(seed)
        self._calls = 0
        self._cars = 0
        self._trucks = 0
        if Consts.DEBUG_MODE:
            os.makedirs('debug/bridge', exist_ok=True)
            self._lane_files = [open('debug/bridge/lane_{}.txt'.format(lane),
                                     'w') for lane in range(self.lanes * 2)]
        os.makedirs('replays', exist_ok=True)
        self._replay_file = open('replays/replay-{}.sim'.format(seed), 'w')
        self.bridge_detector = BridgeDetector(60)

    # New vehicles #

    def add_vehicle(self, vehicle):
        self._calls += 1
        if type(vehicle) is list:
            if Consts.SINGLE_LANE:
                lane = 0
            else:
                lane = self._random.randint(0, (self.lanes * 2) - 1)
            if self.lane_queues[lane]:
                return False
            else:
                lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
                if (((lead_vehicle and lead_vehicle.position - lead_vehicle.length >= vehicle[0].minimum_distance) or (lead_vehicle is None)) and not self.lane_queues[lane]):
                    self._add_vehicle(vehicle.pop(0), lead_vehicle, lane)
                    self.lane_queues[lane] = vehicle
                    return True
                elif not Consts.SINGLE_LANE:
                    # Could not add to this lane, so go through all lanes and
                    # find the first place we can add this new vehicle to
                    for lane, _ in enumerate(self.vehicles):
                        lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
                        if (((lead_vehicle and lead_vehicle.position - lead_vehicle.length >= vehicle[0].minimum_distance) or (lead_vehicle is None)) and not self.lane_queues[lane]):
                            self._add_vehicle(vehicle.pop(0), lead_vehicle, lane)
                            self.lane_queues[lane] = vehicle
                            return True
                    return False
        else:
            if Consts.SINGLE_LANE:
                lane = 0
            else:
                lane = self._random.randint(0, (self.lanes * 2) - 1)
            lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
            if (((lead_vehicle and lead_vehicle.position - lead_vehicle.length
                  >= vehicle.minimum_distance) or (lead_vehicle is None))
                    and not self.lane_queues[lane]):
                self._add_vehicle(vehicle, lead_vehicle, lane)
                return True
            elif not Consts.SINGLE_LANE:
                # Could not add to this lane, so go through all lanes and find
                # the first place we can add this new vehicle to
                for lane, _ in enumerate(self.vehicles):
                    lead_vehicle = self.vehicles[lane][-1] if self.vehicles[
                        lane] else None
                    if (((lead_vehicle and lead_vehicle.position -
                         lead_vehicle.length >= vehicle.minimum_distance)
                            or (lead_vehicle is None))
                            and not self.lane_queues[lane]):
                        self._add_vehicle(vehicle, lead_vehicle, lane)
                        return True
                return False

    def _add_vehicle(self, vehicle, lead_vehicle, lane):
        vehicle.set_lane(lane)
        vehicle.add_to_road(self, lead_vehicle)
        self.vehicles[lane].append(vehicle)
        if type(vehicle) == Vehicle.Car:
            self._cars += 1
        else:
            self._trucks += 1
        if Consts.DEBUG_MODE:
            self._lane_files[lane].write('{}\n'.format(vehicle._id))

    def _add_platooned_truck(self, vehicle, lead_vehicle, lane):
        self._add_vehicle(vehicle, lead_vehicle, lane)
        vehicle.position = vehicle.lead_vehicle.position - vehicle.lead_vehicle.length - vehicle.follow_distance

    # Safetime Headway Zones #

    def add_safetime_headway_zone_all_lanes(self, start, end, time):
        for i in range(self.lanes * 2):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_safetime_headway_zone(self.length - end,
                                               self.length - start, time, lane)
            else:
                self.add_safetime_headway_zone(start, end, time, lane)

    def add_safetime_headway_zone(self, start, end, time, lane):
        if self.headway_zones[lane]:
            can_add_zone = True
            for zone in self.headway_zones[lane]:
                if zone.end > start > zone.start:
                    can_add_zone = False
                    break
            if can_add_zone:
                self.headway_zones[lane].append(SafetimeHeadwayZone(start, end,
                                                                    time))
        else:
            self.headway_zones[lane].append(SafetimeHeadwayZone(start, end,
                                                                time))

    def get_safetime_headway(self, lane, position):
        if self.headway_zones[lane]:
            for zone in self.headway_zones[lane]:
                if zone.end > position >= zone.start:
                    p = ((position - zone.start) / (zone.end - zone.start))
                    return zone.time * p
            return self.safetime_headway
        else:
            return self.safetime_headway

    # Speed Limited Zones #

    def add_speed_limited_zone_all_lanes(self, start, end, speed_limit):
        for i in range(self.lanes * 2):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_speed_limited_zone(self.length - end,
                                            self.length - start,
                                            speed_limit, lane)
            else:
                self.add_speed_limited_zone(start, end, speed_limit, lane)

    def add_speed_limited_zone(self, start, end, speed_limit, lane):
        if self.speed_restricted_zones[lane]:
            can_add_zone = True
            for zone in self.speed_restricted_zones[lane]:
                if zone.end > start > zone.start:
                    can_add_zone = False
                    break
            if can_add_zone:
                self.speed_restricted_zones[lane].append(
                    SpeedLimitedZone(start, end, speed_limit))
        else:
            self.speed_restricted_zones[lane].append(
                SpeedLimitedZone(start, end, speed_limit))

    def get_speed_limit(self, lane, position):
        if self.speed_restricted_zones[lane]:
            for zone in self.speed_restricted_zones[lane]:
                if zone.end > position >= zone.start:
                    return zone.speed
            return None
        else:
            return None

    # Point Detectors #

    def add_point_detector_all_lanes(self, position, time_interval):
        for i in range(self.lanes * 2):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_point_detector(lane, self.length - position,
                                        time_interval)
            else:
                self.add_point_detector(lane, position, time_interval)

    def add_point_detector(self, lane, position, time_interval):
        if self.point_detectors[lane]:
            can_add_detector = True
            for detector in self.point_detectors[lane]:
                if detector.position == position:
                    can_add_detector = False
                    break
            if can_add_detector:
                self.point_detectors[lane].append(PointDetector(lane, position,
                                                                time_interval))
        else:
            self.point_detectors[lane].append(PointDetector(lane, position,
                                                            time_interval))

    # Space Detectors #

    def add_space_detector_all_lanes(self, start, end, time_interval):
        for i in range(self.lanes * 2):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_space_detector(lane, self.length - end,
                                        self.length - start, time_interval)
            else:
                self.add_space_detector(lane, start, end, time_interval)

    def add_space_detector(self, lane, start, end, time_interval):
        if self.space_detectors[lane]:
            can_add_detector = True
            for detector in self.space_detectors[lane]:
                if detector.end > start > detector.start:
                    can_add_detector = False
                    break
            if can_add_detector:
                self.space_detectors[lane].append(
                    SpaceDetector(lane, start, end, time_interval))
        else:
            self.space_detectors[lane].append(
                SpaceDetector(lane, start, end, time_interval))

    # Simulation update #

    def update(self, time_step, simulated_time, queue):
        vehicle_data = [[] for _ in range(self.lanes * 2)]
        # Step 1: Parallel calculate new parameters for all vehicles
        for lane in self.vehicles:
            for vehicle in lane:
                vehicle.calc_new_params()

        # Step 2: Parallel update new parameters for all vehicles
        for lane in self.vehicles:
            for vehicle in lane:
                vehicle.update_new_params(simulated_time)

        # Step 3: Add next platoon truck for each platoon if possible:
        for i, _ in enumerate(self.lane_queues):
            if self.lane_queues[i]:
                lead = self.vehicles[i][-1]
                assert(lead is not None and type(lead) is Vehicle.PlatoonedTruck)
                if lead.position - lead.length >= self.lane_queues[i][0].follow_distance:
                    self._add_platooned_truck(self.lane_queues[i].pop(0), lead,
                                              i)

        # Step 4: Remove any vehicle at the end of the bridge
        vehicles_to_remove = [[] for _ in range(self.lanes * 2)]
        for i, lane in enumerate(self.vehicles):
            for vehicle in lane:
                if vehicle.position > self.length:
                    vehicles_to_remove[i].append(vehicle)
                else:
                    vehicle_data[i].append((vehicle._label, vehicle.position,
                                            vehicle._id))
        for i, lane in enumerate(vehicles_to_remove):
            for vehicle in lane:
                vehicle.finalise()
                self.vehicles[i].remove(vehicle)

        # Step 5: Update lead vehicles for all remaining vehicles
        for lane in self.vehicles:
            for i, vehicle in enumerate(lane):
                if i == 0:
                    vehicle.set_lead_vehicle(None)
                else:
                    vehicle.set_lead_vehicle(lane[i - 1])

        # Step 6: Update point detectors
        for i, lane in enumerate(self.point_detectors):
            for detector in lane:
                detector.tick(time_step, simulated_time, self.vehicles[i])

        # Step 7: Update space detectors
        for i, lane in enumerate(self.space_detectors):
            for detector in lane:
                detector.tick(time_step, simulated_time, self.vehicles[i])

        # Step 8: Update bridge detector
        self.bridge_detector.tick(time_step, simulated_time,
                                  flatten(self.vehicles))

        if queue:
            queue.put(vehicle_data)

        self._replay_file.write('Simulation Step: {}\n'.format(simulated_time))
        self._replay_file.write('{}\n'.format(vehicle_data))

    def write_detector_output(self):
        for lane in self.point_detectors:
            for detector in lane:
                detector.write_results()
        for lane in self.space_detectors:
            for detector in lane:
                detector.write_results()
        self.bridge_detector.write_results()

    def plot_detector_output(self):
        for lane in self.point_detectors:
            for detector in lane:
                detector.plot()
        for lane in self.space_detectors:
            for detector in lane:
                detector.plot()
        self.bridge_detector.plot()
