import itertools
import math
import random
import csv
import time


NUMBER_OF_SIMULATIONS = 500  # How many times to run the core program.
COURTS = 4              # How many courts will be used.
NUMBER_OF_BREAKS = 2    # How many breaks should everyone get?
PLAYER_COUNT = 24       # How many players in the match.
ROUNDS = 12             # How many rounds will be played.
TEAM_SIZE = 2           # How many people will be on a team? 2 would be a (2 vs 2) game.


# Create a list of possible team combinations.  We will also rank these.  Team ranks
# will help prioritize team choices.
def create_team_combinations(players, team_size):
    # Create a list of all combinations.
    if team_size == 1:
        combos = [(x, x) for x in players]
    else:
        combos = list(itertools.combinations(players, team_size))

    # Iterate through the combinations and order them by closeness.
    # For sorting the format for ranked scores will be (score, combo)
    ranked_combos = list()

    for combo in combos:
        minimum = min(combo)
        maximum = max(combo)
        score = maximum - minimum
        ranked_combos.append((score, combo))

    ranked_combos.sort()
    return ranked_combos


# Choose the teams for a specific round.
def choose_teams(play_order, player_combinations, on_break, max_teams):
    players_used = set(on_break)
    teams = list()

    # Go through the player_combinations and choose the teams that best fit the constraints.
    i = 0
    while len(teams) < max_teams:
        # If for some reason we have exhausted the player_order then exit the loop.
        if i >= len(play_order):
            break
        player = play_order[i][1]

        # If we have already used the current player increment and continue.
        if player in players_used:
            i += 1
            continue

        # Search player_combinations to find the player.
        for team in player_combinations:
            used_flag = False
            team_members = team[1]
            if player in team_members:
                # Check that none of the players have already been used.
                for member in team_members:
                    if member in players_used:
                        used_flag = True
            else:
                continue

            if used_flag:
                continue
            else:
                teams.append(team_members)
                for member in team_members:
                    players_used.add(member)
                break
        i = i + 1

    # If we have an odd number of teams we need to remove one.
    if len(teams) % 2 == 1:
        extra = teams.pop()
        for entry in extra:
            players_used.remove(entry)

    return teams, players_used


# We want to balance the games so that opposing teams are as close to equal as possible.
def balance_matches(schedule):
    matches = dict()

    for key in schedule:
        match = schedule[key]
        sorted_match = list()

        for team in match:
            skill = team[0] + team[1]
            sorted_match.append([skill, team])

        sorted_match.sort()
        new_matches = list()

        for entry in sorted_match:
            new_matches.append(entry[1])
        matches[key] = new_matches

    return matches


# Check how many rounds that each player has played, and put the players who have played
# the most rounds on break.  I added some randomness here to try to avoid some
# artifacts that were showing up in the results.
def set_up_break(play_order, breaks_per_round):
    on_break = set()

    maximum = play_order[-1][0]
    minimum = play_order[0][0]
    players = play_order.copy()
    random.shuffle(players)

    i = maximum
    while i >= minimum and len(on_break) < breaks_per_round:
        j = 0
        while j < len(players):
            if players[j][0] == i:
                on_break.add(players[j][1])
            if len(on_break) >= breaks_per_round:
                break
            j += 1
        i -= 1

    on_break = list(on_break)
    on_break.sort()

    return on_break


# Create a round-robin match schedule given constraints.
def create_match_schedule(courts, number_of_breaks, player_count, rounds, team_size):
    # Set up a dictionary where we will build up our matches.  And another to track players
    # who will be on break.
    matches = dict()
    players_on_break = dict()

    # Create a list of players.
    players = list(range(1, player_count + 1))

    # Create a dict to track the number of rounds played by each player.
    rounds_played = dict()
    for player in players:
        rounds_played[player] = 0

    # Create all possible team combinations.
    combos = create_team_combinations(players, team_size)

    # Calculate the number of people to put on break every round.
    total_breaks = player_count * number_of_breaks
    breaks_per_round = math.ceil(total_breaks / rounds)

    # Set up the matches.
    match = 1
    while match <= rounds:

        # Determine an order for player placement.
        play_order = list()
        for player in players:
            play_order.append((rounds_played[player], player))
        play_order.sort()

        # Determine which players to put on break.
        on_break = set_up_break(play_order, breaks_per_round)
        players_on_break[match] = on_break

        # Determine the number of teams we need for the round.
        max_teams_1 = 2 * courts
        max_teams_2 = (player_count - breaks_per_round) // team_size
        if max_teams_2 % 2 == 1:
            max_teams_2 = max_teams_2 - 1
        number_of_teams = min(max_teams_1, max_teams_2)

        # Let's cycle through our combos and choose our team pairings.
        teams, players_used = choose_teams(play_order, combos, on_break, number_of_teams)
        matches[match] = teams

        # Let's update the rounds played for each player.
        for member in players_used:
            if member not in on_break:
                rounds_played[member] = rounds_played[member] + 1

        # Now remove any team combinations that were used from combos.  I could have used a better
        # data structure in retrospect, but this is probably fast enough.
        i = 0
        while i < len(teams):
            team = teams[i]
            j = 0
            while j < len(combos):
                if combos[j][1] == team:
                    del combos[j]
                    break
                j += 1
            i += 1

        match = match + 1

    # Ok, we have selected the teams that will be playing.  Now we want to partner teams of equal skill.
    matches = balance_matches(matches)

    return matches, players_on_break


