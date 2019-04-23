#!/usr/bin/env python3

import json
import os
import random
import string


def str2bool(v):
  if v.lower() in ("yes", "true", "t", "1", "y"):
      return True
  elif v.lower() in ("no", "false", "f", "0", "n"):
      return False
  else:
      raise ValueError('Not a recognised boolean value')


if __name__ == '__main__':
    params = {
        'Simulation Update Frequency': {
            'itemtype': float,
            'help': 'How often the simulator updates in real time'
        },
        'Simulation Length': {
            'itemtype': int,
            'help': 'How much time to simulate'
        },
        'Simulation Time Step': {
            'itemtype': float,
            'help': 'How much time passes in each simulation update'
        },
        'Minimum Gap': {
            'itemtype': int,
            'help': 'Minimum distance to enforce between vehicles (m)'
        },
        'Bridge Length': {
            'itemtype': int,
            'help': 'Length of the bridge to simulate (m)'
        },
        'Safetime Headway': {
            'itemtype': float,
            'help': 'Default safetime headway for the bridge'
        },
        'Multi Lane Traffic': {
            'itemtype': bool,
            'help': 'Whether to simulate only a single lane of traffic (False), '
                    'or bi-directional traffic (True)'
        },
        'Number of Lanes': {
            'itemtype': int,
            'help': 'Number of lanes of traffic per direction in bi-directional '
                    'simulation',
            'requires': 'Multi Lane Traffic'
        },
        'Inflow Rate': {
            'itemtype': int,
            'help': 'Number of vehicles per hour injected into the system '
                    '(per lane)'
        },
        'Truck Percentage': {
            'itemtype': int,
            'help': 'The percentage distribution of trucks in the overall traffic',
            'post_expression': 'simulation_params["Car Percentage"] = 100 - '
                               'simulation_params["Truck Percentage"]'
        },
        'Car v0': {
            'itemtype': int,
            'help': 'Desired speed for cars (m/s)',
            'requires': 'Car Percentage'
        },
        'Truck v0': {
            'itemtype': int,
            'help': 'Desired speed for trucks (m/s)',
            'requires': 'Truck Percentage'
        },
        'Car Speed Variance': {
            'itemtype': int,
            'help': 'Percentage of mean speed the distribution should vary between'
                    ' for cars',
            'requires': 'Car v0'
        },
        'Truck Speed Variance': {
            'itemtype': int,
            'help': 'Percentage of mean speed the distribution should vary between'
                    ' for trucks',

            'requires': 'Truck v0'
        },
        'Platoon Percentage': {
            'itemtype': int,
            'help': 'The percentage of Automated Truck Platoons in the overall '
                    'truck traffic',
            'requires': 'Truck Percentage'
        },
        'Minimum Platoon Length': {
            'itemtype': int,
            'help': 'Minimum number of vehicles in an Automated Truck Platoon',
            'requires': 'Platoon Percentage'
        },
        'Maximum Platoon Length': {
            'itemtype': int,
            'help': 'Maximum number of vehicles in an Automated Truck Platoon',
            'requires': 'Platoon Percentage',
            'post_expression': 'assert(simulation_params["Maximum Platoon Length"]>= simulation_params["Minimum Platoon Length"])'
        },
        'Minimum Platoon Gap': {
            'itemtype': int,
            'help': 'Minimum gap between vehicles in an Automated Truck Platoon '
                    '(m)',
            'requires': 'Platoon Percentage'
        },
        'Maximum Platoon Gap': {
            'itemtype': int,
            'help': 'Maximum gap between vehicles in an Automated Truck Platoon '
                    '(m)',
            'requires': 'Platoon Percentage',
            'post_expression': 'assert(simulation_params["Maximum Platoon Gap"]>= simulation_params["Minimum Platoon Gap"])'
        },
        'Number of Runs': {
            'itemtype': int,
            'help': 'The number of runs to perform with this configuration'
        }
    }
    print('Welcome to the Configuration Generator for Traffic Simulator')

    simulation_params = dict()
    seed = random.getrandbits(128)
    short_seed = seed >> (128 - 32)
    simulation_params['Seed'] = seed
    simulation_params['Short Seed'] = short_seed
    simulation_params['detectors'] = []

    for param in params:
        if 'requires' in params[param]:
            if params[param]['requires'] not in simulation_params or not simulation_params[params[param]['requires']]:
                continue

        prompt_string = ('Enter the value for {}.\n'
                         '\tHelp: {}\n'
                         '\tValue: '.format(param.lower(),
                                            params[param]['help']))
        answer = input(prompt_string)
        t = params[param]['itemtype']
        while True:
            try:
                if t is bool:
                    answer = str2bool(answer)
                else:
                    answer = t(answer)
            except ValueError:
                print('Type was not correct for {}, should be {}'.format(param, t))
                answer = input('Please enter the value again: ')
            else:
                simulation_params[param] = answer
                if 'post_expression' in params[param]:
                    exec(params[param]['post_expression'])
                break

    answer = input('Would you like to configure point or space detectors? '
                   '(Y/N): ')
    while True:
        try:
            answer = str2bool(answer)
            break
        except ValueError:
            print('Could not understand input, please enter Y or N.')

    if answer:
        num_lanes = simulation_params.get('Number of lanes', 1)
        if simulation_params['Multi Lane Traffic']:
            possible_lanes = [str(x) for x in range(num_lanes * 2)]
            possible_lanes_int = [int(x) for x in range(num_lanes * 2)]
        else:
            possible_lanes = [str(x) for x in range(num_lanes)]
            possible_lanes_int = [int(x) for x in range(num_lanes)]
        possible_lanes.append('all')

        prompt_string = ('Options:\n\t'
                         '1 - New point detector\n\t'
                         '2 - New space detector\n\t'
                         'Q - Finished\n'
                         'Enter Option: ')
        answer = input(prompt_string)
        while True:
            while answer.lower() not in ('1', '2', 'q'):
                print('Invalid option {}'.format(answer))
                answer = input(prompt_string)

            if answer == '1':
                lane = input('Enter lane for new point detector. Options are: [{}, {}] or All: '.format(min(possible_lanes_int), max(possible_lanes_int)))
                while lane.lower() not in possible_lanes:
                    print('Invalid option for lane')
                    lane = input('Enter lane for new point detector. Options are: [{}, {}] or All: '.format(min(possible_lanes_int), max(possible_lanes_int)))

                if lane.lower() != 'all':
                    lane = int(lane)
                else:
                    lane = 'all'

                while True:
                    position = input('Enter position for new point detector. Options are: [{}, {}]: '.format(0, simulation_params['Bridge Length']))
                    try:
                        position = int(position)
                    except ValueError:
                        print('Invalid option {}. Must be integer type.'.format(position))
                    else:
                        if not (position >= 0 and position <=  simulation_params['Bridge Length']):
                            print('Invalid position {}'.format(position))
                        else:
                            break

                while True:
                    interval = input('Enter macroscopic update interval in seconds: ')
                    try:
                        interval = int(interval)
                    except ValueError:
                        print('Invalid option {}. Must be integer type.'.format(interval))
                    else:
                        break

                simulation_params['detectors'].append({
                    'type': 'point',
                    'position': position,
                    'lane': lane,
                    'interval': interval
                })
            elif answer == '2':
                lane = input('Enter lane for new space detector. Options are: [{}, {}] or All: '.format(min(possible_lanes_int), max(possible_lanes_int)))
                while lane.lower() not in possible_lanes:
                    print('Invalid option for lane')
                    lane = input('Enter lane for new point detector. Options are: [{}, {}] or All: '.format(min(possible_lanes_int), max(possible_lanes_int)))

                if lane.lower() != 'all':
                    lane = int(lane)
                else:
                    lane = 'all'

                while True:
                    position_start = input('Enter start position of new space detector. Options are: [{}, {}]: '.format(0, simulation_params['Bridge Length'] - 1))
                    try:
                        position_start = int(position_start)
                    except ValueError:
                        print('Invalid option {}. Must be integer type.'.format(position_start))
                    else:
                        if not (position_start >= 0 and position_start <=  simulation_params['Bridge Length'] - 1):
                            print('Invalid position {}'.format(position_start))
                        else:
                            break

                while True:
                    position_end = input('Enter end position of new space detector. Options are: [{}, {}]: '.format(position_start + 1, simulation_params['Bridge Length']))
                    try:
                        position_end = int(position_end)
                    except ValueError:
                        print('Invalid option {}. Must be integer type.'.format(position_end))
                    else:
                        if not (position_end >= position_start + 1 and position_end <=  simulation_params['Bridge Length']):
                            print('Invalid position {}'.format(position_start))
                        else:
                            break

                while True:
                    interval = input('Enter macroscopic update interval in seconds: ')
                    try:
                        interval = int(interval)
                    except ValueError:
                        print('Invalid option {}. Must be integer type.'.format(interval))
                    else:
                        break

                simulation_params['detectors'].append({
                    'type': 'space',
                    'position_start': position_start,
                    'position_end': position_end,
                    'lane': lane,
                    'interval': interval
                })
            elif answer.lower() == 'q':
                break

            answer = input(prompt_string)

    # Space - start, end, interval, lane
    # Point - position, interval, lane

    name = input('Enter file name to save the configuration to '
                 '(should end in .json): ')
    if not name:
        name = ''.join(random.choices(string.ascii_uppercase + string.digits,
                                      k=6))
    if not name.endswith('.json'):
        name = name + '.json'
    name = 'configs/' + name
    os.makedirs('configs', exist_ok=True)
    f = open(name, 'w')
    f.write(json.dumps(simulation_params, indent=4, sort_keys=True))
    f.close()
    print('Saved configuration file to: {}'.format(name))
