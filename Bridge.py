import os
import random

import Vehicle


class SafetimeHeadwayZone(object):
    def __init__(self, start, end, time):
        self.start = start
        self.end = end
        self.time = time


class Bridge(object):
    def __init__(self, seed, length, lanes, safetime_headway):
        self.length = length
        self.lanes = lanes
        self.safetime_headway = safetime_headway
        self.headway_zones = [[] for _ in range(self.lanes * 2)]
        self.vehicles = [[] for _ in range(self.lanes * 2)]
        self._random = random.Random(seed)
        self._calls = 0
        self._cars = 0
        self._trucks = 0
        os.makedirs('debug/bridge', exist_ok=True)
        self._lane_files = [open('debug/bridge/lane_{}.txt'.format(lane), 'w')
                            for lane in range(self.lanes * 2)]

    def add_vehicle(self, vehicle):
        self._calls += 1
        lane = self._random.randint(0, (self.lanes * 2) - 1)
        lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
        if lead_vehicle:
            if (lead_vehicle.position - lead_vehicle.length >=
                    vehicle.minimum_distance):
                self._add_vehicle(vehicle, lead_vehicle, lane)
                return True
            else:
                # Could not add to this lane, so go through all lanes and find
                # the first place we can add this new vehicle to
                for lane, _ in enumerate(self.vehicles):
                    lead_vehicle = self.vehicles[lane][-1] if self.vehicles[
                        lane] else None
                    if (lead_vehicle.position - lead_vehicle.length >=
                            vehicle.minimum_distance):
                        self._add_vehicle(vehicle, lead_vehicle, lane)
                        return True
                return False
        else:
            self._add_vehicle(vehicle, lead_vehicle, lane)
            return True

    def add_safetime_headway_zone_all_lanes(self, start, end, time):
        for i in range(self.lanes * 2):
            lane = i if i < self.lanes else (i * -1) + (self.lanes - 1)
            if lane < 0:
                start = self.length - end
                end = self.length - start
            self.add_safetime_headway_zone(start, end, time, lane)

    def add_safetime_headway_zone(self, start, end, time, lane):
        if self.headway_zones[lane]:
            can_add_zone = True
            for zone in self.headway_zones[lane]:
                if start < zone.end and start > zone.start:
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

    def _add_vehicle(self, vehicle, lead_vehicle, lane):
        vehicle.set_lane(lane)
        vehicle.add_to_road(self, lead_vehicle)
        self.vehicles[lane].append(vehicle)
        if type(vehicle) == Vehicle.Car:
            self._cars += 1
        else:
            self._trucks += 1
        self._lane_files[lane].write('{}\n'.format(vehicle._id))

    def update(self):
        # Step 1: Parallel calculate new parameters for all vehicles
        for lane in self.vehicles:
            for vehicle in lane:
                vehicle.calc_new_params()

        # Step 2: Parallel update new parameters for all vehicles
        for lane in self.vehicles:
            for vehicle in lane:
                vehicle.update_new_params()

        # Step 3: Remove any vehicle at the end of the bridge
        vehicles_to_remove = [[] for _ in range(self.lanes * 2)]
        for i, lane in enumerate(self.vehicles):
            for vehicle in lane:
                if vehicle.position > self.length:
                    vehicles_to_remove[i].append(vehicle)
        for i, lane in enumerate(vehicles_to_remove):
            for vehicle in lane:
                vehicle.finalise()
                self.vehicles[i].remove(vehicle)

        # Step 4: Update lead vehicles for all remaining vehicles
        for lane in self.vehicles:
            for i, vehicle in enumerate(lane):
                if i == 0:
                    vehicle.set_lead_vehicle(None)
                else:
                    vehicle.set_lead_vehicle(lane[i - 1])
