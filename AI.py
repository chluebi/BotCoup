import random
import asyncio

from base import *

class RandomActionPlayer(Player):

    async def wait_for_action(self, possible_actions):
        return random.choice(possible_actions)

    async def wait_for_lose_influence(self):
        return self.influence[0]

    async def wait_for_challenge(self, action, possible_actions):
        return possible_actions[0]

    async def wait_for_block(self, action, possible_actions):
        return possible_actions[0]

class RandomEverything(Player):
    
    async def wait_for_action(self, possible_actions):
        return random.choice(possible_actions)

    async def wait_for_lose_influence(self):
        return random.choice(self.influence)

    async def wait_for_challenge(self, action, possible_actions):
        return random.choice(possible_actions)

    async def wait_for_block(self, action, possible_actions):
        return random.choice(possible_actions)

class HarryHonest(Player):
    async def wait_for_action(self, possible_actions):
        honest_actions = []
        for action in possible_actions:
            if action.character is None or action.character in self.influence:
                honest_actions.append(action)
        return random.choice(honest_actions)

    async def wait_for_lose_influence(self):
        return random.choice(self.influence)

    async def wait_for_challenge(self, action, possible_actions):
        return possible_actions[0]

    async def wait_for_block(self, action, possible_actions):
        for a in possible_actions:
            if a.character in self.influence:
                return a
        return possible_actions[0]