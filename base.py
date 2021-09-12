import asyncio
import random
import copy

class Action:

    def __init__(self, game, author):
        self.author = author
        self.game = game
        self.character = None
        self.blockable = None

    def __str__(self):
        return f'Default Action by {self.author}'

    def pov(self):
        return f'Default Action'

    async def resolve(self):
        pass

    async def wait_for_block(self, blockers):
        for player in self.game.players:
            if player == self.author:
                continue
            if len(player.influence) <= 0:
                continue

            possible_actions = [NoBlock(self.game, player, self)]
            for blocker in blockers:
                possible_actions.append(Block(self.game, player, self, blocker))

            block = await player.wait_for_block(self, possible_actions)
            self.game.add_history(str(block))

            if isinstance(block, Block):
                if await block.resolve():
                    return True
                else:
                    return False
        return False

    async def wait_for_challenge(self):
        for player in self.game.players:
            if player == self.author:
                continue
            if len(player.influence) <= 0:
                continue

            possible_actions = [NoChallenge(self.game, player, self), Challenge(self.game, player, self)]

            challenge = await player.wait_for_challenge(self, possible_actions)
            self.game.add_history(str(challenge))

            if isinstance(challenge, Challenge):
                if await challenge.resolve():
                    return True
                else:
                    return False
        return False

class NoBlock(Action):

    def __init__(self, game, author, action):
        super().__init__(game, author)
        self.action = action

    def __str__(self):
        return f'  {self.author} does not block "{self.action}"'

    def pov(self):
        return f'  Don\'t block \"{self.action}\"'


class Block(Action):

    def __init__(self, game, author, action, character):
        super().__init__(game, author)
        self.action = action
        self.character = character

    def __str__(self):
        return f'  🚫 {self.author} blocks \"{self.action}\" with {self.character}'

    def pov(self):
        return f'  🚫 Block \"{self.action}\" with {self.character}'

    async def resolve(self):
        return not await self.wait_for_challenge()


class NoChallenge(Action):

    def __init__(self, game, author, action):
        super().__init__(game, author)
        self.action = action

    def __str__(self):
        return f'    {self.author} does not challenge \"{self.action}\"'

    def pov(self):
        return f'    Do not challenge \"{self.action}\"'

    
class Challenge(Action):
    def __init__(self, game, author, action):
        super().__init__(game, author)
        self.action = action

    def __str__(self):
        return f'    ⚠️ {self.author} challenges "{self.action}"'

    def pov(self):
        return f'    ⚠️ Challenge \"{self.action}\"'
        
    async def resolve(self):
        if self.action.character not in self.action.author.influence:
            self.game.add_history(f'Challenge successful: {self.action.author} does not have {self.action.character}')
            await self.action.author.lose_influence()
            return True
        else:
            self.game.add_history(f'Challenge unsuccessful: {self.action.author} does have {self.action.character}')
            await self.author.lose_influence()
            return False

class TargetedAction(Action):
    
    def __init__(self, game, author, target):
        super().__init__(game, author)
        self.target = target

    def __str__(self):
        return f'Targeted Action at {self.target} by {self.author}'

    def pov(self):
        return f'Targeted Action at {self.target}'


class Income(Action):

    async def resolve(self):
        self.author.coins += 1

    def __str__(self):
        return f'{self.author} takes income'

    def pov(self):
        return f'Income (+1 coin)'


class ForeignAid(Action):

    def __init__(self, game, author):
        super().__init__(game, author)
        self.blockable = ['Duke']

    async def resolve(self):
        block = await self.wait_for_block(self.blockable)
        
        if not block:
            self.author.coins += 2

    def __str__(self):
        return f'{self.author} takes foreign aid'

    def pov(self):
        return f'Foreign Aid (+2 coins, can be blocked by Duke)'


class Coup(TargetedAction):

    async def resolve(self):
        self.author.coins -= 7
        await self.target.lose_influence()

    def __str__(self):
        return f'{self.author} coupes {self.target}'

    def pov(self):
        return f'Coup {self.target}'

class Tax(Action):

    def __init__(self, game, author):
        super().__init__(game, author)
        self.character = 'Duke'
    
    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if not challenge:
            self.author.coins += 3

    def __str__(self):
        return f'{self.author} uses a Duke to take tax'

    def pov(self):
        return f'Duke: Tax (+3 Coins)'


class Assassinate(TargetedAction):

    def __init__(self, game, author, target):
        super().__init__(game, author, target)
        self.character = 'Assassin'
        self.blockable = ['Contessa']
    
    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if challenge:
            return

        block = await self.wait_for_block(self.blockable)

        if block:
            return
        
        self.author.coins -= 3
        await self.target.lose_influence()

    def __str__(self):
        return f'{self.author} uses an Assassin to assassinate {self.target}'

    def pov(self):
        return f'Assassin: Assassinate {self.target} (-3 Coins)'


class ExchangeFirst(Action):

    def __init__(self, game, author):
        super().__init__(game, author)
        self.character = 'Ambassador'

    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if challenge:
            return

        self.game.deck.append(self.author.influence[0])
        self.author.influence.remove(self.author.influence[0])
        random.shuffle(self.game.deck)
        self.author.influence.append(self.game.deck[-1])
        self.game.deck.remove(self.game.deck[-1])
        
    def __str__(self):
        return f'{self.author} uses an Ambassador to exchange one card with the court deck'

    def pov(self):
        return f'Ambassador: Exchange {self.influence[0]} with court deck.'


