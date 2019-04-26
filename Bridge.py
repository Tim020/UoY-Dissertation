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

    def add_vehicle(self, vehicle, force_lane=None):
        self._calls += 1
        if type(vehicle) is list:
            if not Consts.MULTI_LANE:
                lane = 0
            else:
                if force_lane:
                    lane = force_lane
                else:
                    lane = self._random.randint(0, (self.lanes * 2) - 1)
            if self.lane_queues[lane]:
                return False, lane, len(vehicle)
            else:
                lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
                if self._can_add_to_lane(lane, lead_vehicle, vehicle[0]):
                    self._add_vehicle(vehicle.pop(0), lead_vehicle, lane)
                    self.lane_queues[lane] = vehicle
                    return True, lane, len(vehicle)
                elif Consts.MULTI_LANE and not force_lane:
                    # Could not add to this lane, so go through all lanes and
                    # find the first place we can add this new vehicle to
                    for lane, _ in enumerate(self.vehicles):
                        lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
                        if self._can_add_to_lane(lane, lead_vehicle, vehicle[0]):
                            self._add_vehicle(vehicle.pop(0), lead_vehicle, lane)
                            self.lane_queues[lane] = vehicle
                            return True, lane, len(vehicle)
                    return False, lane, len(vehicle)
                else:
                    return False, lane, len(vehicle)
        else:
            if not Consts.MULTI_LANE:
                lane = 0
            else:
                if force_lane:
                    lane = force_lane
                else:
                    lane = self._random.randint(0, (self.lanes * 2) - 1)
            lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
            if self._can_add_to_lane(lane, lead_vehicle, vehicle):
                self._add_vehicle(vehicle, lead_vehicle, lane)
                return True, lane, 1
            elif Consts.MULTI_LANE and not force_lane:
                # Could not add to this lane, so go through all lanes and find
                # the first place we can add this new vehicle to
                for lane, _ in enumerate(self.vehicles):
                    lead_vehicle = self.vehicles[lane][-1] if self.vehicles[
                        lane] else None
                    if self._can_add_to_lane(lane, lead_vehicle, vehicle):
                        self._add_vehicle(vehicle, lead_vehicle, lane)
                        return True, lane, 1
                return False, lane, 1
            else:
                return False, lane, 1

    def _can_add_to_lane(self, lane, lead_vehicle, vehicle):
        if self.lane_queues[lane]:
            return False
        if lead_vehicle:
            current_gap = lead_vehicle.position - lead_vehicle.length
            if current_gap >= Consts.MINIMUM_INJECTION_GAP:
                return True
            else:
                return False
        else:
            return True

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
        r = self.lanes * 2 if Consts.MULTI_LANE else 1
        for i in range(r):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_safetime_headway_zone(self.length - end,
                                               self.length - start, time, lane)
            else:
                self.add_safetime_headway_zone(start, end, time, lane)

    def add_safetime_headway_zone(self, start, end, time, lane):
        if not Consts.MULTI_LANE and lane > 0:
            print('Single lane traffic only, ignoring safetime headway for '
                  'lane {}'.format(lane))
            return
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
        r = self.lanes * 2 if Consts.MULTI_LANE else 1
        for i in range(r):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_speed_limited_zone(self.length - end,
                                            self.length - start,
                                            speed_limit, lane)
            else:
                self.add_speed_limited_zone(start, end, speed_limit, lane)

    def add_speed_limited_zone(self, start, end, speed_limit, lane):
        if not Consts.MULTI_LANE and lane > 0:
            print('Single lane traffic only, ignoring speed limit for '
                  'lane {}'.format(lane))
            return
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
        r = self.lanes * 2 if Consts.MULTI_LANE else 1
        for i in range(r):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_point_detector(lane, self.length - position,
                                        time_interval)
            else:
                self.add_point_detector(lane, position, time_interval)

    def add_point_detector(self, lane, position, time_interval):
        if not Consts.MULTI_LANE and lane > 0:
            print('Single lane traffic only, ignoring point detector for '
                  'lane {}'.format(lane))
            return
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
        r = self.lanes * 2 if Consts.MULTI_LANE else 1
        for i in range(r):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                self.add_space_detector(lane, self.length - end,
                                        self.length - start, time_interval)
            else:
                self.add_space_detector(lane, start, end, time_interval)

    def add_space_detector(self, lane, start, end, time_interval):
        if not Consts.MULTI_LANE and lane > 0:
            print('Single lane traffic only, ignoring space detector for '
                  'lane {}'.format(lane))
            return
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

    # Configuration Settings

    def configure(self, conf):
        detectors = conf.get('detectors')
        self._configure_detectors(detectors)

        headways = conf.get('headways')
        self._configure_headways(headways)

        speedlimits = conf.get('speedlimits')
        self._configure_speedlimits(speedlimits)

    def _configure_detectors(self, detectors):
        for detector in detectors:
            if detector['type'] == 'point':
                position = detector['position']
                interval = detector['interval']
                if detector['lane'] == 'all':
                    self.add_point_detector_all_lanes(position, interval)
                else:
                    self.add_point_detector(detector['lane'], position,
                                            interval)
            elif detector['type'] == 'space':
                start = detector['position_start']
                end = detector['position_end']
                interval = detector['interval']
                if detector['lane'] == 'all':
                    self.add_space_detector_all_lanes(start, end, interval)
                else:
                    self.add_space_detector(detector['lane'], start, end, interval)
            else:
                raise ValueError('Unknown type: {}'.format(detector['type']))

    def _configure_headways(self, headways):
        for zone in headways:
            start = zone['position_start']
            end = zone['position_end']
            headway = zone['headway']
            if zone['lane'] == 'all':
                self.add_safetime_headway_zone_all_lanes(start, end, headway)
            else:
                self.add_safetime_headway_zone(start, end, headway, zone['lane'])

    def _configure_speedlimits(self, speedlimits):
        for zone in speedlimits:
            start = zone['position_start']
            end = zone['position_end']
            headway = zone['speedlimit']
            if zone['lane'] == 'all':
                self.add_speed_limited_zone_all_lanes(start, end, headway)
            else:
                self.add_speed_limited_zone(start, end, headway, zone['lane'])

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
