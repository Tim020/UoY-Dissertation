import os

import Consts


class Vehicle(object):
    def __init__(self, _id, desired_velocity, max_acceleration,
                 max_deceleration, minimum_distance, length, model, weight):
        # Paramaters from the driver model
        self.desired_velocity = desired_velocity
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.minimum_distance = minimum_distance
        self.length = length

        # Other parameters
        self._id = _id
        self._label = 'Base'
        self._bridge = None
        self.model = model
        self.weight = weight

        # Running values
        self.velocity = 0
        self.acceleration = 0
        self.position = 0
        self.gap = 0
        self.lead_vehicle = None
        self.lane = 0

        # Update values
        self._new_acceleration = None
        self._new_velocity = None
        self._new_position = None
        self._new_gap = None

        self._file = None

    def calc_new_params(self):
        self._new_acceleration = self.model.calc_acceleration(self)
        self._new_velocity = self.model.calc_velocity(self)
        self._new_position = self.model.calc_position(self)
        self._new_gap = self.model.calc_gap(self)

    def update_new_params(self, simulated_time):
        self.velocity = self._new_velocity
        self.acceleration = self._new_acceleration
        self.position = self._new_position
        self.gap = self._new_gap

        assert(self.velocity >= 0)
        assert(self.position >= 0)
        if self.lead_vehicle:
            assert(self.lead_vehicle.position - self.lead_vehicle.length >= self.position)

        if Consts.DEBUG_MODE:
            self._file.write('{},{},{},{}\n'.format(simulated_time,
                                                    self.velocity,
                                                    self.position, self.gap))

        # print('{}|{}: Lane: {}, '
        #       'Position: {}, Velocity: {}'.format(self._label, self._id,
        #                                           self.lane, self.position,
        #                                           self.velocity))

    def set_desired_speed(self, desired_velocity):
        self.desired_velocity = desired_velocity

    def set_lead_vehicle(self, vehicle):
        self.lead_vehicle = vehicle
        self.gap = self.model.calc_gap(self)

    def add_to_road(self, bridge, lead_vehicle):
        self._bridge = bridge
        self.lead_vehicle = lead_vehicle
        if lead_vehicle:
            self.gap = self.lead_vehicle.position - self.lead_vehicle.length
            self.velocity = lead_vehicle.velocity
        else:
            self.gap = Consts.BRIDGE_LENGTH + 100
            self.velocity = self.desired_velocity
        if Consts.DEBUG_MODE:
            os.makedirs('debug/lane_{}'.format(self.lane), exist_ok=True)
            self._file = open('debug/lane_{}/{}.txt'.format(self.lane,
                                                            self._id), 'w')

    def set_lane(self, lane):
        self.lane = lane

    def get_safetime_headway(self):
        return self._bridge.get_safetime_headway(self.lane, self.position)

    def get_desired_velocity(self):
        bridge_limit = self._bridge.get_speed_limit(self.lane, self.position)
        return bridge_limit if bridge_limit else self.desired_velocity

    def finalise(self):
        if Consts.DEBUG_MODE:
            self._file.close()

    def __str__(self):
        return '{}({}, {})'.format(self._label, self._id,
                                   self.desired_velocity)


class Car(Vehicle):
    def __init__(self, _id, desired_velocity, max_acceleration,
                 max_deceleration, minimum_distance, length, model, weight):
        super().__init__(_id, desired_velocity, max_acceleration,
                         max_deceleration, minimum_distance, length, model,
                         weight)
        self._label = 'Car'


class Truck(Vehicle):
    def __init__(self, _id, desired_velocity, max_acceleration,
                 max_deceleration, minimum_distance, length, model, weight):
        super().__init__(_id, desired_velocity, max_acceleration,
                         max_deceleration, minimum_distance, length, model,
                         weight)
        self._label = 'Truck'
