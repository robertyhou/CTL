import json
import gamelib
#These are default dicts starting with 0
def on_action_frame(turn_string, scored_on_locations, enemy_offense_spawn_locations, enemy_scrambler_spawn_location):
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
                scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(scored_on_locations))

        spawns = events["spawn"]
        for spawn in spawns:
            if spawn[3] == 1:
                unit_owner_self = True
            if not unit_owner_self:
                location = spawn[0]
                spawn_id = spawn[1]
                if spawn_id in [3, 4]:
                    enemy_offense_spawn_locations[tuple(location)] += 1
                elif spawn_id == 5:
                    enemy_scrambler_spawn_location[tuple(location)] += 1