class ExchangeSecond(Action):
    
    def __init__(self, game, author):
        super().__init__(game, author)
        self.character = 'Ambassador'

    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if challenge:
            return

        self.game.deck.append(self.author.influence[1])
        self.author.influence.remove(self.author.influence[1])
        random.shuffle(self.game.deck)
        self.author.influence.append(self.game.deck[-1])
        self.game.deck.remove(self.game.deck[-1])
        
    def __str__(self):
        return f'{self.author} uses an Ambassador to exchange one card with the court deck'

    def pov(self):
        return f'Ambassador: Exchange {self.influence[1]} with court deck.'


class ExchangeBoth(Action):
    
    def __init__(self, game, author):
        super().__init__(game, author)
        self.character = 'Ambassador'

    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if challenge:
            return

        for i in range(2):
            self.game.deck.append(self.author.influence[0])
            self.author.influence.remove(self.author.influence[0])
        random.shuffle(self.game.deck)
        for i in range(2):
            self.author.influence.append(self.game.deck[-1])
            self.game.deck.remove(self.game.deck[-1])

        
    def __str__(self):
        return f'{self.author} uses an Ambassador to exchange two cards with the court deck'

    def pov(self):
        return f'Ambassador: Exchange {self.influence[0]} and {self.influence[1]} with court deck.'


class Steal(TargetedAction):

    def __init__(self, game, author, target):
        super().__init__(game, author, target)
        self.character = 'Captain'
        self.blockable = ['Captain', 'Ambassador']
    
    async def resolve(self):
        challenge = await self.wait_for_challenge()
        
        if challenge:
            return

        block = await self.wait_for_block(self.blockable)

        if block:
            return
        
        coins = min(2, self.target.coins)
        self.target.coins -= coins
        self.author.coins += coins

    def __str__(self):
        return f'{self.author} uses a Captain to steal from {self.target}'

    def pov(self):
        return f'Captain: Steal from {self.target} (steal up to 2 coins)'


cards = ['Duke', 'Assassin', 'Ambassador', 'Captain', 'Contessa']
deck = []
[[deck.append(card) for j in range(3)] for card in cards]


class Player:

    def __init__(self, name):
        self.name = name
        self.coins = 2
        self.influence = []
        self.starting_influence = []

    def __str__(self):
        return f'{self.name} (influence: {len(self.influence)} | coins: {self.coins})'

    def generate_possible_actions(self):
        if self.coins >= 10:
            possible_actions = []

            for player in self.game.players:
                if player == self:
                    continue
                if len(player.influence) <= 0:
                    continue
                possible_actions.append(Coup(self.game, self, player))

            return possible_actions


        possible_actions = [Income(self.game, self), ForeignAid(self.game, self)]
        possible_actions += [Tax(self.game, self)]
        possible_actions += [ExchangeFirst(self.game, self)]

        if len(self.influence) > 1:
            possible_actions += [ExchangeBoth(self.game, self)]
            if self.influence[0] != self.influence[1]:
                 possible_actions += [ExchangeSecond(self.game, self)]

        for player in self.game.players:
            if player == self:
                continue
            if len(player.influence) <= 0:
                continue
            possible_actions.append(Steal(self.game, self, player))

        if self.coins >= 7:
            for player in self.game.players:
                if player == self:
                    continue
                if len(player.influence) <= 0:
                    continue
                possible_actions.append(Coup(self.game, self, player))
        elif self.coins >= 3:
            for player in self.game.players:
                if player == self:
                    continue
                if len(player.influence) <= 0:
                    continue
                possible_actions.append(Assassinate(self.game, self, player))

        return possible_actions

    async def turn(self):
       possible_actions = self.generate_possible_actions()
       action = await self.wait_for_action(possible_actions)
       self.game.add_history('🃏 ' + str(action))
       await action.resolve()

    async def lose_influence(self):
        influence = await self.wait_for_lose_influence()
        self.game.add_history(f'💔 {self} loses {influence}')
        self.influence.remove(influence)
        return

    async def wait_for_lose_influence(self):
        return self.influence[0]

    async def wait_for_action(self, possible_actions):
        return possible_actions[0]

    async def wait_for_challenge(self, action, possible_actions):
        return possible_actions[0]

    async def wait_for_block(self, action, possible_actions):
        return possible_actions[0]

    



class Lobby:

    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

class Game:

    def __init__(self, lobby):
        self.history = []
        self.deck = copy.copy(deck)
        self.players = lobby.players
        for player in self.players:
            player.game = self
        self.deal_influence()
        self.add_history(str(''.join([f'{player.name}: {player.influence}\n' for player in self.players])))

    def deal_influence(self):
        for player in self.players:
            for _ in range(2):
                influence = random.choice(self.deck)
                player.influence.append(influence)
                player.starting_influence.append(influence)
                self.deck.remove(influence)

    def add_history(self, text):
        self.history.append(text)
        #print(text)

    def win(self):
        players_with_influence = [player for player in self.players if len(player.influence) > 0]
        if len(players_with_influence) == 0:
            raise Exception('all players ded')
        elif len(players_with_influence) == 1:
            return players_with_influence[0]
        else:
            return False

    async def run(self):
        self.round = 0
        while not self.win():
            self.round += 1
            self.add_history(f'round {self.round}')

            for player in self.players:
                if len(player.influence) <= 0:
                    continue
                await player.turn()

                if self.win():
                    break
        
        self.winner = self.win()
        self.add_history(f'{self.winner} won')