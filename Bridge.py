import random

import Vehicle


class Bridge(object):
    def __init__(self, seed, length, lanes):
        self.length = length
        self.lanes = lanes
        self.vehicles = [[] for _ in range(self.lanes * 2)]
        self._random = random.Random(seed)
        self._calls = 0
        self._cars = 0
        self._trucks = 0

    def add_vehicle(self, vehicle):
        self._calls += 1
        lane = self._random.randint(0, (self.lanes * 2) - 1)
        lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
        if lead_vehicle:
            if lead_vehicle.position - lead_vehicle.length >= vehicle.minimum_distance:
                self._add_vehicle(vehicle, lead_vehicle, lane)
                return True
            else:
                # Could not add to this lane, so go through all lanes and find
                # the first place we can add this new vehicle to
                for lane, _ in enumerate(self.vehicles):
                    lead_vehicle = self.vehicles[lane][-1] if self.vehicles[lane] else None
                    if lead_vehicle.position - lead_vehicle.length >= vehicle.minimum_distance:
                        self._add_vehicle(vehicle, lead_vehicle, lane)
                        return True
                return False
        else:
            self._add_vehicle(vehicle, lead_vehicle, lane)
            return True

    def _add_vehicle(self, vehicle, lead_vehicle, lane):
        vehicle.add_to_road(lead_vehicle)
        vehicle.set_lane(lane)
        self.vehicles[lane].append(vehicle)
        if type(vehicle) == Vehicle.Car:
            self._cars += 1
        else:
            self._trucks += 1

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
                self.vehicles[i].remove(vehicle)

        # Step 4: Update lead vehicles for all remaining vehicles
        for lane in self.vehicles:
            for i, vehicle in enumerate(lane):
                if i == 0:
                    vehicle.set_lead_vehicle(None)
                else:
                    vehicle.set_lead_vehicle(lane[i - 1])
