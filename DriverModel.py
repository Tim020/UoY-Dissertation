import math


from Simulation import TIME_STEP, MINUMUM_GAP, BRIDGE_LENGTH


class DriverModel(object):

    @staticmethod
    def calc_acceleration(vehicle):
        raise NotImplementedError()

    @staticmethod
    def calc_velocity(vehicle):
        raise NotImplementedError()

    @staticmethod
    def calc_position(vehicle):
        raise NotImplementedError()

    @staticmethod
    def calc_gap(vehicle):
        raise NotImplementedError()


class IDM(DriverModel):

    @staticmethod
    def calc_acceleration(vehicle):
        """
        dv(t)/dt = [1 - (v(t)/v0)^4  - (s*(t)/s(t))^2]
        """
        acceleration = math.pow((vehicle.prev_velocity / vehicle.desired_velocity), 4)
        deceleration = math.pow(IDM.calc_desired_gap(vehicle) / vehicle.prev_gap, 2)
        return vehicle.max_acceleration * (1 - acceleration - deceleration)

    @staticmethod
    def calc_desired_gap(vehicle):
        pv = vehicle.prev_velocity
        if vehicle.lead_vehicle:
            lpv = vehicle.lead_vehicle.prev_velocity
        else:
            lpv = pv
        c = ((vehicle.get_safetime_headway() * pv) + ((pv * (pv - lpv)) / (2 * math.sqrt(vehicle.max_acceleration * vehicle.max_deceleration))))
        return MINUMUM_GAP + max(0, c)

    @staticmethod
    def calc_velocity(vehicle):
        new_velocity = vehicle.prev_velocity + (IDM.calc_acceleration(vehicle) * TIME_STEP)
        if new_velocity < 0:
            new_velocity = 0
        return new_velocity

    @staticmethod
    def calc_position(vehicle):
        if IDM.calc_velocity(vehicle) < 0:
            new_position = vehicle.prev_position - 0.5 * (math.pow(vehicle.prev_velocity, 2) / IDM.calc_acceleration(vehicle))
        else:
            new_position = vehicle.prev_position + vehicle.prev_velocity * TIME_STEP + (0.5 * IDM.calc_acceleration(vehicle) * math.pow(TIME_STEP, 2))
        return new_position

    @staticmethod
    def calc_gap(vehicle):
        if vehicle.lead_vehicle:
            return vehicle.lead_vehicle.position - IDM.calc_position(vehicle) - vehicle.lead_vehicle.length
        else:
            return BRIDGE_LENGTH + 100
