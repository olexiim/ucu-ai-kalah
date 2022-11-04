#!/usr/bin/env python
"""Run script for Kalah Gameboard.

Kalah Gameboard is a software that implements an ancient board game called
Kalah or Mancala.

This is a main module for the Kalah Gameboard.

From Wikipedia (en.wikipedia.org/wiki/Kalah):
    
    The game requires a Kalah board and 36 - 72 seeds or stones. The board has 
    six small pits, called houses, on each side; and a big pit, called a Kalah 
    or store, at each end. 
    The object of the game is to capture more seeds than one's opponent.
    
    Rules.
    1. At the beginning of the game, three seeds are placed in each house.
    2. Each player controls the six houses and their seeds on his/her side of 
    the board. His/her score is the number of seeds in the store to his/her 
    right.
    3. Players take turns sowing their seeds. On a turn, the player removes 
    all seeds from one of the houses under his/her control. Moving 
    counter-clockwise, the player drops one seed in each house in turn, 
    including the player's own store but not his/her opponent's.
    4. If the last sown seed lands in the player's store, the player gets 
    an additional move. There is no limit on the number of moves a player can 
    make in his/her turn.
    5. If the last sown seed lands in an empty house owned by the player, and 
    the opposite house contains seeds, both the last seed and the opposite 
    seeds are captured and placed into the player's store.
    6. When one player no longer has any seeds in any of his/her houses, 
    the game ends. The other player moves all remaining seeds to his/her store, 
    and the player with the most seeds in his/her store wins.
    
    The game may vary with amount of initial seeds: 3, 4, 5, 6. The more seeds
    the more harder to play.


@author: Oleksii Molchanovskyi
@organization: Ukraine Catholic University
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

from main_window import Ui_kalah_window
from options_dialog import Ui_kalah_options

import methods.state as st

import sys
import inspect
import time
import os
from os.path import isfile, join
from importlib import import_module
from multiprocessing import Process, Pipe
from PyQt5 import QtCore, QtGui, QtWidgets

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class AsyncRunProcess(Process):
    """Class that implements methods running in a separate process"""
    def __init__(self, obj, state, conn):
        Process.__init__(self)
        self.obj = obj
        self.state = state.copy()
        self.conn = conn

    def run(self):
        result = self.obj.make_move(self.state)
        print(result)
        self.conn.send(("finish", result))


class AsyncRun(QtCore.QObject):
    """Class that runs method instance for a problem asynchronously"""
    success = QtCore.pyqtSignal([int])
    finished = QtCore.pyqtSignal()
    stop = False

    def __init__(self, obj, state):
        QtCore.QObject.__init__(self)
        self.obj = obj
        self.state = state

    def run(self):
        print("<{}> thinks...".format(self.obj.name()))
        start_time = time.time()
        parent_conn, child_conn = Pipe()
        self.process = AsyncRunProcess(self.obj, self.state, child_conn)
        self.process.start()
        while not self.stop and not parent_conn.poll():
            time.sleep(0.1)
        if self.stop:
            self.process.terminate()
            self.process.join()
        elif parent_conn.poll():
            msg, result = parent_conn.recv()
            print("Calculation finished in %.2f seconds" % (time.time() - start_time))
            self.process.join()
            self.success.emit(result)
        self.finished.emit()

    def stopWork(self):
        time.sleep(2)
        self.stop = True


class OptionsDlg(QtWidgets.QDialog):
    """Envelope-class for Kalah game options dialog"""

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_kalah_options()
        self.ui.setupUi(self)
        self.ui.timer_on.stateChanged.connect(self.timer_on_changed)
        self.ui.player_1.currentIndexChanged.connect(self.player_1_changed)
        self.ui.player_2.currentIndexChanged.connect(self.player_2_changed)
        
    def timer_on_changed(self, index):
        self.ui.time_per_move_label.setEnabled(index == QtCore.Qt.Checked)
        self.ui.time_per_move.setEnabled(index == QtCore.Qt.Checked)
        
    def player_1_changed(self, index):
        self.ui.ai_level_1.setEnabled(index>0)
        self.ui.ai_level_label_1.setEnabled(index>0)
        
    def player_2_changed(self, index):
        self.ui.ai_level_2.setEnabled(index>0)
        self.ui.ai_level_label_2.setEnabled(index>0)


class BoardScene(QtWidgets.QGraphicsScene):
    """Class that displays Kalah board"""
    state = None
    holes_num = 0
    holes = [[], []]
    kalahs = []
    width = 0
    height = 0
    redraw_geometry = True
    active_player = 0
    selected_hole = -1
    allow_mouse_events = True
    stone_pics = []
    
    hole_clicked = QtCore.pyqtSignal(int, int)
    
    stone_positions = [[0,0]], [[0,]]
    
    def __init__(self, state, width, height, parent=None):
        QtWidgets.QGraphicsScene.__init__(self, parent)
        self.state = state.copy()
        self.holes_num = state.holes_num()
        self.old_state = st.KalahState(0)
        self.kalahs = [{"item": None, "text": None, "rect": None, "items": [], 'item_coords': [], 'text_rect': None} for x in [0, 1]]
        self.holes = [[{"item": None, "text": None, 'rect': None, "items": [], "item_coords": [], 'text_rect': None} for x in range(self.holes_num)] for x in [0, 1]]
        self.redraw_geometry = True
        
        self.hole_selected_pen = QtGui.QPen(QtGui.QBrush(QtCore.Qt.blue), 3)
        self.hole_selected_brush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 96))
        self.hole_normal_pen = QtGui.QPen(QtCore.Qt.NoPen) # QtGui.QPen(QtCore.Qt.black)
        self.hole_normal_brush = QtGui.QBrush(QtCore.Qt.NoBrush) # QtGui.QBrush(QtCore.Qt.white)
        self.hole_active_pen =  QtGui.QPen(QtCore.Qt.NoPen) # QtGui.QPen(QtCore.Qt.black)
        self.hole_active_brush = QtGui.QBrush(QtGui.QColor(235, 233, 237, 127))
        
        self.kalah_normal_pen = QtGui.QPen(QtCore.Qt.NoPen) # QtGui.QPen(QtCore.Qt.black)
        self.kalah_normal_brush = QtGui.QBrush(QtCore.Qt.NoBrush) # QtGui.QBrush(QtCore.Qt.white)
        self.kalah_active_pen = QtGui.QPen(QtCore.Qt.NoPen) # QtGui.QPen(QtGui.QBrush(QtCore.Qt.red), 3)
        self.kalah_active_brush = QtGui.QBrush(QtCore.Qt.NoBrush) # QtGui.QBrush(QtGui.QColor(0,0,255,96))
        
        self._load_stone_pics()
        self.draw()
#        self.setSceneRect(0, 0, width, height)
        
    def _load_stone_pics(self):
        for i in range(1, 14):
            self.stone_pics.append(QtGui.QPixmap('images/stone-'+str(i)+'.png'))
        
    def set_state(self, state, redraw=False):
        self.old_state = self.state.copy()
        self.state = state.copy()
        if redraw:
            self.draw()
    
    def _draw_hole(self, player, hole, number, prev_number):
        rect = self.holes[player][hole]['rect']
        if self.holes[player][hole]['items']:
            item = self.holes[player][hole]['items'].pop()
            self.removeItem(item)
        if number == 0:
            return
        if number > len(self.stone_pics):
            i = len(self.stone_pics) - 1
        else:
            i = number - 1
        item = self.addPixmap(self.stone_pics[i])
        item.setOffset(rect.left(), rect.top())
        item.setData(0, player)
        item.setData(1, hole)
        item.setData(2, 0)
        self.holes[player][hole]['items'].append(item)
                
    def _draw_kalah(self, player, number, prev_number):
        if number==prev_number:
            return
        for i in range(prev_number):
            item = self.kalahs[player]['items'].pop()
            self.removeItem(item)
        if number==0:
            return
        rect = self.kalahs[player]['rect']
        y_num = int(rect.height() / (self.stone_pic.height() + 1))
        x_num = number/y_num + (number%y_num!=0 and 1 or 0)
        width = rect.width() / x_num
        for i in range(number):
            yi, xi = i % y_num, i / y_num
            y = yi*self.stone_pic.height() + (yi-1)
            x = width*xi + width/2 - self.stone_pic.width()/2
            item = self.addPixmap(self.stone_pic)
            item.setData(0, player)
            item.setData(1, -1)
            item.setData(2, 1)
            item.setOffset(rect.left() + x, rect.top() + y)
            self.kalahs[player]['items'].append(item)
                
    def _set_hole(self, player, hole, number=-1, prev_number=0):
        if number<0:
            number = self.state.player_holes(player)[hole]
        if not prev_number:
            prev_number = self.old_state.player_holes(player)[hole]
        self.holes[player][hole]['text'].setText(str(number))
        self.holes[player][hole]['text'].update()
        self._draw_hole(player, hole, number, prev_number)
        
    def _set_kalah(self, player, number=-1, prev_number=0):
        if number<0:
            number = self.state.player_kalah(player)
        if not prev_number:
            prev_number = self.old_state.player_kalah(player)
        self.kalahs[player]['text'].setText(str(number))
        self.kalahs[player]['text'].update()
        self._draw_kalah(player, number, prev_number)
    
    def draw(self):
        if self.redraw_geometry:
            self.board_pic = QtGui.QPixmap('images/board.png')
            self.stone_pic = QtGui.QPixmap('images/stone.png')
            self.addPixmap(self.board_pic)
            g = self.sceneRect()
            self.width, self.height = g.width(), g.height()
            block_width = block_height = 55
#            self.block_coords = [[[0,0] for x in range(self.holes_num)] for x in [0,1]]
            
            for player in [0,1]:
                y = player==0 and 134 or 54
                y_t = player==0 and 195 or 24
                for hole in range(self.holes_num):
                    if player==1:
                        hole_real_num = self.holes_num-hole-1
                    else:
                        hole_real_num = hole
                    hole_rect = QtCore.QRectF(79 + 65*hole, y, block_width, block_height)
                    hole_rect_1 = QtCore.QRectF(hole_rect.left()-2, hole_rect.top()-2, hole_rect.width()+4, hole_rect.height()+4)
                    self.holes[player][hole_real_num]['rect'] = hole_rect
                    text_rect = QtCore.QRectF(79 + 65*hole, y_t, 55, 24)
                    self.holes[player][hole_real_num]['text_rect'] = text_rect
                    hole = self.addEllipse(hole_rect_1, self.hole_normal_pen, self.hole_normal_brush)
                    hole.setAcceptHoverEvents(True)
                    hole.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
                    hole.setData(0, player)
                    hole.setData(1, hole_real_num)
                    hole.setData(2, 0)
                    self.holes[player][hole_real_num]['item'] = hole
                    hole_text = self.addSimpleText("0")
                    hole_text.setPen(QtGui.QPen(QtCore.Qt.white))
                    hole_text.setBrush(QtGui.QBrush(QtCore.Qt.white))
                    hole_text.setPos(self.holes[player][hole_real_num]['text_rect'].center().x()-hole_text.boundingRect().width()/2, self.holes[player][hole_real_num]['text_rect'].center().y()-hole_text.boundingRect().height()/2)
                    hole_text.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                    font = hole_text.font()
                    font.setPixelSize(int(text_rect.height()*0.6))
                    hole_text.setFont(font)
                    self.holes[player][hole_real_num]['text'] = hole_text
        
                if player==0:
                    kalah_rect = QtCore.QRectF(480, 66, 38, 110)
                    kalah_rect_1 = QtCore.QRectF(469, 54, 60, 138)
                    kalah_text_rect = QtCore.QRectF(465, 192, 55, 24)
                else:
                    kalah_rect = QtCore.QRectF(22, 66, 38, 110)
                    kalah_rect_1 = QtCore.QRectF(12, 54, 60, 138)
                    kalah_text_rect = QtCore.QRectF(10, 24, 55, 24)
                self.kalahs[player]['rect'] = kalah_rect
                self.kalahs[player]['text_rect'] = kalah_text_rect
                kalah = self.addRect(kalah_rect_1, self.kalah_normal_pen, self.kalah_normal_brush)
                kalah.setAcceptHoverEvents(False)
                kalah.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                kalah.setData(0, player)
                kalah.setData(1, -1)
                kalah.setData(2, 1)
                kalah_text = self.addSimpleText("0")
                kalah_text.setPen(QtGui.QPen(QtCore.Qt.white))
                kalah_text.setBrush(QtGui.QBrush(QtCore.Qt.white))
                kalah_text.setPos(kalah_text_rect.center().x()-kalah_text.boundingRect().width()/2, kalah_text_rect.center().y()-kalah_text.boundingRect().height()/2)
                kalah_text.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                font = kalah_text.font()
                font.setPixelSize(int(kalah_text_rect.height()*0.75))
                kalah_text.setFont(font)
                self.kalahs[player]['text'] = kalah_text
                
                self.redraw_geometry = False
                
        for player in [0,1]:
            for hole in range(self.holes_num):
                self._set_hole(player, hole)
            self._set_kalah(player)
    
    def change_hole_status(self, player, hole, selected=False, activated=False):
        if player<0 or player>1 or hole<0 or hole>=self.holes_num:
            return
        if not self.holes[player][hole] or not self.holes[player][hole]['item']:
            return
        hole = self.holes[player][hole]['item']
        if selected:
            hole.setPen(QtGui.QPen(self.hole_selected_pen))
            hole.setBrush(QtGui.QBrush(self.hole_selected_brush))
        elif activated:
            hole.setPen(QtGui.QPen(self.hole_active_pen))
            hole.setBrush(QtGui.QBrush(self.hole_active_brush))
        else:
            hole.setPen(QtGui.QPen(self.hole_normal_pen))
            hole.setBrush(QtGui.QBrush(self.hole_normal_brush))
        hole.update()
            
    def change_kalah_status(self, player, activated=False):
        if player<0 or player>1:
            return
        if not self.kalahs[player] or not  self.kalahs[player]['item']:
            return
        kalah =  self.kalahs[player]['item']
        if activated:
            kalah.setPen(self.kalah_active_pen)
            kalah.setBrush(self.kalah_active_brush)
        else:
            kalah.setPen(self.kalah_normal_pen)
            kalah.setBrush(self.kalah_normal_brush)
        kalah.update()
            
    def select_hole(self, player, hole):
        self.change_hole_status(player, hole, selected=True)
    
    def deselect_hole(self, player, hole):
        self.change_hole_status(player, hole)
        
    def activate_hole(self, player, hole):
        self.change_hole_status(player, hole, activated=True)
    
    def deactivate_hole(self, player, hole):
        self.change_hole_status(player, hole)
        
    def activate_kalah(self, player):
        self.change_kalah_status(player, activated=True)
    
    def deactivate_kalah(self, player):
        self.change_kalah_status(player)
        
    def set_active_player(self, player):
        self.active_player = player
    
    def mousePressEvent(self, event):
#        QtGui.QGraphicsScene.mousePressEvent(self, event)
        super(BoardScene, self).mousePressEvent(event)
        if self.allow_mouse_events and event.button()==QtCore.Qt.LeftButton:
#            item = self.mouseGrabberItem()
#             item = self.itemAt(event.scenePos())
            item = self.itemAt(event.scenePos(), QtGui.QTransform())
#            print item
            if item:
                player, hole, kalah = item.data(0), item.data(1), item.data(2)
                # if not player.isNull() and player.toInt()[0]==self.active_player:
                #     hole = hole.toInt()[0]
                #     player = player.toInt()[0]
                if not player is None and  player == self.active_player:
                    if hole>=0:
                        if self.selected_hole>=0:
                            self.deselect_hole(player, self.selected_hole)
                        self.select_hole(player, hole)
                        self.selected_hole = hole
#                        self.hole_clicked.emit(player, hole)
#                        self.emit(QtCore.SIGNAL("hole_clicked"), player, hole)
    
    def mouseReleaseEvent(self, event):
        super(BoardScene, self).mousePressEvent(event)
        if event.button()==QtCore.Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QtGui.QTransform() )
            if item:
                player, hole = item.data(0), item.data(1)
                # if not player.isNull() and player.toInt()[0]==self.active_player:
                if not player is None and player == self.active_player:
                    # hole = hole.toInt()[0]
                    # player = player.toInt()[0]
                    if hole>=0 and hole==self.selected_hole:
                        self.selected_hole = -1
                        self.deselect_hole(self.active_player, hole)
                        self.hole_clicked.emit(player, hole)
            if self.selected_hole>=0:
                self.deselect_hole(self.active_player, self.selected_hole)
                self.selected_hole = -1
                
    def block_mouse(self):
        self.allow_mouse_events = False
        
    def unblock_mouse(self):
        self.allow_mouse_events = True

class MainWindow(QtWidgets.QMainWindow):
    
    options = {"stones":5, "player_1":"human", "player_2":"human", 
               "ai_level_1":3, "ai_level_2":3, 
               "timer_on":False, "time_per_move":60, 
               "show_moves":False,
               "show_moves_time_interval":0.5}
    ai_methods = {}
    method_path = "methods"
    
    games_history = None
    moves = []
    active_player = 0
    ai_players = [False, False]
    ai_levels = [3, 3]
    
    current_state = None
    board_scene = None
    tasks = []
    
    ai_run_thread = None
    ai_run_object = None
    
    save_game_results = True
    
#    board_scene_holes = [[],[]]
#    board_kalahs = [None, None]
#    board_selected_hole = -1
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent, QtCore.Qt.WindowFlags(QtCore.Qt.Window + QtCore.Qt.MSWindowsFixedSizeDialogHint))
        self.ui = Ui_kalah_window()
        self.ui.setupUi(self)
        
        self.ui.newgame.clicked.connect(self.new_game)
        self.ui.stopgame.clicked.connect(self.stop_game)
        # self.ui.savegame.clicked.connect(self.save_game)
        # self.ui.loadgame.clicked.connect(self.load_game)
        self.ui.options.clicked.connect(self.popup_options_dialog)
        # self.ui.history.clicked.connect(self.show_history)
        self.ui.undo.clicked.connect(self.undo_move)
        self.ui.advice.clicked.connect(self.advice)
        
        self.main_timer = QtCore.QTimer(self)
        self.main_timer.timeout.connect(self.update_main_timer)
        self.game_timer = QtCore.QTimer(self)
        self.game_timer.timeout.connect(self.update_game_timer)
        
        self.ui.time_left.hide()
        self.ui.active_player.hide()
        self.ui.board.setUpdatesEnabled(True)
        
#        self.ai_players[0] = self.options["player_1"]!="human"
#        self.ai_players[1] = self.options["player_2"]!="human"
        self.load_player_methods()
        
        self.ui.advice.hide()
        self.ui.history.hide()
        self.ui.loadgame.hide()
        self.ui.savegame.hide()
        self.process_options()
        
    def load_player_methods(self):
        method_files = [ f for f in os.listdir(self.method_path) if isfile(join(self.method_path,f)) and f.endswith('.py') ]
        sys.path.append(join(sys.path[0], self.method_path))
        self.ai_methods = {}
        for method_file in method_files:
            module_name = 'methods.'+method_file.replace('.py','')
            import_module(module_name)
            for name, obj in inspect.getmembers(sys.modules[module_name]):
                if inspect.isclass(obj) and obj.__bases__ and obj.__bases__[0].__name__=="Method" and not obj._disabled:
                    self.ai_methods[obj.__name__] = {'file':method_file, 'class':obj, 'title':obj._name, 'short_title':obj._short_name, 'module':module_name}
        
    def popup_options_dialog(self):
        dialog = OptionsDlg(self)
        
        dialog.ui.stones.setValue(self.options["stones"])
        obj = {"player_1": dialog.ui.player_1, "player_2": dialog.ui.player_2}
        for key, o in obj.items():
            index = 0
            o.addItem("Human", "human")
            for player, data in self.ai_methods.items():
                o.addItem("AI. "+data["title"], QtCore.QVariant(player))
                if self.options[key]==player:
                    index = o.count()-1
            o.setCurrentIndex(index)
            
        dialog.ui.ai_level_1.setValue(self.options["ai_level_1"])
        dialog.ui.ai_level_1.setEnabled(dialog.ui.player_1.currentIndex()>0)
        dialog.ui.ai_level_label_1.setEnabled(dialog.ui.player_1.currentIndex()>0)
            
        dialog.ui.ai_level_2.setValue(self.options["ai_level_2"])
        dialog.ui.ai_level_2.setEnabled(dialog.ui.player_2.currentIndex()>0)
        dialog.ui.ai_level_label_2.setEnabled(dialog.ui.player_2.currentIndex()>0)
        
        dialog.ui.timer_on.setCheckState(self.options["timer_on"] and QtCore.Qt.Checked or QtCore.Qt.Unchecked)
        dialog.ui.time_per_move_label.setEnabled(self.options["timer_on"])
        dialog.ui.time_per_move.setEnabled(self.options["timer_on"])
        dialog.ui.time_per_move.setValue(self.options['time_per_move'])
        
        dialog.ui.show_moves.setCheckState(self.options["show_moves"] and QtCore.Qt.Checked or QtCore.Qt.Unchecked)
        
        if dialog.exec_():
            self.options["stones"] = dialog.ui.stones.value()
            # self.options["player_1"] = dialog.ui.player_1.itemData(dialog.ui.player_1.currentIndex()).toString().__str__()
            # self.options["player_2"] = dialog.ui.player_2.itemData(dialog.ui.player_2.currentIndex()).toString().__str__()
            self.options["player_1"] = dialog.ui.player_1.itemData(dialog.ui.player_1.currentIndex())
            self.options["player_2"] = dialog.ui.player_2.itemData(dialog.ui.player_2.currentIndex())
            self.options["ai_level_1"] = dialog.ui.ai_level_1.value()
            self.options["ai_level_2"] = dialog.ui.ai_level_2.value()
            self.options["timer_on"] = dialog.ui.timer_on.checkState()==QtCore.Qt.Checked
            self.options["time_per_move"] = dialog.ui.time_per_move.value()
            self.options["show_moves"] = dialog.ui.show_moves.checkState()==QtCore.Qt.Checked
            self.process_options()
            return True

        return False
        
    def process_options(self):
#        if self.options["timer_on"]:
#            self.display_timer()
#            self.ui.time_left.show()
#        else:
#            self.ui.time_left.hide()
        if self.options["player_1"].lower() == "human":
            self.ai_players[0] = False
        else:
            self.ai_players[0] = self.options["player_1"]
            self.ai_levels[0] = self.options["ai_level_1"]
        if self.options["player_2"].lower() == "human":
            self.ai_players[1] = False
        else:
            self.ai_players[1] = self.options["player_2"]
            self.ai_levels[1] = self.options["ai_level_2"]
    
    def new_game(self):
        self.active_player = 0
        self.is_animating = False
        self.move_result = st.MoveEnds
        self.current_state = st.KalahState(self.options["stones"])
        self.board_scene = None
        self.display_active_player()
        self.display_board()
        self.moves = []
        self.on_game = True
        self.ui.stopgame.setEnabled(True)
        if self.options["timer_on"]:
            self.ui.time_left.show()
            self.restart_game_timer()
            self.game_with_timer = True
        else:
            self.ui.time_left.hide()
            self.game_timer.stop()
            self.game_with_timer = False
        if self.ai_players[self.active_player]:
            self.board_scene.block_mouse()
            self.ai_moves()
        else:
            self.board_scene.unblock_mouse()
#        self.main_timer.start(100)
        
        
    def restart_game_timer(self):
        self.game_timer_value = self.options["time_per_move"]
        self.display_timer(self.game_timer_value)
        self.game_timer.start(1000)
    
    def load_game(self):
        pass
    
    def save_game(self):
        pass
    
    def show_history(self):
        pass
    
    def undo_move(self):
        if self.moves:
            move = self.moves.pop()
            self.active_player = move['player']
            self.board_scene.set_active_player(self.active_player)
            self.current_state = move['state']
            self.display_board()
            
            self.move_result = st.MoveEnds
            self.display_active_player()
            if self.ai_players[self.active_player]:
                self.board_scene.block_mouse()
                self.ai_moves()
            else:
                self.board_scene.unblock_mouse()
            self.restart_game_timer()

            if not self.moves:
                self.ui.undo.setEnabled(False)
    
    def advice(self):
        pass
    
    def end_game(self):
        if self.on_game:
#            self.main_timer.stop()
            self.game_timer.stop()
            self.on_game = False
            self.ui.time_left.hide()
            self.board_scene.hole_clicked.disconnect()
            score = self.current_state.end_game()
            if score[0]>score[1]:
                msg = "Game over. Player 1 wins!"
            elif score[0]<score[1]:
                msg = "Game over. Player 2 wins!"
            else:
                msg = "Game over. It's a draw!"
            msg += " Score %d:%d" % (score[0],score[1])
            self.ui.active_player.setText(msg)
            self.display_board()
            
            self.moves = []
            self.ui.undo.setEnabled(False)
            self.ui.stopgame.setEnabled(False)
            
    def end_game_on_time(self):
        if self.on_game:
            self.game_timer.stop()
            self.on_game = False
            self.ui.time_left.hide()
            self.board_scene.hole_clicked.disconnect()
            msg = "Time out. Player %d wins!" % (2-self.active_player)
            self.ui.active_player.setText(msg)
            
            self.moves = []
            self.ui.undo.setEnabled(False)
            self.ui.stopgame.setEnabled(False)
    
    def display_board(self, state=None):
        if not state:
            state = self.current_state
        if not self.board_scene:
            bg = self.ui.board.geometry()
            self.board_scene = BoardScene(state, bg.width(), bg.height())
            self.board_scene.set_active_player(self.active_player)
            self.board_scene.hole_clicked.connect(self.make_move)
            
            self.ui.board.setScene(self.board_scene)
            self.ui.board.fitInView(self.board_scene.sceneRect(), QtCore.Qt.IgnoreAspectRatio)
        else:
            self.board_scene.set_state(state, redraw=True)
        
    def display_active_player(self, player_num=None):
        if not player_num:
            player_num = self.active_player
        msg = "Player " + str(player_num+1) + " moves"
        if self.move_result == st.MoveEndsInPlayersKalah:
            msg += " once more"
        if self.ai_players[player_num]:
            msg += ". Wait..."
        self.ui.active_player.show()
        self.ui.active_player.setText(msg)
        
    def display_timer(self, time_left=0):
        self.ui.time_left.setText("Time left: %02d:%02d" % (time_left/60, time_left%60))
        
    def _change_player(self):
        self.active_player = (self.active_player + 1) % 2
        if self.board_scene:
            self.board_scene.set_active_player(self.active_player)
        return self.active_player
        
#    def make_move_slot(self, player, hole):
#        if hole<0 or hole>=self.current_state.holes_num() or player!=self.active_player:
#            return
#        self.tasks.append({'func':self.make_move, 'param':{'player':player,'hole':hole}})
                
    def make_move(self, player, hole):
        if hole<0 or hole>=self.current_state.holes_num() or player!=self.active_player:
            return
        time.sleep(0.1)
        
        if not self.ai_players[player]:
            self.moves.append({'state':self.current_state.copy(), 'player':self.active_player})
            self.ui.undo.setEnabled(True)
        
        self.move_result = self.current_state.move(player, hole)
        if self.move_result == st.WrongMove:
            QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Warning", "Wrong move. Try another!", QtWidgets.QMessageBox.Ok, self).exec_()
            return
            
        if self.options["show_moves"] and self.current_state.get_last_moves():
            self.animated_moves = self.current_state.get_last_moves().get_list()
            if self.animated_moves:

                def animate_move():
                    if self.prev_move:
                        if self.prev_move['hole']>=0:
                            self.board_scene.deactivate_hole(self.prev_move['player'], self.prev_move['hole'])
                        if self.prev_move['kalah']:
                            self.board_scene.deactivate_kalah(self.prev_move['player'])
                    if self.animated_moves:
                        move = self.animated_moves.pop(0)
                        if move['hole']>=0:
                            self.board_scene.activate_hole(move['player'], move['hole'])
                        if move['kalah']:
                            self.board_scene.activate_kalah(move['player'])
                        self.prev_move = move
        
                        self.display_board(move['state'])
#                        print move['state'].to_string()
                    else:
                        self.animated_timer.stop()
                        self.end_animation()
                        self.display_board()
                        self.move_finished()
                        
                self.prev_move = None
                self.animated_timer = QtCore.QTimer()
                self.animated_timer.timeout.connect(animate_move)
                self.animated_timer.start(int(self.options["show_moves_time_interval"]*1000))
                animate_move()
                self.begin_animation()

        if not self.is_animating:
            self.display_board()
            self.move_finished()
            
    def move_finished(self):
        if self.move_result != st.MoveEndsInPlayersKalah:
            self._change_player()
        if self.current_state.is_finished(self.active_player):
            self.end_game()
        else:
            self.display_active_player()
            if self.ai_players[self.active_player]:
                self.board_scene.block_mouse()
                self.ai_moves()
            else:
                self.board_scene.unblock_mouse()
            self.restart_game_timer()
        
    def update_main_timer(self):
        if self.tasks:
            task = self.tasks.pop(0)
            self.process_task(task)
            
    def update_game_timer(self):
        if self.is_animating:
            return
        self.game_timer_value -= 1
        self.display_timer(self.game_timer_value)
        if self.game_timer_value==0:
            self.end_game_on_time()
    
    def process_task(self, task):
        if task['func']:
            task['func'](task['param'])
            
    def begin_animation(self):
        self.is_animating = True
        self.ui.undo.setEnabled(False)
        if self.board_scene:
            self.board_scene.block_mouse()
            
    def end_animation(self):
        self.is_animating = False
        self.ui.undo.setEnabled(True)
        if self.board_scene:
            self.board_scene.unblock_mouse()
            
    def ai_moves(self):
        ai_player = self.ai_players[self.active_player]
        obj = self.ai_methods[ai_player]['class'](self.active_player, self.ai_levels[self.active_player])
        if self.game_with_timer:
            if self.options["time_per_move"]>10:
                obj.set_run_time_limit(self.options["time_per_move"]-2)
            else:
                obj.set_run_time_limit(self.options["time_per_move"])

        self.ai_run_object = AsyncRun(obj, self.current_state)
        self.ai_run_thread = QtCore.QThread()
        self.ai_run_thread.started.connect(self.ai_run_object.run, QtCore.Qt.DirectConnection)
        self.ai_run_thread.finished.connect(self.ai_run_object.deleteLater, QtCore.Qt.DirectConnection)
        self.ai_run_object.finished.connect(self.ai_run_object.deleteLater, QtCore.Qt.DirectConnection)
        self.ai_run_object.finished.connect(self.ai_run_object.stopWork, QtCore.Qt.DirectConnection)
        self.ai_run_object.finished.connect(self.ai_run_thread.quit, QtCore.Qt.DirectConnection)
        self.ai_run_object.success.connect(self.process_ai_move)
        self.ai_run_object.moveToThread(self.ai_run_thread)
        self.ai_run_thread.start()
        
    def process_ai_move(self, hole):
        if self.ai_run_thread:
            self.ai_run_thread.wait()
            del self.ai_run_thread
            self.ai_run_thread = None
        if self.ai_run_object:
            del self.ai_run_object
            self.ai_run_object = None
        
        if self.on_game:
            self.make_move(self.active_player, hole)
            
    def stop_game(self):
        self.on_game = False
        if self.ai_run_thread:
            self.ai_run_thread.wait()
            del self.ai_run_thread
            self.ai_run_thread = None
        if self.ai_run_object:
            del self.ai_run_object
            self.ai_run_object = None
            
        self.game_timer.stop()
        self.ui.time_left.hide()
        self.board_scene.hole_clicked.disconnect()
        msg = "Game stopped by user"
        self.ui.active_player.setText(msg)
        
        self.moves = []
        self.ui.undo.setEnabled(False)
        self.ui.stopgame.setEnabled(False)
        
if __name__ == "__main__":
    sys.path.append(join(sys.path[0], 'methods'))
    app = QtWidgets.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())
