import numpy as np
from mpe.multiagent.core import World, Agent, Landmark
from mpe.multiagent.scenario import BaseScenario

"""
Same as simple_reference, except one agent is the ‘speaker’ (gray) that does not move (observes goal of other agent),
and other agent is the listener (cannot speak, but must navigate to correct landmark).

"""

'''
1 speaker and 2 listener
comm dim = 2 original is 3


'''


class Scenario(BaseScenario):
    def make_world(self):
        world = World()
        # set any world properties first
        world.dim_c = 2
        num_landmarks = 3
        world.collaborative = True
        # add agents
        world.agents = [Agent() for i in range(3)]
        for i, agent in enumerate(world.agents):
            agent.name = 'agent %d' % i
            agent.collide = False
            agent.size = 0.075
        # speaker
        world.agents[0].movable = True
        # listener_1 and listener_2
        world.agents[1].silent = True
        world.agents[2].silent = True
        # add landmarks
        world.landmarks = [Landmark() for i in range(num_landmarks)]
        for i, landmark in enumerate(world.landmarks):
            landmark.name = 'landmark %d' % i
            landmark.collide = False
            landmark.movable = False
            landmark.size = 0.04
        # make initial conditions
        self.reset_world(world)
        return world

    def reset_world(self, world):
        # assign goals to agents
        for agent in world.agents:
            agent.goal_a_1 = None
            agent.goal_a_2 = None
            agent.goal_b = None
            agent.goal_c = None

        # want listener_1 to go to the goal landmark
        world.agents[0].goal_a_1 = world.agents[1]
        world.agents[0].goal_b = np.random.choice(world.landmarks)

        # want listener_2 to go to the goal landmark
        world.agents[0].goal_a_2 = world.agents[2]
        world.agents[0].goal_c = np.random.choice(world.landmarks)

        # random properties for agents
        for i, agent in enumerate(world.agents):
            agent.color = np.array([0.25, 0.25, 0.25])
            # random properties for landmarks
        world.landmarks[0].color = np.array([0.65, 0.15, 0.15])
        world.landmarks[1].color = np.array([0.15, 0.65, 0.15])
        world.landmarks[2].color = np.array([0.15, 0.15, 0.65])
        # special colors for goals
        world.agents[0].goal_a_1.color = world.agents[0].goal_b.color + np.array([0.45, 0.45, 0.45])
        world.agents[0].goal_a_2.color = world.agents[0].goal_b.color + np.array([0.15, 0.15, 0.15])

        # set random initial states
        for agent in world.agents:
            agent.state.p_pos = np.random.uniform(-1, +1, world.dim_p)
            agent.state.p_vel = np.zeros(world.dim_p)
            agent.state.c = np.zeros(world.dim_c)
        for i, landmark in enumerate(world.landmarks):
            landmark.state.p_pos = np.random.uniform(-1, +1, world.dim_p)
            landmark.state.p_vel = np.zeros(world.dim_p)

    def benchmark_data(self, agent, world):
        # returns data for benchmarking purposes
        return self.reward(agent, self.reward)

    def reward(self, agent, world):
        # squared distance from listener to landmark
        a = world.agents[0]
        dist2 = np.sum(np.square(a.goal_a_1.state.p_pos - a.goal_b.state.p_pos)) + np.sum(np.square(a.goal_a_2.state.p_pos - a.goal_c.state.p_pos))
        return -dist2

    def observation(self, agent, world):
        # goal color
        goal_color_b = np.zeros(world.dim_color)
        goal_color_c = np.zeros(world.dim_color)


        if agent.goal_b is not None:
            goal_color_b = agent.goal_b.color
        if agent.goal_c is not None:
            goal_color_c = agent.goal_c.color


        # get positions of all entities in this agent's reference frame
        entity_pos = []
        for entity in world.landmarks:
            entity_pos.append(entity.state.p_pos - agent.state.p_pos)

        # communication of all other agents
        comm = []
        for other in world.agents:
            if other is agent or (other.state.c is None): continue
            comm.append(other.state.c)

        # speaker
        if agent.movable:
            return np.concatenate([goal_color_b] + [goal_color_c])
        # listener
        if agent.silent:
            return np.concatenate([agent.state.p_vel] + entity_pos + comm)

