#!/usr/bin/env python
"""Contains state class for the Kalah game

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

from copy import deepcopy

#
# Constans that are used to return turn results up to the calling program
#

# Current move didn't finished
MoveNotEnds = 0
# Current move is finished
MoveEnds = 1
# Current move is finished with the last stone in a player's Kalah
MoveEndsInPlayersKalah = 2
# Current move is finished with the last stone in a player's empty pit
MoveEndsInPlayersEmptyHole = 3
# Current move is wrong (we've got some error)
WrongMove = 4


class KalahStateList(object):
    """Class that stores a list of the Kalah states
    
    Purpose of this class is to provide the main program a list of
    interimediate states for the moves' animation
    
    Attributes:
        _list: a list of states
    """
    _list = []

    def __init__(self):
        """Inits an empty list"""
        self._list = []

    def add_state(self, state, active_player, active_hole=-1, active_kalah=False):
        """Adds a state to list"""
        self._list.append({'state': state.copy(), 'player': active_player, 'hole': active_hole, 'kalah': active_kalah})

    def get_list(self):
        """Returns a reference to list""" 
        return self._list


class KalahState(object):
    """
    Kalah game state
    
    Attributes:
        _holes_num: amount of holes or pits (default: 6)
        _holes: two lists of contents of each player's holes
        _kalahs: amount of stones in each player's kalah
        last_moves: an object of KalahStateList that stores a sequence of
            interimediate states for the moves' animation
        last_move_result: last made move (refer to constants' lists on the top 
            of file)
    """
    _holes_num = 6
    _holes = [[], []]
    _kalahs = [0, 0]
    last_moves = None
    last_move_result = MoveEnds
    
    def __init__(self, stones_per_hole, holes_num=6):
        """Inits a board
        
        Args:
            stones_per_hole: number of stones in each hole on game startup
            holes_num: number of hole (standard is 6)
        """
        self._holes_num = holes_num
        self._holes = [[], []]
        self._kalahs = [0, 0]
        for hole in range(self._holes_num):
            self._holes[0].append(stones_per_hole)
            self._holes[1].append(stones_per_hole)
            
    def holes_num(self):
        """Returns number of holes"""
        return self._holes_num
    
    def player_holes(self, player):
        """Returns a list of number of stones in player's holes"""
        return self._holes[player]
        
    def player_kalah(self, player):
        """Returns amount of stones in player's kalah"""
        return self._kalahs[player]
        
    def player_points(self, player):
        """Returns amount of stones in player's kalah"""
        return self._kalahs[player]
            
    def move(self, player, hole_num):
        """
        Makes a move
        
        During this function a current player's stones are taken from hole with
        hole_num number and are distributed corresponding to game's rules.
        Please refer main.py for game's rules.
        
        If there are several consequent moves of one player then all that 
        moves are combined in one action. 
        
        When this function is finished there will be stored following data:
            last_move_result: result of the last move; see the list of 
                constants on the top of the file
            last_moves: a list of consequent steps (when stones are put one
                by one to corresponding pits)
        
        Args:
            player: current player number (0 or 1)
            hole_num: number of hole or pit from which the move begins
        """
        self.last_moves = None
        last_moves = KalahStateList()
        
        def opposite_hole(hole_num):
            return self._holes_num - hole_num - 1
        
        def make_turn(player, hole_num=-1, skip_kalah=False):
            # place stones to player's holes
            for hole in range(hole_num+1, self._holes_num):
                self._holes[player][hole] += 1
                last_moves.add_state(self, player, hole)
                self.amount_of_stones -= 1
                if not self.amount_of_stones:
                    if not skip_kalah and self._holes[player][hole]==1:
                        return MoveEndsInPlayersEmptyHole, hole
                    return MoveEnds, hole
            
            # place stones to player's kalah
            if not skip_kalah:
                self._kalahs[player] += 1
                last_moves.add_state(self, player, active_kalah=True)
                self.amount_of_stones -= 1
                if not self.amount_of_stones:
                    return MoveEndsInPlayersKalah, -1

            return MoveNotEnds, float('inf')
            
        if hole_num<0 or hole_num>=self._holes_num or player<0 or player>1:
            return WrongMove
        self.amount_of_stones = self._holes[player][hole_num]
        if not self.amount_of_stones:
            return WrongMove
        
        other_player = (player+1) % 2
        self._holes[player][hole_num] = 0
        last_moves.add_state(self, player, hole_num)
        while self.amount_of_stones:
            turn_result, last_hole = make_turn(player, hole_num)
            if turn_result==MoveEndsInPlayersKalah:
                self.last_moves = last_moves
                if self.is_finished(player):
                    self.last_move_result = MoveEnds
                else:
                    self.last_move_result = MoveEndsInPlayersKalah
                return self.last_move_result
            elif turn_result == MoveEndsInPlayersEmptyHole:
                if self._holes[other_player][opposite_hole(last_hole)] > 0:
                    self._holes[player][last_hole] = 0
                    self._kalahs[player] += 1
                    last_moves.add_state(self, player, last_hole, active_kalah=True)
                    kalah_add = self._holes[other_player][opposite_hole(last_hole)]
                    self._holes[other_player][opposite_hole(last_hole)] = 0
                    last_moves.add_state(self, other_player, opposite_hole(last_hole))
                    self._kalahs[player] += kalah_add
                    last_moves.add_state(self, player, active_kalah=True)
                self.last_moves = last_moves
                self.last_move_result = MoveEnds
                return self.last_move_result
            elif turn_result==MoveEnds:
                self.last_moves = last_moves
                self.last_move_result = MoveEnds
                return self.last_move_result
            
            turn_result, last_hole = make_turn(other_player, skip_kalah=True)
            hole_num = -1
            
        self.last_moves = last_moves
        self.last_move_result = MoveEnds
        return self.last_move_result
        
    def get_last_moves(self):
        """Returns a list of last move consequent steps"""
        return self.last_moves
    
    def is_finished(self, player):
        """
        Checks if the game is finished
        
        Args:
            player: current player number (0 or 1)
            
        Returns: 
            True/False is there game finished now (during player's turn, 
            i.e. when player has his/her turn but there are no any stones 
            on his/her board's side)
        """
        for hole in self._holes[player]:
            if hole:
                return False
        return True
        
    def end_game(self):
        """Ends the game and moves all onboard stones to corresponding 
        player kalah
        
        Returns:
            An array of result scores for each player
        """
        for player in [0,1]:
            for hole in range(self._holes_num):
                self._kalahs[player] += self._holes[player][hole]
                self._holes[player][hole] = 0
        return self._kalahs
        
    def to_string(self):
        """Copies the state to string and returns it"""
        return "(" + str(self._holes[0]) + ", " + str(self._kalahs[0]) + ") (" + str(self._holes[1]) + ", " + str(self._kalahs[1]) + ")"
        
    def __print__(self):
        """Prints the state in a text format"""
        print (self.to_string())
        
    def copy(self):
        """Returns a copy of the state"""
        last_moves, self.last_moves = self.last_moves, None
        state = deepcopy(self)
        self.last_moves = last_moves
        return state
        
    def is_temporary(self):
        """Not used"""
        return self._temporary
        
    def get_neighbors(self, player):
        """Returns a neighbor state of this state for the player's move
        
        This function makes only one move. This function does not take into
        account the possibilities of the extra moves
        
        Args:
            player: active player's number (0 or 1)
        """
        neighbors = []
        for hole in range(self._holes_num):
            if self._holes[player][hole]:
                new_state = self.copy()
                result = new_state.move(player, hole)
                if result == MoveEndsInPlayersKalah:
                    new_player = player
                else:
                    new_player = (player+1) % 2
                neighbors.append({'state':new_state, 'result':result, 'hole':[hole], 'player':new_player})
        return neighbors
        
    def get_all_neighbors(self, player):
        """Returns a neighbor state of this state for the player's move
        
        This function makes all possible moves including an extra moves.
        
        Args:
            player: active player's number (0 or 1)
            
        Returns:
            A list of possible moves and their results in format of list of 
            such dictionary:
            {'state':new_state, 'result':result, 'hole':[hole], 'player':new_player}
            Where:
                @new_state is a neighbor state
                @result is a result of the move that lead to this neighbot
                @hole is a number of hole from which we should pickup the 
                stones to make this particular move
                @new_player the number of a new player after that move
        """
        neighbors = self.get_neighbors(player)
        i = 0
        while i < len(neighbors):
            if neighbors[i]['result'] == MoveEndsInPlayersKalah:
                # new_extra = True
                new_state = neighbors.pop(i)
                new_neighbors = new_state['state'].get_neighbors(player)
                for new_new_state in new_neighbors:
                    new_new_state['hole'] = new_state['hole'] + new_new_state['hole']
                neighbors = neighbors + new_neighbors
            else:
                i += 1

#        map(lambda x: x['state'].__print__(), neighbors)
        return neighbors


if __name__ == "__main__":
    state = KalahState(0)
    state._kalahs = [6, 4]
    state._holes = [[0, 4, 8, 7, 2, 4], [0, 0, 0, 0, 0, 1]]
    n = state.get_neighbors(1)
    for x in n:
        print(x['hole'], x['state'].to_string(), x['player'])