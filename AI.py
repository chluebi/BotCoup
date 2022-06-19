import random
import asyncio

from base import *


class OfflinePlayer(Player):

    async def wait_for_action(self, possible_actions):
        print('\nChoose a move')
        print(self)
        print('Your influences', self.influence)
        for i, action in enumerate(possible_actions):
            print(i, action.pov())
        return possible_actions[int(input('Enter Move:'))]

    async def wait_for_lose_influence(self):
        print('\nChoose an influence to lose')
        print(self)
        print('Your influences', self.influence)
        for i, action in enumerate(self.influence):
            print(i, 'lose', action)
        return self.influence[int(input('Enter Influence to lose:'))]

    async def wait_for_challenge(self, action, possible_actions):
        print('\nChoose wether to challenge')
        print(self)
        print('Your influences', self.influence)
        for i, action in enumerate(possible_actions):
            print(i, action.pov())
        return possible_actions[int(input('Enter if you want to challenge:'))]

    async def wait_for_block(self, action, possible_actions):
        print('\nChoose wether to block')
        print(self)
        print('Your influences', self.influence)
        for i, action in enumerate(possible_actions):
            print(i, action.pov())
        return possible_actions[int(input('Enter if you want to block:'))]

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


class FionaFuture(Player):

    async def init(self):
        self.memory = [[] for p in self.game.players]

    async def on_action(self, action):
        if not hasattr(self, 'memory'):
            return
        if hasattr(action, 'character') and action.author != self.game:
            self.memory[self.game.players.index(action.author)].append(action.character)

    async def wait_for_action(self, possible_actions):
        old_output = self.game.print_output
        self.game.print_output = False
        actions, value = await self.wait_for_action_future(possible_actions, self.game, self, [], 4)
        self.game.print_output = old_output
        print('Fiona', actions, value)
        return actions[0][0]

    async def wait_for_action_future(self, possible_actions, game, self_copy, action_chain, max_recursion, recursion=0):
        honest_actions = []
        for action in possible_actions:
            if action.character is None or action.character in self_copy.influence:
                honest_actions.append(action)

        best_value = 0
        best_action = None

        actions = []

        for action in possible_actions:
            if True:
                game_copy = copy.deepcopy(game)
                self_copy = game_copy.players[self.game.players.index(self)]
                self_copy.memory = copy.copy(self.memory)

                new_players = []
                for player in game_copy.players:
                    p = FionaFuture('sim fiona')
                    p.game = game_copy
                    p.influence = copy.copy(self.memory[game_copy.players.index(player)])
                    p.coins = player.coins
                    new_players.append(p)

                game_copy.players = new_players

                possible_actions_copy = self_copy.generate_possible_actions()
                if len(possible_actions) != len(possible_actions_copy):
                    pass
                    
                action_copy = None
                for a in possible_actions_copy:
                    if type(a) == type(action):
                        action_copy = a
                        break

                if action_copy is None:
                    continue

                await action_copy.resolve()

                value = (len(self_copy.influence)**10 + (self_copy.coins)**1.5) * len([p for p in game_copy.players if len(p.influence) > 0])
                for p in [p for p in game_copy.players if p is not self_copy]:
                    if len(p.influence) <= 0:
                        value += 2**10 + 13**1.5
                    else:
                        value += (2-len(p.influence))**10 + (13-p.coins)**1.5

                
                new_action_chain = copy.copy(action_chain + [(action, value)])

                if game_copy.win():
                    if game_copy.winner == self_copy:
                        value += 500
                    else:
                        value += -500
                else:
                    if recursion+1 >= max_recursion:
                        value = value
                    else:
                        actions, new_value = await self.wait_for_action_future(possible_actions_copy, game_copy, self_copy, new_action_chain, max_recursion, recursion=recursion+1)
                        value = (value + new_value * 0.5)/1.5

                if action not in honest_actions:
                    value = value * 0.6

                if best_action is None or (value > best_value):
                    #print(value, action, '\nreplaces\n',  best_value, best_action)
                    best_value = value
                    best_action = action

        actions = [(best_action, best_value)] + actions

        #if recursion == 0:
            #print(recursion+1, actions)
        #print(recursion, best_action, best_value)
        return copy.copy(actions), best_value

    async def wait_for_lose_influence(self):
        influence =  random.choice(self.influence)
        return influence

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