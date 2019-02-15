from faker import Faker

import Consts

uuid_generator = Faker()
uuid_generator.seed(Consts.SIMULATION_SEED)


class Vehicle(object):
    def __init__(self, desired_velocity, max_acceleration, max_deceleration,
                 minimum_distance, length, model):
        self._id = uuid_generator.uuid4()
        self._label = 'Base'
        self._bridge = None

        # Paramaters from the driver model
        self.desired_velocity = desired_velocity
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.minimum_distance = minimum_distance
        self.length = length
        self.model = model

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

    def calc_new_params(self):
        self._new_acceleration = self.model.calc_acceleration(self)
        self._new_velocity = self.model.calc_velocity(self)
        self._new_position = self.model.calc_position(self)
        self._new_gap = self.model.calc_gap(self)

    def update_new_params(self):
        self.velocity = self._new_velocity
        self.acceleration = self._new_acceleration
        self.position = self._new_position
        self.gap = self._new_gap

        assert(self.velocity >= 0)
        if self.lead_vehicle:
            assert(self.lead_vehicle.position > self.position)

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

    def set_lane(self, lane):
        self.lane = lane

    def get_safetime_headway(self):
        return self._bridge.get_safetime_headway(self.lane, self.position)


class Car(Vehicle):
    def __init__(self, desired_velocity, max_acceleration, max_deceleration,
                 minimum_distance, length, model):
        super().__init__(desired_velocity, max_acceleration, max_deceleration,
                         minimum_distance, length, model)
        self._label = 'Car'


class Truck(Vehicle):
    def __init__(self, desired_velocity, max_acceleration, max_deceleration,
                 minimum_distance, length, model):
        super().__init__(desired_velocity, max_acceleration, max_deceleration,
                         minimum_distance, length, model)
        self._label = 'Truck'
