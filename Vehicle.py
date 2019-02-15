from faker import Faker

from Simulation import SIMULATION_SEED

uuid_generator = Faker()
uuid_generator.seed(SIMULATION_SEED)


class Vehicle(object):
    def __init__(self, desired_velocity, max_acceleration, max_deceleration, length, model):
        self._id = uuid_generator.uuid4()

        # Paramaters from the driver model
        self.desired_velocity = desired_velocity
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.length = length
        self.model = model

        # Running values
        self.velocity = 0
        self.prev_velocity = 0
        self.acceleration = 0
        self.prev_acceleration = 0
        self.position = 0
        self.prev_position = 0
        self.gap = 0
        self.prev_gap = 0
        self.lead_vehicle = None

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
        self.prev_velocity = self.velocity
        self.prev_acceleration = self.acceleration
        self.prev_position = self.position
        self.prev_gap = self.gap

        self.velocity = self._new_velocity
        self.acceleration = self._new_acceleration
        self.position = self._new_position
        self.gap = self._new_gap

        print('{}: Position: {}, Velocity: {} m/s'.format(self._id, self.position, self.velocity))

    def set_desired_speed(self, desired_velocity):
        self.desired_velocity = desired_velocity

    def set_lead_vehicle(self, vehicle):
        self.lead_vehicle = vehicle
        self.gap = self.model.calc_gap(self)
        self.prev_gap = self.gap

    def get_safetime_headway(self):
        return 1
