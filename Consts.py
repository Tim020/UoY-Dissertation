import random

_random = None

# The number of simulation runs to do
NUM_RUNS = 1

DEBUG_MODE = False

# Seed used in this simulation - used to generate IDs of various things
SIMULATION_SEED = random.getrandbits(128)
# Need a 32 bit seed to use for the numpy random generators
SIMULATION_SHORT_SEED = SIMULATION_SEED >> (128 - 32)

# Whether force the simulation to update at the same frequency as the display
FORCE_DISPLAY_FREQ = True

# How often the simulation updates
SIMULATION_FREQUENCY = 0.001

# Length of simulation in seconds
SIMULATION_LENGTH = 3600

# Simulation time step in seconds
TIME_STEP = 0.1

# Percentage distribution of cars and truck traffic
CAR_PCT = 80
TRUCK_PCT = 20
# Chance that when a truck is added to the road, it will be a platoon
PLATOON_CHANCE = 0

# Minimum distance to enforce between vehicles
MINUMUM_GAP = 2

# Length of the bridge for the simulation
BRIDGE_LENGTH = 1000
# Whether to simulate only a single lane of traffic (False), or bi-directional traffic (True)
MULTI_LANE = True
# Number of lanes of traffic per direction in bi-directional simulation
BRIDGE_LANES = 1
# Default safetime headway for the bridge
SAFETIME_HEADWAY = 1

# Number of vehicles per per hour injected into the system (per lane)
INFLOW_RATE = 2000

# Average speed for trucks and cars (m/s)
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


def configure_random():
    global _random
    _random = random.Random(SIMULATION_SEED)


def generate_seed():
    global SIMULATION_SEED, SIMULATION_SHORT_SEED, _random

    if not _random:
        print('_random has not been configured. Calling configure_random before generating a new seed')
        configure_random()

    # Seed used in this simulation - used to generate IDs of various things
    SIMULATION_SEED = _random.getrandbits(128)
    # Need a 32 bit seed to use for the numpy random generators
    SIMULATION_SHORT_SEED = SIMULATION_SEED >> (128 - 32)


def load_from_json(conf):
    global DEBUG_MODE
    params = {
        'Seed': 'SIMULATION_SEED',
        'Short Seed': 'SIMULATION_SHORT_SEED',
        'Simulation Update Frequency': 'SIMULATION_FREQUENCY',
        'Simulation Length': 'SIMULATION_LENGTH',
        'Simulation Time Step': 'TIME_STEP',
        'Minimum Gap': 'MINUMUM_GAP',
        'Bridge Length': 'BRIDGE_LENGTH',
        'Safetime Headway': 'SAFETIME_HEADWAY',
        'Multi Lane Traffic': 'MULTI_LANE',
        'Number of Lanes': 'BRIDGE_LANES',
        'Inflow Rate': 'INFLOW_RATE',
        'Truck Percentage': 'TRUCK_PCT',
        'Car Percentage': 'CAR_PCT',
        'Car v0': 'CAR_SPEED',
        'Truck v0': 'TRUCK_SPEED',
        'Car Speed Variance': 'CAR_SPEED_VARIANCE',
        'Truck Speed Variance': 'TRUCK_SPEED_VARIANCE',
        'Platoon Percentage': 'PLATOON_CHANCE',
        'Minimum Platoon Length': 'MIN_PLATOON_LENGTH',
        'Maximum Platoon Length': 'MAX_PLATOON_LENGTH',
        'Minimum Platoon Gap': 'MIN_PLATOON_GAP',
        'Maximum Platoon Gap': 'MAX_PLATOON_GAP',
        'Number of Runs': 'NUM_RUNS'
    }
    print('Loading configuration from file')
    for param in conf:
        if param in params:
            if DEBUG_MODE:
                print('Setting {} to {}'.format(params[param], conf[param]))
            exec('{} = {}'.format(params[param], conf[param]), globals())
    print('Loaded configuration from file')
