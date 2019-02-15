from Simulation import SIMULATION_FREQUENCY, TIME_STEP
from Vehicle import Vehicle
from DriverModel import IDM


class Bridge(object):
    def __init__(self, env, length, lanes):
        self.env = env
        self.length = length
        self.lanes = lanes
        self.vehicles = [[] for _ in range(self.lanes * 2)]
        self.action = env.process(self.update(SIMULATION_FREQUENCY, TIME_STEP))
        self.simulated_time = 0

        self.add_vehicle(Vehicle(22, 2, 3, 2, IDM), 0)

    def add_vehicle(self, vehicle, lane):
        lead_vehicle = self.vehicles[lane][0] if self.vehicles[lane] else None
        vehicle.set_lead_vehicle(lead_vehicle)
        self.vehicles[lane].append(vehicle)

    def update(self, frequency, time_step):
        while True:
            print('Update at {}, simulated time: {}s'.format(self.env.now, self.simulated_time))

            for lane in self.vehicles:
                for vehicle in lane:
                    vehicle.calc_new_params()
            for lane in self.vehicles:
                for vehicle in lane:
                    vehicle.update_new_params()

            self.simulated_time += time_step
            yield self.env.timeout(frequency)
