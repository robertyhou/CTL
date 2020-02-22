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


        enemy_offense_spawn_locations = {}
        enemy_scrambler_spawn_locations = {}
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

    path_length = len(path)
    path_intercept = path[int(0.5 * path_length)]
    path_intercept_radius = game_state.get_locations_in_range(path_intercept, 2)
    for location in self.offense_locations:
        defensive_path = game_state.find_path_to_edge(location)
        overlap = False
        for i in path_intercept_radius:
            for j in defensive_path:
                if i ==j:
                    overlap = True
                    location = i
                    break
        if path_intercept in path:
            for _ in range(game_state.get_resource(1, 1) // 2):
                game_state.attempt_spawn(SCRAMBLER, path[-1], num=1)

