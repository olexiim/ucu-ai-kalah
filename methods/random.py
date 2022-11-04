#!/usr/bin/env python
"""Dummy method for playing Kalah.

Contains class RandomMethod that just selects random hole among the possible
ones and proceed with it.

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

from methods.method import Method
from random import randint


class RandomMethod(Method):
    """Class contains logic of the random player.
    
    Attributes:
        Please refer to method.py for details
    """
    _name = "Random"
    _short_name = "Random"
    _disabled = False
    
    def make_move(self, state):
        """Makes a next move for the random player.
        
        Args:
            state: current state
            
        Returns:
            Player's hole number which defines a player's next move
        """
        super(RandomMethod, self).make_move(state)
        holes_num = state.holes_num()
        my_holes = state.player_holes(self._player)
        candidates = []
        for hole in range(holes_num):
            if my_holes[hole] > 0:
                candidates.append(hole)
        if candidates:
            hole = candidates[randint(0, len(candidates)-1)]
            return hole
        return -1
