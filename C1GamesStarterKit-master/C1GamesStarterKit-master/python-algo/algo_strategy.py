import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import cache_moves
from collections import defaultdict

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.enemy_offense_spawn_locations = defaultdict(lambda: 0)
        self.enemy_scrambler_spawn_location = defaultdict(lambda: 0)


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        # game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        self.build_starter_defences(game_state)

        if game_state.turn_number < 5:
            self.build_base_scramblers(game_state)
        else:
            if self.build_self_destruct(game_state):
                self.spawn_self_destruct(game_state)
            else:
                self.build_base_scramblers(game_state)
            # self.build_reactive_defense(game_state)

        self.counter_spawn(game_state)
        # self.place_offensive_units(game_state)

        # Now let's analyze the enemy base to see where their defenses are concentrated.
        # If they have many units in the front we can build a line for our EMPs to attack them at long range.
        """if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
            self.emp_line_strategy(game_state)
        else:
            # They don't have many units in the front so lets figure out their least defended area and send Pings there.

            # Only spawn Ping's every other turn
            # Sending more at once is better since attacks can only hit a single ping at a time
            if game_state.turn_number % 2 == 1:
                # To simplify we will just check sending them from back left and right
                ping_spawn_location_options = [[13, 0], [14, 0]]
                best_location = self.least_damage_spawn_location(game_state, ping_spawn_location_options)
                game_state.attempt_spawn(PING, best_location, 1000)

            # Lastly, if we have spare cores, let's build some Encryptors to boost our Pings' health.
            # encryptor_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
            # game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)
        """

    def build_starter_defences(self, game_state):
        game_map = game_state.game_map
        destructor_locations = [[3, 11], [3, 10], [24, 11], [24, 10]]
        wall_locations = [[0, 13], [1, 13], [2, 12], [3, 12], [4, 12], [27, 13], [26, 13], [25, 12], [24, 12], [23, 12]]
        upgrade_locations = [[0, 13], [1, 13], [2, 12], [27, 13], [26, 13], [25, 12]]

        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        game_state.attempt_spawn(FILTER, wall_locations)
        game_state.attempt_upgrade(upgrade_locations)

    def build_self_destruct(self, game_state):
        game_map = game_state.game_map
        destructor_locations = [[11, 5], [16, 5]]
        wall_locations = [[8, 6], [9, 6], [10, 5], [11, 4], [12, 5], [13, 5], [13, 4], [14, 4], [10, 6], [11, 6],
                          [12, 6], [17, 6], [15, 4], [16, 4], [17, 5], [18, 6], [19, 7], [20, 7], [20, 6], [15, 6],
                          [16, 6]]
        idx = 0
        while game_state.get_resource(BITS) > 0 and idx < len(wall_locations):
            loc = wall_locations[idx]
            game_state.attempt_spawn(FILTER, loc)
            idx += 1
        setup_finished = idx == len(wall_locations) - 1
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        return setup_finished

    def spawn_self_destruct(self, game_state):
        bomb_locations = [[8, 5], [15, 1]]
        game_state.attempt_spawn(SCRAMBLER, bomb_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build destructor one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1] + 1]
            game_state.attempt_spawn(DESTRUCTOR, build_location)

    def build_base_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        scrambler_locations = [[8, 5], [19, 5]]
        idx = 0
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and idx < len(scrambler_locations):
            deploy_location = scrambler_locations[idx]
            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            idx += 1

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[
                game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (
                            valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: `https://docs.c1games.com/json-docs.html`
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        spawns = events["spawn"]
        for spawn in spawns:
            if spawn[3] == 1:
                unit_owner_self = True
            else:
                unit_owner_self = False

            if not unit_owner_self:
                location = spawn[0]
                spawn_id = spawn[1]
                if spawn_id in [3, 4]:
                    self.enemy_offense_spawn_locations[tuple(location)] += 1
                elif spawn_id == 5:
                    self.enemy_scrambler_spawn_location[tuple(location)] += 1

    def freq_spawn(self, dictionary):
        arr = []
        for key in dictionary:
            val = dictionary[key]
            arr.append((key, val))
        arr.sort(key=lambda x: x[1])
        if len(arr) == 0:
            return -1
        return arr[-1]

    def counter_spawn(self, game_state):
        freq_spawn_opp_location = self.freq_spawn(self.enemy_offense_spawn_locations)
        if freq_spawn_opp_location == -1:
            return
        freq_spawn_opp_location = freq_spawn_opp_location[0]
        path = game_state.find_path_to_edge(freq_spawn_opp_location)
        for _ in range(3):
            game_state.attempt_spawn(SCRAMBLER, path[-1], num=1)

    """def compute_ideal_start(self, game_state):
        # returns the least damage received location and the most damage dealt location
        # for each of the starting points
        # get the path
        # compute how much damange a given offensive unit can deal
        # place half at least damage spawn location
        # place half at most damage dealing location
        starting_locations = []
        for i in range(14):
            starting_locations.append([i, 13 - i])
        for i in range(14):
            starting_locations.append([14 + i, i])
        game_map = game_state.game_map
        least_damage_location = self.least_damage_spawn_location(game_state, starting_locations)
        most_damage_location = None
        max_damage = float('-inf')
        EMP_unit = gamelib.GameUnit(EMP, game_state.config)
        for starting_location in starting_locations:
            path = game_state.find_path_to_edge(starting_location)
            if path is None:
                continue
            damage = 0
            units_of_enemy_can_damage = []
            for path_location in path:
                # assume placing EMPs right now
                for location in game_map.get_locations_in_range(path_location, EMP_unit):
                    if (len(game_map[location[0], location[1]]) > 0):
                        units_of_enemy_can_damage.extend(game_map[location[0], location[1]])
            damage = len(units_of_enemy_can_damage)
            if damage > max_damage:
                max_damage = damage
                most_damage_location = starting_location
        return least_damage_location, most_damage_location

    def place_offensive_units(self, game_state):
        allowance = game_state.BITS // 4 + 1 - 2  # placing 2 scramblers
        least_damage_received_location, most_damage_dealt_location = self.compute_ideal_start(game_state)
        num_ping_least_damage_received = 0
        num_emp_most_damage_dealt = 0
        if allowance >= 6:
            num_ping_least_damage_received = allowance // 2
            num_emp_most_damage_dealt = (allowance // 2) // 3
        elif allowance >= 4:
            num_ping_least_damage_received = allowance - 3
            num_emp_most_damage_dealt = 1
        else:
            num_ping_least_damage_received = allowance

        game_state.attempt_spawn(game_state.PING, least_damage_received_location, num_ping_least_damage_received)
        game_state.attempt_spawn(game_state.EMP, most_damage_dealt_location, num_emp_most_damage_dealt)"""

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path is None:
                continue
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR,
                                                                                             game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
