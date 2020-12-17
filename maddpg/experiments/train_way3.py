import argparse
import pickle
import time

import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow.contrib.layers as layers

import maddpg.maddpg.common.tf_util as U
from maddpg.maddpg.trainer.maddpg import MADDPGAgentTrainer, GROUPAgentTrainer
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser("Reinforcement Learning experiments for multiagent environments")
    # Environment
    parser.add_argument("--scenario", type=str, default="simple_spread_way2", help="name of the scenario script")
    parser.add_argument("--max-episode-len", type=int, default=10, help="maximum episode length")
    parser.add_argument("--num-episodes", type=int, default=1000, help="number of episodes")
    parser.add_argument("--num-adversaries", type=int, default=0, help="number of adversaries")
    parser.add_argument("--good-policy", type=str, default="maddpg", help="policy for good agents")
    parser.add_argument("--adv-policy", type=str, default="maddpg", help="policy of adversaries")
    # Core training parameters
    parser.add_argument("--lr", type=float, default=1e-2, help="learning rate for Adam optimizer")
    parser.add_argument("--gamma", type=float, default=0.95, help="discount factor")
    parser.add_argument("--batch-size", type=int, default=10, help="number of episodes to optimize at the same time")
    parser.add_argument("--num-units", type=int, default=64, help="number of units in the mlp")
    # Checkpointing
    parser.add_argument("--exp-name", type=str, default="full_obs_comm_seperate_nn", help="name of the experiment")
    parser.add_argument("--save-dir", type=str, default="/tmp/policy/", help="directory in which training state and model should be saved")
    parser.add_argument("--save-rate", type=int, default=200, help="save model once every time this many episodes are completed")
    parser.add_argument("--load-dir", type=str, default="", help="directory in which training state and model are loaded")
    # Evaluation
    parser.add_argument("--restore", action="store_true", default=False)
    parser.add_argument("--display", action="store_true", default=False)
    parser.add_argument("--benchmark", action="store_true", default=False)
    parser.add_argument("--benchmark-iters", type=int, default=20, help="number of iterations run for benchmarking")
    parser.add_argument("--benchmark-dir", type=str, default="/Users/chenjingdi/Desktop/code/Jingdi-MADDPG/maddpg/benchmark_files/", help="directory where benchmark data is saved")
    parser.add_argument("--plots-dir", type=str, default="/Users/chenjingdi/Desktop/code/Jingdi-MADDPG/maddpg/learning_curves/", help="directory where plot data is saved")
    return parser.parse_args()

def mlp_model(input, num_outputs, scope, reuse=False, num_units=64, rnn_cell=None):
    # This model takes as input an observation and returns values of all actions
    with tf.variable_scope(scope, reuse=reuse):
        out = input
        out = layers.fully_connected(out, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_outputs, activation_fn=None)
        return out

def make_env(scenario_name, arglist, benchmark=False):
    from mpe.multiagent.environment import MultiAgentEnv
    import mpe.multiagent.scenarios as scenarios

    # load scenario from script
    scenario = scenarios.load(scenario_name + ".py").Scenario()
    # create world
    world = scenario.make_world()
    # create multiagent environment
    if benchmark:
        env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation, scenario.benchmark_data)
    else:
        env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation)
    return env

def get_group_trainers(env, obs_shape_n, arglist):
    trainers = []

    model = mlp_model
    trainer = GROUPAgentTrainer
    obs_n = []
    for i in range(0, 5):
        obs_n.append([a[i] for a in obs_shape_n])

    for i in range(env.n):
        for j in range(0, 5):
            trainers.append(trainer(
                "agent_%d_group" % j, model, obs_n[j], env.group_space_output, i, arglist,
                local_q_func=(arglist.adv_policy=='ddpg')))

    return trainers


def get_trainers(env, num_adversaries, obs_shape_n, arglist):
    trainers = []  # physical movement trainer
    comm_trainers = []

    model = mlp_model
    trainer = MADDPGAgentTrainer
    for i in range(num_adversaries):
        trainers.append(trainer(
            "agent_%d" % i, model, obs_shape_n, env.physical_action_space, i, arglist,
            local_q_func=(arglist.adv_policy=='ddpg')))
        comm_trainers.append(trainer(
            "agent_%d_comm" % i, model, obs_shape_n, env.comm_action_space, i, arglist,
            local_q_func=(arglist.adv_policy == 'ddpg')))

    for i in range(num_adversaries, env.n):
        trainers.append(trainer(
            "agent_%d" % i, model, obs_shape_n, env.physical_action_space, i, arglist,
            local_q_func=(arglist.adv_policy == 'ddpg')))
        comm_trainers.append(trainer(
            "agent_%d_comm" % i, model, obs_shape_n, env.comm_action_space, i, arglist,
            local_q_func=(arglist.adv_policy == 'ddpg')))

    return trainers, comm_trainers

