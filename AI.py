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


class SamSensible(Player):
    async def wait_for_action(self, possible_actions):
        honest_actions = []
        for action in possible_actions:
            if action.character is None or action.character in self.influence:
                honest_actions.append(action)

        def is_strongest(action):
            return len(action.target.influence) >= max([len(player.influence) for player in self.game.players])

        def is_richest(action):
            return action.target.coins >= max([player.coins for player in self.game.players])

        if len(honest_actions) <= 1:
            return honest_actions[0]

        if random.random() < 0.05:
            return random.choice(honest_actions)

        for action in honest_actions:
            if isinstance(action, Assassinate):
                if is_strongest(action) and is_richest(action):
                    return action
        for action in honest_actions:
            if isinstance(action, Assassinate):
                if is_strongest(action):
                    return action

        for action in honest_actions:
            if isinstance(action, Coup):
                if is_strongest(action) and is_richest(action):
                    return action
        for action in honest_actions:
            if isinstance(action, Coup):
                if is_strongest(action):
                    return action

        if max([player.coins for player in self.game.players]) >= 7:
            for action in honest_actions:
                if isinstance(action, Steal):
                    if is_strongest(action) and is_richest(action):
                        return action
            for action in honest_actions:
                if isinstance(action, Steal):
                    if is_richest(action):
                        return action

        for action in honest_actions:
            if isinstance(action, Tax):
                return action

        for action in honest_actions:
            if isinstance(action, ExchangeBoth):
                return action
            if isinstance(action, ExchangeFirst):
                return action
            if isinstance(action, ExchangeSecond):
                return action

        return honest_actions[0]

    async def wait_for_lose_influence(self):
        return random.choice(self.influence)

    async def wait_for_challenge(self, action, possible_actions):
        return possible_actions[0]

    async def wait_for_block(self, action, possible_actions):
        for a in possible_actions:
            if a.character in self.influence:
                if hasattr(action, 'target'):
                    if action.target is self:
                        return a
                else:
                    return a
        return possible_actions[0]