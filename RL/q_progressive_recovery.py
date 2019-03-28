from deep_q_network import DeepQNetwork
from rl_environment import environment
import networkx as nx
from graph_helper import r_graph, r_2d_graph, r_tree, get_root, DP_optimal, plot_graph, simulate_tree_recovery, plot_bar_x
import numpy as np
import random
import itertools
from ratio_heuristic import ratio_heuristic
import time

# Load checkpoint
load_path = "weights/weights.ckpt"
save_path = "weights/weights.ckpt"

'''
read = False
util_20 = True

# grid params
grid_nodes = 5

# random graph
num_nodes = grid_nodes ** 2
resources = 1

if read:
    G = nx.read_gpickle('experiments/{0}x{0}_a.gpickle'.format(grid_nodes))
else:
    if util_20:
        reward_save = 'experiments/{0}x{0}_b.txt'.format(grid_nodes) 
        G = r_2d_graph(grid_nodes, grid_nodes, util_range=[1,20], demand_range=[1,10])
        nx.write_gpickle(G, 'experiments/{0}x{0}_b.gpickle'.format(grid_nodes))
    else:
        #G = r_tree(num_nodes)
        reward_save = 'experiments/{0}x{0}_a.txt'.format(grid_nodes)
        G = r_2d_graph(grid_nodes, grid_nodes)
        nx.write_gpickle(G, 'experiments/{0}x{0}_a.gpickle'.format(grid_nodes))
'''
num_nodes = 20; p=0.2
G = r_graph(num_nodes, p)
resources = 1

print('num_edges:', G.number_of_edges())

try:
    plot_graph(G, get_root(G), 'rl_graph.png')
except:
    print('No display')

env = environment(G, [get_root(G)], resources)
n_y = len(env.actions_permutations)

print("Ratio Heuristic", ratio_heuristic(G, [get_root(G)], resources))
print()

# Initialize DQN
DQN = DeepQNetwork(
    n_y=n_y,
    n_x=num_nodes,
    resources=resources,
    env=env,
    learning_rate=0.1,
    replace_target_iter=100,
    memory_size=20000,
    batch_size=256,
    reward_decay=0.3,
    epsilon_min=0.2,
    epsilon_greedy_decrement=0.5e-4,
    # load_path=load_path,
    save_path=save_path
)

EPISODES = 5000
rewards = []
total_steps_counter = 0
episodes_since_max = 0

optimal_action_sequences = []
overall_start = time.time()

for episode in range(EPISODES):

    observation, done = env.reset()
    episode_reward = 0
    action_sequence = []
    start = time.time()

    while not done:
        # 1. Choose an action based on observation
        action = DQN.choose_action(observation)

        # check for random action
        if action == -1:
            action = env.random_action()

        # save the taken action
        action_sequence.append(action)

        #print('Chosen action', action)
        # 2. Take the chosen action in the environment
        observation_, reward, done = env.step(action)
        #print(observation_, reward, done)

        # 3. Store transition
        DQN.store_transition(observation, action, reward, observation_)

        episode_reward += reward

        if total_steps_counter > 5000:
            # 4. Train
            DQN.learn()

        if done:
            rewards.append(episode_reward)
            max_reward_so_far = np.amax(rewards)

            # if maximum reward so far, save the action sequence
            if episode_reward == max_reward_so_far:
                optimal_action_sequences.append((action_sequence, episode_reward))
                episodes_since_max = 0
                # DQN.epsilon = 1

            print("==========================================")
            print("Episode: ", episode)
            print("Reward: ", round(episode_reward, 2))
            print("Epsilon: ", round(DQN.epsilon,2))
            print("Max reward so far: ", max_reward_so_far)

            end = time.time()
            print('Episode time:', end - start)
            start = time.time()

            break

        # Save observation
        observation = observation_

        # Increase total steps
        total_steps_counter += 1

    episodes_since_max += 1
    if episodes_since_max > 1100:
        break

    if episode > (EPISODES - 100):
        DQN.epsilon_min = 0

overall_end = time.time()

# if we have a reasonable number of nodes, we can compute optimal
if num_nodes < 24:
    dp_time = time.time()
    print("Optimal:", DP_optimal(G, [get_root(G)], resources))
    dp_time_end = time.time()
    print('DP time:', dp_time_end - dp_time)

print()

#print('Tree Heuristic:', simulate_tree_recovery(G, resources, get_root(G), clean=False))
ratio_time_start = time.time()
print("Ratio Heuristic", ratio_heuristic(G, [get_root(G)], resources))
ratio_time_end = time.time()
print('Ratio time:', ratio_time_end - ratio_time_start)

# TESTING
# convert our best optimal action sequence to vector representation, test it for correctness
opt = optimal_action_sequences[len(optimal_action_sequences) - 1][0]
reward = optimal_action_sequences[len(optimal_action_sequences) - 1][1]

print()
#print('RL action sequence:')
env.reset()
true_r = 0
for action in opt:
    #print('action index', action)
    _, r, d = env.step(action, debug=True)
    true_r += r

print('reward during training:', reward)
plot_bar_x(rewards, 'episode', 'reward_graph.png')
with open(reward_save, 'w') as f:
    for item in rewards:
        f.write('%s\n' % item)

print('RL method time (s): ', overall_end - overall_start)
