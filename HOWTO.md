Requires Python 3 to run.

First step is to install the necessary package requirements using:

```pip3 install requirements.txt```

Next, generate a configuration file to use for the simulation:

```./ConfigurationGenerator.py```

Finally, pass this file into the simulator to run it:

```./Simulation.py configs/CONFIG.json```

To run without the display (much, much faster):

```HEADLESS=1 ./Simulation.py configs/CONFIG.json```

Results and graphs are saved to the `output` directory, in a subdirectory of
the seed used in the simulation

Handy one liner to run multiple simulations at once, if all the configs are in `configs/DIR`:

```ind configs/DIR -name "*.json" | sort --version-sort | HEADLESS=1 xargs ./Simulation.py```