# Print the match schedule.
def print_match_schedule(matches, breaks):
    column_width = 35
    courts = len(matches[1]) // 2
    header = 'Round          '
    i = 1
    while i <= courts:
        header_piece = ''
        header_piece = 'Court ' + str(i)
        while len(header_piece) < column_width:
            header_piece = header_piece + ' '
        header = header + header_piece
        i += 1
    length = len(header)
    header = header + 'Rest'
    print(header)

    for key in matches:
        line_up = matches[key]
        if line_up == []:
            break
        print_line = str(key)
        while len(print_line) < 15:
            print_line = print_line + ' '

        i = 0
        while i < len(line_up) - 1:
            team_1 = line_up[i]
            team_2 = line_up[i+1]
            piece = str(team_1) + ' vs ' + str(team_2)
            while len(piece) < column_width:
                piece = piece + ' '
            print_line = print_line + piece
            i = i + 2

        while len(print_line) < length:
            print_line = print_line + ' '

        if key in breaks:
            players = breaks[key]
            players = tuple(players)
            print_line = print_line + str(players)

        print(print_line)


# Given a match and player count determine who is on break.
def recalculate_breaks(match, player_count):
    on_break = dict()
    for key in match:
        players = set(range(1, player_count + 1))
        line_up = match[key]
        playing = set()
        for entry in line_up:
            playing.add(entry[0])
            playing.add(entry[1])
        on_break[key] = players - playing
    return on_break


def create_a_match_csv(matches, breaks):
    # Check the number of courts.
    courts = len(matches[1]) // 2

    # Set up a data set using our match data.
    data = list()
    for key in matches:
        data_entry = dict()
        data_entry["Round"] = key
        line_up = matches[key]
        i = 0
        court = 0
        while i < len(line_up) - 1:
            court = court + 1
            team_1 = line_up[i]
            team_2 = line_up[i+1]
            data_entry['Court ' + str(court)] = str(team_1) + ' vs ' + str(team_2)
            i += 2

        if key in breaks:
            data_entry['Rest'] = str(breaks[key])

        data.append(data_entry)

    # Csv filename
    filename = "matches.csv"

    # Set up the fieldnames
    fieldnames = ["Round"]
    i = 1
    while i <= courts:
        fieldnames.append("Court " + str(i))
        i += 1
    fieldnames.append("Rest")

    # Open the CSV file in write mode
    with open(filename, mode='w', newline='') as file:
        # Create a CSV DictWriter object
        writer = csv.DictWriter(file, fieldnames)

        # Write the header (field names)
        writer.writeheader()

        # Write the rows
        writer.writerows(data)

    print(' ')
    print(f"CSV file '{filename}' created successfully!")


# Ok, our create_match_schedule function creates a schedule with some randomness.  We will run
# that function many times, and check the results to find the most desirable fit.
def find_best_results(runs=NUMBER_OF_SIMULATIONS):
    # Run a loop to get results and then check for the best solution.
    maximum = 1000000
    winner = dict()
    i = 0
    while i < runs:
        matches, breaks = create_match_schedule(COURTS, NUMBER_OF_BREAKS, PLAYER_COUNT, ROUNDS, TEAM_SIZE)
        worst_match = 0
        for key in matches:
            players = matches[key]
            j = 0
            while j < len(players):
                difference = abs(sum(players[j]) - sum(players[j+1]))
                if difference > worst_match:
                    worst_match = difference
                j += 2
        if worst_match < maximum:
            maximum = worst_match
            winner = matches
        i += 1

    # We have a winner, but do to my implementation I am going to recalculate
    # who is on break.
    breaks = recalculate_breaks(winner, PLAYER_COUNT)

    print_match_schedule(winner, breaks)
    create_a_match_csv(winner, breaks)
    return winner, breaks


start = time.time()
find_best_results()
end = time.time()
print('-')
print('The simulation was run ' + str(NUMBER_OF_SIMULATIONS) + ' times.')
print('The total run time was ' + str(end-start) + ' seconds.')