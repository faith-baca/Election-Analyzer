# 6.0002 Spring 2022

from state import State


def load_election(filename):
    """
    Reads the contents of a file, with data given in the following tab-separated format:
    State[tab]Democrat_votes[tab]Republican_votes[tab]EC_votes

    Parameters:
    filename - the name of the data file as a string

    Returns:
    a list of State instances
    """
    with open(filename, "r") as open_file: #opens the file and stores the contents in open_file
        file_contents = open_file.readlines()[1:] # reads through the file excluding the first line
        state_list = []
        
        for line in file_contents:
            plain_line = line.strip() # gets rid of \n characters indicating new lines
            line_list = plain_line.split("\t") # splits each line where there's a tab
            state = State(line_list[0], line_list[1], line_list[2], line_list[3]) # creates a state object for each line using the state and votes 
            state_list.append(state) # list of state objects
        

    return state_list    


def election_winner(election):
    """
    Finds the winner of the election based on who has the most amount of EC votes.
    All of EC votes from a state go to the party with the majority vote for modeling simplicity

    Parameters:
    election - a list of State instances

    Returns:
    a tuple, (winner, loser) of the election i.e. ('dem', 'rep') if Democrats won, else ('rep', 'dem')
    """
    rep_ec_votes = 0
    dem_ec_votes = 0
    for state in election:
        state_winner = state.get_winner() # determines which party had more popular votes in each state
        if state_winner == "rep": # if republicans had majority popular vote in a state,
            rep_ec_votes += state.get_ecvotes() # add all that state's electoral college votes to rep_ec_votes
        else: # same process for democrats
            dem_ec_votes += state.get_ecvotes()
    
    if rep_ec_votes > dem_ec_votes: # if republicans have most ec votes, they win the election
        return ("rep", "dem")
    else:
        return ("dem", "rep")
        

def winner_states(election):
    """
    Finds the list of States that were won by the winning candidate (lost by the losing candidate).

    Parameters:
    election - a list of State instances

    Returns:
    A list of State instances won by the winning candidate
    """
    rep_states_won = []
    dem_states_won = []
    for state in election: 
        state_winner = state.get_winner()
        if state_winner == "rep": # adds all states won by reps to rep_states_won as state objects
            rep_states_won.append(state)
        else: # same for dems
            dem_states_won.append(state)
    
    if election_winner(election) == ("rep", "dem"): # calls other helper function to determine winner and which list will be returned
        return rep_states_won
    else:
        return dem_states_won



def ec_votes_to_flip(election, total=538):
    """
    Finds the number of additional EC votes required by the loser to change election outcome.
    A party wins when they earn half the total number of EC votes plus 1.

    Parameters:
    election - a list of State instances
    total - total possible number of EC votes

    Returns:
    int, number of additional EC votes required by the loser to change the election outcome
    """
    winner_vote_total = 0
    half_votes = total / 2

    for state in winner_states(election): # adds up all the winner's electoral college votes
        winner_vote_total += state.get_ecvotes()

    loser_vote_total = total - winner_vote_total # subtracts the the winner's votes from total votes to find loser votes
    
    return int(half_votes - loser_vote_total) + 1 # number of votes needed for loser to win



def combinations(L):
    """
    Helper function to generate powerset of all possible combinations
    of items in input list L

    Parameters:
    L - list of items

    Returns:
    a list of lists that contains all possible
    combinations of the elements of L
    """


    def get_binary_representation(n, num_digits):
        """
        Inner function to get a binary representation of items to add to a subset,
        which combinations() uses to construct and append another item to the powerset.

        Parameters:
        n and num_digits are non-negative ints

        Returns:
            a num_digits str that is a binary representation of n
        """
        result = ''
        while n > 0:
            result = str(n%2) + result
            n = n//2
        if len(result) > num_digits:
            raise ValueError('not enough digits')
        for i in range(num_digits - len(result)):
            result = '0' + result
        return result

    powerset = []
    for i in range(0, 2**len(L)):
        binStr = get_binary_representation(i, len(L))
        subset = []
        for j in range(len(L)):
            if binStr[j] == '1':
                subset.append(L[j])
        powerset.append(subset)
    return powerset

