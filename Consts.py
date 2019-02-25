import random

DEBUG_MODE = True

FORCE_DISPLAY_FREQ = True

# How often the simulation updates
SIMULATION_FREQUENCY = 0.01

# Length of simulation in seconds
SIMULATION_LENGTH = 36000

# Simulation time step in seconds
TIME_STEP = 0.1

# Percentage distribution of cars and truck traffic
CAR_PCT = 80
TRUCK_PCT = 20
# Chance that when a truck is added to the road, it will be a platoon
PLATOON_CHANCE = 2

# Minimum distance to enforce between vehicles
MINUMUM_GAP = 2

# Length of the bridge for the simulation
BRIDGE_LENGTH = 500
BRIDGE_LANES = 4

# Seed used in this simulation - used to generate IDs of various things
SIMULATION_SEED = random.getrandbits(128)
# Need a 32 bit seed to use for the numpy random generators
SIMULATION_SHORT_SEED = SIMULATION_SEED >> (128 - 32)

# Number of vehicles per per hour injected into the system
INFLOW_RATE = 10000

# Average speed for trucks and cars
CAR_SPEED = 33
TRUCK_SPEED = 22

# Percentage of mean speed the distribution should go between ± for vehicles
CAR_SPEED_VARIANCE = 20
TRUCK_SPEED_VARIANCE = 10

# Minimum and maximum number of trucks allowed in a platoon
MIN_PLATOON_LENGTH = 2
MAX_PLATOON_LENGTH = 10

# Minumum and maximum gap between trucks in a platoon
MIN_PLATOON_GAP = 2
MAX_PLATOON_GAP = 5
