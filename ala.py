"""
Safe Malware Behavior Simulator (educational)
Simulates conceptual behavior of Viruses, Worms, and Trojans on an abstract network.
No file or network activity — purely in-memory.

Dependencies: matplotlib
Run: python3 malware_simulator_safe.py
"""

import random
import math
import matplotlib.pyplot as plt

# ---------------------------
# Configuration parameters
# ---------------------------
NUM_NODES = 80
AVG_DEGREE = 4        # average number of connections per node
TIMESTEPS = 60
TRIALS = 1

# Threat-specific probabilities (tune for classroom demos)
VIRUS_SPREAD_CHANCE = 0.18   # chance virus spreads during a file-sharing interaction
WORM_SPREAD_CHANCE = 0.25    # chance worm attempts to infect each neighbor each timestep
TROJAN_DOWNLOAD_CHANCE = 0.02 # per node per timestep chance to "download" a trojan disguised item
TROJAN_ACTIVATION_DELAY = 6  # timesteps after infection until payload activates (simulated)

# How often nodes "interact" for virus-like spreading per timestep
MEETINGS_PER_TIMESTEP = 30

random.seed(42)

# ---------------------------
# Network generation (random graph)
# ---------------------------
def generate_random_graph(n, avg_degree):
    # simple undirected random graph using approximate Erdos-Renyi p
    p = avg_degree / (n - 1)
    neighbors = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < p:
                neighbors[i].add(j)
                neighbors[j].add(i)
    return neighbors

# ---------------------------
# Node state model
# ---------------------------
class Node:
    def __init__(self, node_id):
        self.id = node_id
        # states
        self.clean = True
        self.infected_virus = False
        self.infected_worm = False
        self.infected_trojan = False
        self.trojan_activation_time = None  # timestep when trojan activates

    def status(self):
        flags = []
        if self.infected_virus: flags.append("Virus")
        if self.infected_worm: flags.append("Worm")
        if self.infected_trojan:
            if self.trojan_activation_time is None:
                flags.append("Trojan(dormant)")
            else:
                flags.append("Trojan(active)")
        if not flags: return "Clean"
        return "+".join(flags)

# ---------------------------
# Simulation functions
# ---------------------------
def simulate_one_run(neighbors, params):
    n = len(neighbors)
    nodes = [Node(i) for i in range(n)]
    T = params['timesteps']

    history_counts = {
        'clean': [],
        'virus': [],
        'worm': [],
        'trojan_dormant': [],
        'trojan_active': [],
    }

    # Seed initial infections (safe and limited)
    # Put a single virus in node 0, worm in node 1, trojan disguised "download" at node 2
    nodes[0].infected_virus = True
    nodes[1].infected_worm = True
    nodes[2].infected_trojan = True
    nodes[2].trojan_activation_time = None  # still dormant until triggered

    # Simulation loop
    for t in range(T):
        # 1) Worm spread: each worm-infected node attempts to infect neighbors
        new_worm_infections = set()
        for node in nodes:
            if node.infected_worm:
                for neigh in neighbors[node.id]:
                    if not nodes[neigh].infected_worm:
                        if random.random() < params['worm_spread_chance']:
                            new_worm_infections.add(neigh)
        for idx in new_worm_infections:
            nodes[idx].infected_worm = True

        # 2) Virus spread: modeled via random "meetings" between pairs (simulates file-exchange)
        for _ in range(params['meetings_per_timestep']):
            a = random.randrange(n)
            # pick one neighbor to represent local file sharing if available, otherwise random
            neighs = list(neighbors[a])
            if neighs:
                b = random.choice(neighs)
            else:
                b = random.randrange(n)
            # if one has virus and other not, chance to infect
            if nodes[a].infected_virus and not nodes[b].infected_virus:
                if random.random() < params['virus_spread_chance']:
                    nodes[b].infected_virus = True
            if nodes[b].infected_virus and not nodes[a].infected_virus:
                if random.random() < params['virus_spread_chance']:
                    nodes[a].infected_virus = True

        # 3) Trojan arrival via "downloads": nodes randomly download a disguised item
        for node in nodes:
            if not node.infected_trojan and random.random() < params['trojan_download_chance']:
                node.infected_trojan = True
                # activation occurs after a delay (simulated)
                node.trojan_activation_time = t + params['trojan_activation_delay']

        # 4) Trojan activation check (when activation time passed, simulate payload activation)
        for node in nodes:
            if node.infected_trojan and node.trojan_activation_time is not None:
                if t >= node.trojan_activation_time:
                    # When activated we mark as active; activation can cause additional effects
                    # For safety: we do not simulate destructive payload; we just mark active.
                    # Optionally we might increase worm-like spread probability for activated trojan.
                    node.trojan_activation_time = -1  # sentinel for "activated"

        # 5) Record counts
        counts = {
            'clean': 0,
            'virus': 0,
            'worm': 0,
            'trojan_dormant': 0,
            'trojan_active': 0
        }
        for node in nodes:
            if not (node.infected_virus or node.infected_worm or node.infected_trojan):
                counts['clean'] += 1
            if node.infected_virus:
                counts['virus'] += 1
            if node.infected_worm:
                counts['worm'] += 1
            if node.infected_trojan:
                if node.trojan_activation_time is None:
                    counts['trojan_dormant'] += 1
                elif node.trojan_activation_time == -1:
                    counts['trojan_active'] += 1
                else:
                    counts['trojan_dormant'] += 1
        for k in history_counts:
            history_counts[k].append(counts[k])

    return history_counts, nodes

# ---------------------------
# Run experiments and plot
# ---------------------------
def run_experiment(num_nodes=NUM_NODES, avg_degree=AVG_DEGREE, timesteps=TIMESTEPS, trials=TRIALS):
    neighbors = generate_random_graph(num_nodes, avg_degree)
    all_histories = []
    for _ in range(trials):
        history, final_nodes = simulate_one_run(neighbors, {
            'timesteps': timesteps,
            'virus_spread_chance': VIRUS_SPREAD_CHANCE,
            'worm_spread_chance': WORM_SPREAD_CHANCE,
            'trojan_download_chance': TROJAN_DOWNLOAD_CHANCE,
            'trojan_activation_delay': TROJAN_ACTIVATION_DELAY,
            'meetings_per_timestep': MEETINGS_PER_TIMESTEP
        })
        all_histories.append(history)
    # If multiple trials, average
    avg_history = {}
    for key in all_histories[0].keys():
        avg_history[key] = [0]*timesteps
    for h in all_histories:
        for k in h:
            for i,val in enumerate(h[k]):
                avg_history[k][i] += val / len(all_histories)
    # Plotting
    t = list(range(timesteps))
    plt.figure(figsize=(10,6))
    plt.plot(t, avg_history['clean'], label='Clean')
    plt.plot(t, avg_history['virus'], label='Virus-infected')
    plt.plot(t, avg_history['worm'], label='Worm-infected')
    plt.plot(t, avg_history['trojan_dormant'], label='Trojan (dormant)')
    plt.plot(t, avg_history['trojan_active'], label='Trojan (active)')
    plt.title('Safe Malware Behavior Simulator — Abstract Counts over Time')
    plt.xlabel('Timestep')
    plt.ylabel('Number of nodes')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_experiment()
