import random

# How often the simulation updates
SIMULATION_FREQUENCY = 0.01

# Length of simulation in seconds
SIMULATION_LENGTH = 120

# Simulation time step in seconds
TIME_STEP = 0.1

# Percentage distribution of cars and truck traffic
CAR_PCT = 80
TRUCK_PCT = 20

# Minimum distance to enforce between vehicles
MINUMUM_GAP = 2

# Length of the bridge for the simulation
BRIDGE_LENGTH = 200

# Seed used in this simulation - used to generate IDs of various things
SIMULATION_SEED = random.getrandbits(128)
# Need a 32 bit seed to use for the numpy random generators
SIMULATION_SHORT_SEED = SIMULATION_SEED >> (128 - 32)

# Number of vehicles per per hour injected into the system
INFLOW_RATE = 2000