def brute_force_swing_states(winner_states, ec_votes_needed):
    """
    Finds a subset of winner_states that would change an election outcome if
    voters moved into those states, these are our swing states. 

    Parameters:
    winner_states - a list of State instances that were won by the winner
    ec_votes_needed - int, number of EC votes needed to change the election outcome

    Returns:
    * A tuple containing the list of State instances such that the election outcome would change if additional
      voters relocated to those states, as well as the number of voters required for that relocation.
    * A tuple containing the empty list followed by zero, if no possible swing states.
    """
    best_combo = [] 
    minimum_voters_moved = 0

    possible_move_combinations = combinations(winner_states) # generates all possible combos of the winner states
    for combo in possible_move_combinations: # creates voters moved and the sum of the states' ec votes for every combo
        voters_moved = 0
        sum_ec_votes = 0

        for state in combo: # moves (margin) voters for every state in each combo, adds each state's ec votes to sum_ec_votes
            margin = state.get_margin() + 1 # number of votes needed to flip a state
            voters_moved += margin
            sum_ec_votes += state.get_ecvotes()

        # or statement for the first iteration since minimum_voters_moved is 0 on the first round
        if sum_ec_votes >= ec_votes_needed and (voters_moved < minimum_voters_moved or minimum_voters_moved == 0):
            best_combo = combo # updates best_combo and minimum_voters_moved
            minimum_voters_moved = voters_moved

    return (best_combo, minimum_voters_moved)



def max_voters_moved(winner_states, max_ec_votes):
    """
    Finds the largest number of voters needed to relocate to get at most max_ec_votes
    for the election loser.

    Analogy to knapsack problem:
        Given a list of states each with a weight(ec_votes) and value(margin+1),
        determine the states to include in a collection so the total weight(ec_votes)
        is less than or equal to the given limit(max_ec_votes) and the total value(voters displaced)
        is as large as possible.

    Parameters:
    winner_states - a list of State instances that were won by the winner
    max_ec_votes - int, the maximum number of EC votes

    Returns:
    * A tuple containing the list of State instances such that the maximum number of voters need to
      be relocated to these states in order to get at most max_ec_votes, and the number of voters
      required required for such a relocation.
    * A tuple containing the empty list followed by zero, if every state has a # EC votes greater
      than max_ec_votes.
    """

    def helper(winner_states, max_ec_votes, memo = None): # top down approach with memoization
        if memo == None: 
            memo = {} # creates memo to store already done subproblems
        if (len(winner_states), max_ec_votes) in memo: # check if combo of winner_states and max_ec_votes is already in memo
            result = memo[(len(winner_states), max_ec_votes)] 
        elif winner_states == [] or max_ec_votes == 0: # if no more max_ec_votes or winner_states to take from
            result = ([], 0)
        elif winner_states[0].get_ecvotes() > max_ec_votes: # if state has too many ec_votes, don't take it
            result = helper(winner_states[1:], max_ec_votes, memo) # runs with the rest of the list because first state does not work
        else:
            next_state = winner_states[0]

            # explore left branch (taking state)
            with_to_take, with_voters = helper(winner_states[1:], max_ec_votes - next_state.get_ecvotes(), memo) # if state taken, fewer ec_votes left
            with_voters += next_state.get_margin() + 1

            # explore right branch (not taking state)
            without_to_take, without_voters = helper(winner_states[1:], max_ec_votes, memo)

            # finding optimal solution after exploring both branches
            if with_voters > without_voters:
                result = (with_to_take + [next_state], with_voters)
            else:
                result = (without_to_take, without_voters)

        memo[(len(winner_states), max_ec_votes)] = result # store result in memo

        return result
        
    return helper(winner_states, max_ec_votes)



def min_voters_moved(winner_states, ec_votes_needed):
    """
    Finds a subset of winner_states that would change an election outcome if
    voters moved into those states. Should minimize the number of voters being relocated.
    Only return states that were originally won by the winner (lost by the loser)
    of the election.

    Parameters:
    winner_states - a list of State instances that were won by the winner
    ec_votes_needed - int, number of EC votes needed to change the election outcome

    Returns:
    * A tuple containing the list of State instances (which we can call swing states) such that the
      minimum number of voters need to be relocated to these states in order to get at least
      ec_votes_needed, and the number of voters required for such a relocation.
    * A tuple containing the empty list followed by zero, if no possible swing states.
    """
    winner_ec_votes = 0

    # sums all ec_votes from winner states
    for state in winner_states:
        winner_ec_votes += state.get_ecvotes()

    # loser needs this many ec votes
    delta_ec_votes = winner_ec_votes - ec_votes_needed

    # gets list of non-swing states and max voters moved to flip the election
    non_swing_states, maximum_voters_moved = max_voters_moved(winner_states, delta_ec_votes) 

    total_voters_moved = 0
    swing_states = [] 

    # creates a list of swing states
    for state in winner_states:
        total_voters_moved += state.get_margin() + 1 # voters needed to flip a state
        if state not in non_swing_states: # this is a swing state
            swing_states.append(state)

    min_voters_moved = total_voters_moved - maximum_voters_moved



    return (swing_states, min_voters_moved)



