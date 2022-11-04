#!/usr/bin/env python
"""One of the minimax method implementation for playing Kalah.

Here is a pseudocode for Minimax algorithm.

The Minimax algorithm is going deep into the searching tree and playing for
both sides: the player and his/her opponent. When it expands a node for the 
player it needs to take into account a possible answer of opponent and vice 
versa.

To become familiar with this method you must understand a simple idea:
    We suppose that our opponent is a smart guy and he/she makes always the
    optimal moves.
 
There are several main functions in the pseudocode below:
    
    Minimax-Decision: starts to build a searching tree with creation of a 
        root node and generating its neighbors // in the class MinMaxMethod 
        below this function is called make_move
    Max-Value: returns heuristic function value for a node in which the player 
        makes the move; the corresponded function in the class is _max_value
    Min-Value: returns heuristic function value for a node where the opponent 
        makes the move; the corresponded function in the class is _min_value
    Terminal-Test: checks if a current state could be expanded or not; the
        corresponded function in the class is _terminal_test
    Utility: calculates an estimation of who will win probably in a specific
        state; corresponded function in the class is _utility

    def Minimax-Decision( state ):
        neighborhood = state.get_all_neighbors( )
        best_value, best_neighbor = -float('inf'), None
        for neighbor in neighborhood:
            neighbor_value = min_value( neighbor.get_state( ) )
            if best_value < neighbor_value :
                best_value, best_neighbor = neighbor_value, neighbor
        return best_neighbor.action( )
        
    def Max-Value( state ):
        if Terminal-Test( state ):
            return Utility( state )
        max_value = -float('inf')
        neighborhood = state.get_all_neighbors( )
        for neighbor in neighborhood:
            max_value = max( max_value, Min-Value( neighbor ) )
        return max_value
        
    def Min-Value( state ):
        if Terminal-Test( state ):
            return Utility( state )
        min_value = float('inf')
        neighborhood = state.get_all_neighbors( )
        for neighbor in neighborhood:
            min_value = min( min_value, Max-Value( neighbor ) )
        return min_value
        
Tips of how to create your own minimax algorithm.

    The structure of the algorithm is the same for different games. There are 
    two points where all decisions are made:
        1) When deciding to terminate a state (node). Look up _terminal_test
        function.
        2) How to estimate state's scores if a state is not a finishing one.
        Look up _utility function.

@author: Oleksii Molchanovskyi
@organization: Ukrainian Catholic University
@country: Ukraine

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

#
# For the purposes of the testing. Please check the code at the bottom of 
# the file to details
#
if __name__ == "__main__":
    from method import Method, raiseNotDefined
else:
    from methods.method import Method, raiseNotDefined


class MinMaxMethod(Method):
    """Class with MinMax method for playing Kalah
    
    Main idea:
        Build a searching tree where each node is a game's state. When expanding
        the active player's node then use _min_value function to find a best
        move for an opponent player. In other case _max_value to find a best
        move for the current player. 
        We finish to expand the tree when its height is equal to self._ai_level.
        For each leaf node we calculate a heuristic function value with 
        _utility function.
        
        In the code below we call this player - Max, an opponent - Min.
    
    Attributes:
        Please refer to method.py for details    
    """
    _name = "Min-max"
    _short_name = "Min-max"
    _disabled = False
    
    def __init__(self, player_num, ai_level=1, run_time_limit=60):
        """Inits MinMaxMethod object
        
        Args:
            Please refer Method class description for details
        """
        # 
        # We're using 90% of maximum run time limit to work
        #
        super(MinMaxMethod, self).__init__(player_num, ai_level, run_time_limit*0.9)
        self._ai_level = max(1, min(ai_level, 5))
    
    def _other_player(self):
        """Returns an opponent player's number (0 or 1)"""
        return (self._player + 1) % 2
    
    def _terminal_test(self, state, player, depth=0):
        """Checks if the state for player is a terminal one (a leaf).
        
        In a pure Minimax algorithm the searching tree is expanding down to 
        leafs. A leaf is a state (node) in which the game stopped. But it 
        would take too much time. So we need to decide somehow earlier when to
        stop. For this purpose we use a node's depth and ai_level. The last one
        is used like a depth limit. The node becomes a leaf (termination-node)
        when:
            1) it has a state where the game stopped OR
            2) its depth is greater then depth limit OR
            3) time is expiring
        In one of these cases we return True, otherwise - False.
        
        Args:
            state: state to check
            player: active player's number for the specified state
            depth: node's depth in the searching tree
        Returns:
            True/False: finished or not
        """

        # TODO: Propose and implement your own criteria of when the expanding should be stopped.

        raiseNotDefined()
    
    def _utility(self, state):
        """Calculates a heuristic function value for a state
        
        Utility is a substitute for heuristics, but the meaning is the same.
        The purpose of this function is to make an estimation of the future 
        possible game result using just a specified state.
        It returns some value. If this value is greater then 0 then player MAX
        is expected to win; if less then 0 then player MIN is expected to win.
        
        Here we use simple heuristics: a difference between player's kalah and 
        opponent's kalah.

        Args:
            state: 
                
        Returns:
            Heuristic value for the specified state
        """

        #         TODO: Propose and implement your own utility function. For instance
        #             you can also take into account amount of stones in all holes
        #             of the each player side of the board.

        raiseNotDefined()
    
    def _max_value(self, state, depth=1):
        """Part of Minimax algorithm for the MAX player
        
        Args:
            state: specific state
            depth: depth of the state in a searching tree
            
        Returns:
            Heuristic function value for this state. If this state is a 
            terminal then function returns result of self._utility function. 
            In other case runs the algorithm for the state's children 
            recursively and calculates the result as a maximum value among the
            all neighbors.
        """
        
        #
        # If the state is terminal then we should stop expanding the searching
        # tree from it. Return the utility of the current state in this case.
        #
        if self._terminal_test(state, self._player):
            return self._utility(state)
            
        # 
        # Among all neighbors of the state you should find the one that has
        # bigest heuristic value. Recall that you take into account your
        # opponent move so to check the result of _min_value of the neighbor
        #
        neighbors = state.get_all_neighbors(self._player)
        value = -float('inf')
        for new_state in neighbors:
            value = max(value, self._min_value(new_state['state'], depth))
            
        # 
        # Return calculated value 
        #
        return value
            
    def _min_value(self, state, depth=1):
        """Part of Minimax algorithm for the MIN player
        
        Args:
            state: specific state
            depth: depth of the state in a searching tree
            
        Returns:
            Heuristic function value for this state. If this state is a 
            terminal then function returns a result of self._utility function. 
            In other case runs the algorithm for the state's children 
            recursively and calculates the result as a minimum value among the
            all neighbors.
        """
        
        #
        # If the state is terminal then we should stop expanding the searching
        # tree from it. Return the utility of the current state in this case.
        #
        if self._terminal_test(state, self._other_player(), depth):
            return self._utility(state)
        
        # 
        # Among all neighbors of the state you should find the one that has
        # the smallest heuristic value. Recall that this function is about your
        # opponent move so you take into account your own answer and should
        # check the result of _max_value of each neighbor
        #
        neighbors = state.get_all_neighbors(self._other_player())
        value = float('inf')
        for new_state in neighbors:
            value = min(value, self._max_value(new_state['state'], depth+1))
            
        # 
        # Return calculated value 
        #
        return value
    
    def make_move(self, state):
        """Makes a decision of the player's next move
        
        The Minimax algorithm is the basis of this function. 
        Actually the first iteration of the minimax algorithm is done here:
            You generate all neighbors of the initial state
            And try to find the one that maximize the value of each neighbor
        
        Args:
            state: current board state
        
        Returns:
            Player's hole number which defines a player's next move
        """
        super(MinMaxMethod, self).make_move(state)
        # print("AI Level: ", self._ai_level)
        
        #
        # Generate all possible neighbors for the state, i.e. check all 
        # possible moves of the player at the moment and for any possible move
        # create a new neighbor. All this stuff is done by get_all_neighbors
        # function.
        #
        neighbors = state.get_all_neighbors(self._player)
        best_value, best_state = -float('inf'), None
        
        #
        # Check if there is only one possible move then return it without any
        # thinking
        #
        if len(neighbors) == 1:
            return neighbors[0]['hole'][0]
            
        #
        # Among all neighbors find the one that has maximum value and return it
        #
        for new_state in neighbors:
            value = self._min_value(new_state['state'])
            if best_value < value :
                best_value, best_state = value, new_state
                
        if best_state:
            return best_state['hole'][0]
            
        # 
        # In case of wrong moves return -1
        #
        return -1


#
# You can test method while changing the board state below and simply executing 
# this module 
#
if __name__ == "__main__":
    from state import KalahState
    state = KalahState(0)
    state._kalahs = [6, 4]
    state._holes = [[1, 4, 0, 0, 0, 0], [0, 0, 0, 0, 3, 1]]
    method = MinMaxMethod(1, 1)
    print (method.make_move(state))