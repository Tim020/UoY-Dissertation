import math


import Consts


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
        acceleration = math.pow(
            (vehicle.velocity / vehicle.get_desired_velocity()), 4)
        deceleration = math.pow(IDM.calc_desired_gap(vehicle) / vehicle.gap, 2)
        return vehicle.max_acceleration * (1 - acceleration - deceleration)

    @staticmethod
    def calc_desired_gap(vehicle):
        pv = vehicle.velocity
        if vehicle.lead_vehicle:
            lpv = vehicle.lead_vehicle.velocity
        else:
            lpv = pv
        c = ((vehicle.get_safetime_headway() * pv) +
             ((pv * (pv - lpv)) / (2 * math.sqrt(
                 vehicle.max_acceleration * vehicle.max_deceleration))))
        return vehicle.minimum_distance + max(0, c)

    @staticmethod
    def calc_velocity(vehicle):
        new_velocity = IDM.calc_raw_velocity(vehicle)
        return max(0, new_velocity)

    @staticmethod
    def calc_raw_velocity(vehicle):
        return vehicle.velocity + (IDM.calc_acceleration(vehicle) *
                                   Consts.TIME_STEP)

    @staticmethod
    def calc_position(vehicle):
        if IDM.calc_raw_velocity(vehicle) < 0:
            new_position = (vehicle.position -
                            (0.5 * (math.pow(vehicle.velocity, 2) /
                                    IDM.calc_acceleration(vehicle))))
        else:
            new_position = (vehicle.position +
                            (vehicle.velocity * Consts.TIME_STEP) +
                            (0.5 * IDM.calc_acceleration(vehicle) *
                             math.pow(Consts.TIME_STEP, 2)))
        return new_position

    @staticmethod
    def calc_gap(vehicle):
        if vehicle.lead_vehicle:
            return (vehicle.lead_vehicle.position -
                    IDM.calc_position(vehicle) - vehicle.lead_vehicle.length)
        else:
            return Consts.BRIDGE_LENGTH + 100


class TruckPlatoon(DriverModel):
    @staticmethod
    def calc_acceleration(vehicle):
        if vehicle.is_leader:
            return IDM.calc_acceleration(vehicle)
        else:
            return TruckPlatoon.calc_acceleration(vehicle.lead_vehicle)

    @staticmethod
    def calc_velocity(vehicle):
        if vehicle.is_leader:
            return IDM.calc_velocity(vehicle)
        else:
            return TruckPlatoon.calc_velocity(vehicle.lead_vehicle)

    @staticmethod
    def calc_position(vehicle):
        if vehicle.is_leader:
            return IDM.calc_position(vehicle)
        else:
            return (TruckPlatoon.calc_position(vehicle.lead_vehicle) -
                    vehicle.lead_vehicle.length - vehicle.follow_distance)

    @staticmethod
    def calc_gap(vehicle):
        if vehicle.lead_vehicle:
            return (vehicle.lead_vehicle.position -
                    TruckPlatoon.calc_position(vehicle) -
                    vehicle.lead_vehicle.length)
        else:
            return Consts.BRIDGE_LENGTH + 100