def train(arglist):
    with U.single_threaded_session():
        # Create environment
        env = make_env(arglist.scenario, arglist, arglist.benchmark)
        # Create agent trainers
        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]

        group_shape_n = []
        for i in range(env.n):
            current_shape_n = [env.group_space_input[i][j].shape for j in range(0, 5)]
            group_shape_n.append(current_shape_n)

        num_adversaries = min(env.n, arglist.num_adversaries)
        trainers, comm_trainers = get_trainers(env, num_adversaries, obs_shape_n, arglist)
        group_trainers = get_group_trainers(env, group_shape_n, arglist)
        print('Using good policy {} and adv policy {}'.format(arglist.good_policy, arglist.adv_policy))

        # Initialize
        U.initialize()

        for agent in trainers:
            agent.saver = tf.train.Saver()
        for agent in comm_trainers:
            agent.saver = tf.train.Saver()

        # Load previous results, if necessary
        if arglist.load_dir == "":
            arglist.load_dir = arglist.save_dir
        if arglist.display or arglist.restore or arglist.benchmark:
            print('Loading previous state...')
            U.load_state(arglist.load_dir)

        episode_rewards = [0.0]  # sum of rewards for all agents
        agent_rewards = [[0.0] for _ in range(env.n)]  # individual agent reward
        final_ep_rewards = []  # sum of rewards for training curve
        final_ep_ag_rewards = []  # agent rewards for training curve
        final_ep_ag_rewards_0 =[]
        final_ep_ag_rewards_1 = []
        final_ep_ag_rewards_2 = []
        agent_info = [[[]]]  # placeholder for benchmarking info
        saver = tf.train.Saver()
        obs_n = env.reset()
        episode_step = 0
        train_step = 0
        t_start = time.time()

        print('Starting iterations...')
        while True:
            # get action
            group_obs = []
            group1 = []
            group2 = []
            group3 = []
            group4 = []
            group5 = []
            for obs in obs_n:
                group1.append([obs[0], obs[2]])
                group2.append([obs[1], obs[3]])
                group3.append([obs[14], obs[15]])

                group4.append([obs[4], obs[6], obs[8], obs[10], obs[12]])
                group5.append([obs[5], obs[7], obs[9], obs[11], obs[13]])

                group_obs.append(group1)
                group_obs.append(group2)
                group_obs.append(group3)
                group_obs.append(group4)
                group_obs.append(group5)

            physical_action_n = [agent.action(obs) for agent, obs in zip(trainers,obs_n)]
            comm_action_n = [agent.action(obs) for agent, obs in zip(comm_trainers,obs_n)]

            group_output = [] ##3 * 5

            action_n = []
            for phy, com in zip(physical_action_n, comm_action_n) :
                action_n.append(np.concatenate((phy, com), axis=0))
            # environment step
            new_obs_n, rew_n, done_n, info_n = env.step(action_n)
            episode_step += 1
            done = all(done_n)
            terminal = (episode_step >= arglist.max_episode_len)
            # collect experience
            for i, agent in enumerate(trainers):
                agent.experience(obs_n[i], physical_action_n[i], rew_n[i], new_obs_n[i], done_n[i], terminal)
            for i, agent in enumerate(comm_trainers):
                agent.experience(obs_n[i], comm_action_n[i], rew_n[i], new_obs_n[i], done_n[i], terminal)

            obs_n = new_obs_n

            for i, rew in enumerate(rew_n):
                episode_rewards[-1] += rew
                agent_rewards[i][-1] += rew

            if done or terminal:
                obs_n = env.reset()
                episode_step = 0
                episode_rewards.append(0)
                for a in agent_rewards:
                    a.append(0)
                agent_info.append([[]])

            # increment global step counter
            train_step += 1

            # for benchmarking learned policies
            if arglist.benchmark:
                for i, info in enumerate(info_n):
                    agent_info[-1][i].append(info_n['n'])
                if train_step > arglist.benchmark_iters and (done or terminal):
                    file_name = arglist.benchmark_dir + arglist.exp_name + '.pkl'
                    print('Finished benchmarking, now saving...')
                    with open(file_name, 'wb') as fp:
                        pickle.dump(agent_info[:-1], fp)
                    break
                continue

            # for displaying learned policies
            if arglist.display:
                time.sleep(0.1)
                env.render()
                continue

            # update all trainers, if not in display or benchmark mode
            loss = None
            for agent in trainers:
                agent.preupdate()
            for agent in comm_trainers:
                agent.preupdate()
            for agent in trainers:
                loss = agent.update(trainers, train_step)
            for agent in comm_trainers:
                loss = agent.update(comm_trainers, train_step)

            # save model, display training output
            if terminal and (len(episode_rewards) % arglist.save_rate == 0):
                U.save_state(arglist.save_dir, saver=saver)
                # print statement depends on whether or not there are adversaries
                if num_adversaries == 0:
                    print("steps: {}, episodes: {}, mean episode reward: {}, time: {}".format(
                        train_step, len(episode_rewards), np.mean(episode_rewards[-arglist.save_rate:]), round(time.time()-t_start, 3)))
                else:
                    print("steps: {}, episodes: {}, mean episode reward: {}, agent episode reward: {}, time: {}".format(
                        train_step, len(episode_rewards), np.mean(episode_rewards[-arglist.save_rate:]),
                        [np.mean(rew[-arglist.save_rate:]) for rew in agent_rewards], round(time.time()-t_start, 3)))
                t_start = time.time()
                # Keep track of final episode reward
                final_ep_rewards.append(np.mean(episode_rewards[-arglist.save_rate:]))
                for i, rew in enumerate(agent_rewards):
                    if i % 3 == 0:
                        final_ep_ag_rewards_0.append(np.mean(rew[-arglist.save_rate:]))
                    if i % 3 == 1:
                        final_ep_ag_rewards_1.append(np.mean(rew[-arglist.save_rate:]))
                    if i % 3 == 2:
                        final_ep_ag_rewards_2.append(np.mean(rew[-arglist.save_rate:]))
                    final_ep_ag_rewards.append(np.mean(rew[-arglist.save_rate:]))

            # saves final episode reward for plotting training curve later
            if len(episode_rewards) > arglist.num_episodes:

                for i, agent in enumerate(comm_trainers):
                    model_path = arglist.plots_dir + arglist.exp_name + "_" + str(arglist.num_episodes) + '_agent_' + str(i) + 'model.ckpt'
                    saver.save(U.get_session(), model_path)

                rew_file_name = arglist.plots_dir + arglist.exp_name + "_" + str(arglist.num_episodes) + '_rewards.csv'
                csv1 = pd.DataFrame(final_ep_rewards).to_csv(rew_file_name, index=False)

                agrew_file_name = arglist.plots_dir + arglist.exp_name + "_" + str(arglist.num_episodes) + '_agrewards.csv'
                csv2 = pd.DataFrame(final_ep_ag_rewards).to_csv(agrew_file_name, index=False)


                entireObs = []
                for i, agent in enumerate(comm_trainers):
                    if i == 1:
                        entireObs.extend(agent.collectEntrieObs())


                agrew_file_name = arglist.plots_dir + arglist.exp_name + "_" + str(arglist.num_episodes) + '_replaybufferObs.csv'
                csv3 = pd.DataFrame(entireObs).to_csv(agrew_file_name, index=False)

                print('...Finished total of {} episodes.'.format(len(episode_rewards)))
                break
    return final_ep_rewards, final_ep_ag_rewards, final_ep_ag_rewards_0, final_ep_ag_rewards_1, final_ep_ag_rewards_2


if __name__ == '__main__':
    arglist = parse_args()
    final_ep_rewards, final_ep_ag_rewards, final_ep_ag_rewards_0, final_ep_ag_rewards_1, final_ep_ag_rewards_2 = train(arglist)
    plt.plot(final_ep_rewards, label = "final_ep_rewards")
#    plt.plot(final_ep_ag_rewards, label="final_ep_ag_rewards")
#    plt.plot(final_ep_ag_rewards_0, label = "final_ep_ag_rewards_0")
#    plt.plot(final_ep_ag_rewards_1, label="final_ep_ag_rewards_1")
#    plt.plot(final_ep_ag_rewards_2, label="final_ep_ag_rewards_2")
#    plt.legend(loc='lower right', fontsize=15)
    plt.xlabel('Episode', fontsize=15)
    plt.ylabel('Average Reward after every 20 Episode finished', fontsize=15)
    plt.grid(True)

    plt.show()


