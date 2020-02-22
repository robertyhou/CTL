import algo_strategy
import game_state
import gamelib
import gamelib.GameUnit

def compute_ideal_start(game_state):
    #returns the least damage received location and the most damage dealt location
    #for each of the starting points
    #get the path
    #compute how much damange a given offensive unit can deal
    #place half at least damage spawn location
    #place half at most damage dealing location
    starting_locations = []
    for i in range(14):
        starting_locations.append([i,13-i])
    for i in range(14):
        starting_locations.append([14+i,i])
    game_map = game_state.game_map
    least_damage_location = least_damage_spawn_location(game_state,starting_locations)
    most_damage_location = None
    max_damage = float('-inf')
    EMP_unit = GameUnit(game_state.EMP,game_state.config)
    for starting_location in starting_locations:
        path = game_state.find_path_to_edge(starting_location)
        damage = 0
        units_of_enemy_can_damage = []
        for path_location in path:
            #assume placing EMPs right now
            for location in game_map.get_locations_in_range(path_location, EMP_unit):
                if(len(game_map[location[0],location[1]])>0):
                    units_of_enemy_can_damage.extend(game_map[location[0],location[1]])
        damage = len(units_of_enemy_can_damage)
        if damage>max_damage:
            max_damage=damage
            most_damage_location = starting_location
    return least_damage_location, most_damage_location

def place_offensive_units(game_state):
    allowance = game_state.BITS //4 +1 -2 #placing 2 scramblers
    least_damage_received_location, most_damage_dealt_location = compute_ideal_start(game_state)
    num_ping_least_damage_received = 0
    num_emp_most_damage_dealt = 0
    if allowance>=6:
        num_ping_least_damage_received = allowance//2
        num_emp_most_damage_dealt = (allowance//2)//3
    elif allowance>=4:
        num_ping_least_damage_received = allowance - 3
        num_emp_most_damage_dealt=1
    else:
        num_ping_least_damage_received = allowance

    game_state.attempt_spawn(game_state.PING,least_damage_received_location,num_ping_least_damage_received)
    game_state.attempt_spawn(game_state.EMP, most_damage_dealt_location,num_emp_most_damage_dealt)

def least_damage_spawn_location( game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR,
                                                                                             game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]