def relocate_voters(election, swing_states, ideal_states = ['AL', 'AZ', 'CA', 'TX']):
    """
    Finds a way to shuffle voters in order to flip an election outcome. Moves voters
    from states that were won by the losing candidate (states not in winner_states), to
    each of the states in swing_states. 

    Parameters:
    election - a list of State instances representing the election
    swing_states - a list of State instances where people need to move to flip the election outcome
                   (result of min_voters_moved or brute_force_swing_states)
    ideal_states - a list of Strings holding the names of states where residents cannot be moved from

    Return:
    * A tuple that has 3 elements in the following order:
        - an int, the total number of voters moved
        - an int, the total number of EC votes gained by moving the voters
        - a dictionary with the following (key, value) mapping:
            - Key: a 2 element tuple of str, (from_state, to_state), the 2 letter State names
            - Value: int, number of people that are being moved
    * None, if it is not possible to sway the election
    """
    states_won = winner_states(election)
    losing_candidate_states = [state for state in election if state.get_name() not in states_won and state.get_name() not in ideal_states]

    ec_votes_needed_to_flip = ec_votes_to_flip(election)

    total_voters_moved = 0
    total_ec_votes_gained = 0
    move_map = {}

    min_voters_to_flip = min_voters_moved(states_won, ec_votes_needed_to_flip)[1] # first element of tuple returned by min_voters_moved
    moveable_voters = sum([(state.get_margin() - 1) for state in losing_candidate_states]) 

    # if there are not enough moveable_voters to flip, no reason to move any voters at all because flipping isn't possible
    if moveable_voters < min_voters_to_flip:
        return None


    else:
        for swing in swing_states:
            votes_needed = swing.get_margin() + 1 
            
            # looping over losing_candidate_states to move voters into swing_states
            for loser in losing_candidate_states:
                votes_available = loser.get_margin() - 1 # -1 so that state remains a loser state
                voters_moved = min(votes_needed, votes_available) # accounts for if there are more available voters than voters needed

                if voters_moved != 0: # min could be 0, but can't move 0 voters
                    votes_needed -= voters_moved 
                    total_voters_moved += voters_moved

                    move_map[(loser.get_name(), swing.get_name())] = voters_moved # creates dictionary of states moved from and to

                    # actually moves voters from loser states into swing states
                    swing.add_losing_candidate_voters(voters_moved)
                    loser.subtract_winning_candidate_voters(voters_moved)

                    # have finally flipped state
                    if votes_needed == 0:
                        ec_votes_needed_to_flip -= swing.get_ecvotes()
                        total_ec_votes_gained += swing.get_ecvotes()
                        break
        
        return (total_voters_moved, total_ec_votes_gained, move_map)





if __name__ == "__main__":
    pass

    year = 2012
    election = load_election(f"{year}_results.txt")
    print(len(election))
    print(election[0])

    winner, loser = election_winner(election)
    won_states = winner_states(election)
    names_won_states = [state.get_name() for state in won_states]
    reqd_ec_votes = ec_votes_to_flip(election)
    print("Winner:", winner, "\nLoser:", loser)
    print("States won by the winner: ", names_won_states)
    print("EC votes needed:",reqd_ec_votes, "\n")

    brute_election = load_election("60002_results.txt")
    brute_won_states = winner_states(brute_election)
    brute_ec_votes_to_flip = ec_votes_to_flip(brute_election, total=14)
    brute_swing, voters_brute = brute_force_swing_states(brute_won_states, brute_ec_votes_to_flip)
    names_brute_swing = [state.get_name() for state in brute_swing]
    ecvotes_brute = sum([state.get_ecvotes() for state in brute_swing])
    print("Brute force swing states results:", names_brute_swing)
    print("Brute force voters displaced:", voters_brute, "for a total of", ecvotes_brute, "Electoral College votes.\n")

    print("max_voters_moved")
    total_lost = sum(state.get_ecvotes() for state in won_states)
    non_swing_states, max_voters_displaced = max_voters_moved(won_states, total_lost-reqd_ec_votes)
    non_swing_states_names = [state.get_name() for state in non_swing_states]
    max_ec_votes = sum([state.get_ecvotes() for state in non_swing_states])
    print("States with the largest margins (non-swing states):", non_swing_states_names)
    print("Max voters displaced:", max_voters_displaced, "for a total of", max_ec_votes, "Electoral College votes.", "\n")


    print("min_voters_moved")
    swing_states, min_voters_displaced = min_voters_moved(won_states, reqd_ec_votes)
    swing_state_names = [state.get_name() for state in swing_states]
    swing_ec_votes = sum([state.get_ecvotes() for state in swing_states])
    print("Complementary knapsack swing states results:", swing_state_names)
    print("Min voters displaced:", min_voters_displaced, "for a total of", swing_ec_votes, "Electoral College votes. \n")


    print("relocate_voters")
    flipped_election = relocate_voters(election, swing_states)
    print("Flip election mapping:", flipped_election)
