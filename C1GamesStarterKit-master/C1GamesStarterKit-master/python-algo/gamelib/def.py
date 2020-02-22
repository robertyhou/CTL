

def setup(game_state):
    game_map = game_state.game_map
    destructor_locations = [[3, 11], [3, 10], [24, 11], [24, 10]]
    wall_locations = [[0, 13], [1, 13], [2, 12], [3, 12], [4, 12], [27, 13], [26, 13], [25, 12], [24, 12], [23, 12]]
    upgrade_locations = []

    # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
    # More community tools available at: https://terminal.c1games.com/rules#Download
    game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
    game_state.attempt_spawn(FILTER, wall_locations)
    game_state.attempt_upgrade(filter_locations)