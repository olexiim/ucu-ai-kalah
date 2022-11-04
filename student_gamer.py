#!/usr/bin/env python

import methods.state as st

import sys
import inspect
import time
import os
from os.path import isfile, join
from importlib import import_module
from multiprocessing import Process, Pipe
from PyQt5 import QtCore, QtGui, QtWidgets


class AsyncRunProcess(Process):
    """Class that implements methods running in a separate process"""

    def __init__(self, obj, state, conn):
        Process.__init__(self)
        self.obj = obj
        self.state = state.copy()
        self.conn = conn

    def run(self):
        result = self.obj.make_move(self.state)
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
            time.sleep(1)
        self.finished.emit()

    def stopWork(self):
        time.sleep(2)
        self.stop = True


# class KalahGamer(QtGui.QMainWindow):
class KalahGamer:
    methods = {}
    players = [None, None]
    active_player = 0
    number_of_stones = 5
    turn_time_limit = 15
    history = []
    method_path = "methods"

    def __init__(self, result_file='results.txt', turn_time_limit=30, number_of_stones=5):
        #        QtGui.QWidget.__init__(self, None)
        self.game_timer = QtCore.QTimer()
        self.game_timer.timeout.connect(self.update_game_timer)
        self.total_timer = QtCore.QElapsedTimer()
        if not self.load_player_methods(self.method_path, self.methods):
            print("Error: no methods found in ()".format(self.method_path))
        else:
            print("Found and loaded {} methods: {}".format(len(self.methods),
                                                           ", ".join(map(lambda f: f['short_title'],
                                                                            self.methods.values()))))
        # if not self.load_student_methods():
        #     print("Error: no student methods found in ()".format(self.student_method_path))
        # else:
        #     print("Found and loaded {} student methods: {}".format(len(self.student_methods),
        #                                                            ", ".join(map(lambda f: f['short_title'],
        #                                                                          self.student_methods.values()))))
        self.history = []
        self.result_file = result_file
        self.turn_time_limit = turn_time_limit
        self.number_of_stones = number_of_stones

    def switch_player(self):
        self.active_player = (self.active_player + 1) % 2
        return self.active_player

    def load_player_methods(self, method_path, method_dict):
        method_files = [f for f in os.listdir(method_path) if
                        isfile(join(method_path, f)) and f.endswith('.py')]
        sys.path.append(join(sys.path[0], method_path))
        counter = 0
        for method_file in method_files:
            module_name = method_path + '.' + method_file.replace('.py', '')
            import_module(module_name)
            for name, obj in inspect.getmembers(sys.modules[module_name]):
                if inspect.isclass(obj) and obj.__bases__ and \
                        "Method" in list(map(lambda x: x.__name__, obj.__mro__)) and not obj._disabled:
                    method_dict[obj.__name__] = {'file': method_file, 'class': obj, 'title': obj._name,
                                                 'short_title': obj._short_name, 'module': module_name}
                    counter += 1
        return counter

    # def load_ai_methods(self):
    #     return self.load_player_methods(self.method_path, self.ai_methods)
    #
    # def load_student_methods(self):
    #     return self.load_player_methods(self.student_method_path, self.student_methods)

    def get_players(self):
        result = []
        for player in self.methods.values():
            result.append(player['short_title'])
        return result

    def play_game(self, player1_title, player2_title, history_file):

        player1_id, player2_id = 0, 1
        self.players_title = [player1_title, player2_title]
        self.history_file = history_file

        for player in self.methods.values():
            if player['short_title'] == player1_title:
                self.players[player1_id] = player['class']
            if player['short_title'] == player2_title:
                self.players[player2_id] = player['class']

        if not self.players[0] or not self.players[1]:
            print("Player's class not found", player1_title, ":", self.players[player1_id],
                  player2_title, ":", self.players[player2_id])
            return False

        print("Starting new game: {} vs. {}".format(player1_title, player2_title))

        self.active_player = 0
        self.move_result = st.MoveEnds
        self.current_state = st.KalahState(self.number_of_stones)
        self.initial_state = self.current_state.copy()
        self.on_game = True
        self.restart_game_timer()
        self.history = []
        self.total_timer.start()

        print("Initial state:\n", self.current_state.to_string())

        self.ai_moves()
        return True

    def ai_moves(self, ai_class=None, player_num=-1):
        if player_num < 0:
            player_num = self.active_player
        if not ai_class:
            ai_class = self.players[player_num]
        obj = ai_class(player_num)
        obj.set_run_time_limit(self.turn_time_limit)

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
        print("Make AI move", self.active_player, hole)
        self.ai_run_thread.wait()
        del self.ai_run_thread
        self.ai_run_thread = None
        del self.ai_run_object
        self.ai_run_object = None

        if self.on_game:
            self.make_move(self.active_player, hole)

    def end_game(self):
        if self.on_game:
            self.game_timer.stop()
            score = self.current_state.end_game()
            if score[0] > score[1]:
                self.game_winner = 1
                msg = "Game over. Player 1 wins!"
            elif score[0] < score[1]:
                self.game_winner = 2
                msg = "Game over. Player 2 wins!"
            else:
                self.game_winner = 0
                msg = "Game over. It's a draw!"
            msg += " Score %d:%d" % (score[0], score[1])
            self.game_result = {'message': msg, 'score_text': "%d:%d" % (score[0], score[1]),
                                'score': (score[0], score[1]), 'winner': self.game_winner,
                                'reason': 'normal', 'total_time': self.total_timer.elapsed() / 1000}
            self.on_game = False

            self.save_results()
            self.process_next_game()

    def end_game_on_time(self):
        if self.on_game:
            self.game_timer.stop()
            self.game_winner = 2 - self.active_player
            self.game_result_score = "Time out"
            msg = "Time out. Player %d wins!" % (2 - self.active_player)
            self.game_result = {'message': msg, 'score_text': "?:?",
                                'score': (-1, -1), 'winner': self.game_winner,
                                'reason': 'timeout', 'total_time': self.total_timer.elapsed() / 1000}
            self.on_game = False

            self.save_results()
            self.process_next_game()

    def make_move(self, player, hole):
        if hole < 0 or hole >= self.current_state.holes_num() or player != self.active_player:
            return

        self.move_result = self.current_state.move(player, hole)
        print("Current state:", self.current_state.to_string())
        if self.move_result == st.WrongMove:
            print("Wrong move!")
            return

        self.history.append(
            {'player': player, 'hole': hole, 'result': self.move_result, 'state': self.current_state.copy()})

        if self.move_result != st.MoveEndsInPlayersKalah:
            self.switch_player()
        if self.current_state.is_finished(self.active_player):
            self.end_game()
        else:
            self.ai_moves()
            self.restart_game_timer()

    def update_game_timer(self):
        self.game_timer_value -= 1
        if self.game_timer_value == 0:
            self.end_game_on_time()

    def restart_game_timer(self):
        self.game_timer_value = self.turn_time_limit * 1.1
        self.game_timer.start(1000)

    def save_results(self):
        secs = self.game_result['total_time']
        mins, secs = secs / 60, secs % 60
        hrs, mins = mins / 60, mins % 60

        with open(self.history_file + '-{}.txt'.format(time.strftime('%d.%m.%Y %H:%M')), 'w') as f:
            f.write("# Player 1: %s\n" % (self.players_title[0],))
            f.write("# Player 2: %s\n" % (self.players_title[1],))
            f.write("# Score: %s\n" % (self.game_result['score_text'],))

            f.write("# Total time: %02d:%02d:%02d\n" % (hrs, mins, secs))

            f.write("# " + self.game_result['message'] + "\n")
            f.write("# Game protocol\n")
            f.write("- - %s\n" % (self.initial_state.to_string()))
            for record in self.history:
                f.write("%d %d %s\n" % (record['player'], record['hole'], record['state'].to_string()))
            # map(lambda x: f.write("%d %d %s\n" % (x['player'], x['hole'], x['state'].to_string())), self.history)

        with open(self.result_file, 'a') as f:
            f.write("{} | {} | {} vs. {} | {}".format(
                time.strftime('%d.%m.%Y %H:%M'),
                "%02d:%02d:%02d" % (hrs, mins, secs),
                self.players_title[0], self.players_title[1], self.game_winner))
            if self.game_result['reason'] == 'timeout':
                f.write(" Timeout\n")
            else:
                f.write(" %s\n" % (self.game_result['score_text']))

        print(self.game_result['message'])
        print("Game finished!")

    def run_games(self, games):
        self.games = games
        self.process_next_game()

    def process_next_game(self):
        if self.games:
            game = self.games.pop(0)
            self.play_game(game['player_1'], game['player_2'], game['history_file'])
        else:
            app.exit()


def run_single_game(player_1, player_2, players_path='methods',
                    logs_path='game_logs', rolling_game=False,
                    turn_time_limit=30):
    sys.path.append(join(sys.path[0], players_path))
    gamer = KalahGamer(result_file=logs_path + os.sep + 'results.txt', turn_time_limit=turn_time_limit)
    players = gamer.get_players()

    if player_1 not in players:
        print(f"{player_1} is not found at {players_path} dir")
        return

    if player_2 not in players:
        print(f"{player_2} is not found at {players_path} dir")
        return

    games = []
    history_file = logs_path + os.sep + player_1.replace(' ', '') + '_' + player_2.replace(' ', '')
    games.append({'player_1': player_1, 'player_2': player_2, 'history_file': history_file})

    if rolling_game:
        history_file = logs_path + os.sep + player_2.replace(' ', '') + '_' + player_1.replace(' ', '')
        games.append({'player1': player_2, 'player2': player_1, 'history_file': history_file})

    print(f"Starting a game: {player_1} vs. {player_2}")

    global app
    app = QtWidgets.QApplication(sys.argv)
    gamer.run_games(games)
    app.exec_()


def run_tournament_one_to_many(player_one="", evaluation_methods=[],
                               player_path='methods', logs_path='game_logs',
                               turn_time_limit=30):
    sys.path.append(join(sys.path[0], player_path))
    gamer = KalahGamer(result_file=logs_path + os.sep + 'results.txt', turn_time_limit=turn_time_limit)
    players = gamer.get_players()

    if player_one not in players:
        print(f"{player_one} is not found at {player_path} dir")
        return

    games = []
    for ai_player in evaluation_methods:
        history_file = logs_path + os.sep + player_one.replace(' ', '') + '_' + ai_player.replace(' ', '')
        games.append({'player_1': player_one, 'player_2': ai_player, 'history_file': history_file})

        history_file = logs_path + os.sep + ai_player.replace(' ', '') + '_' + player_one.replace(' ', '')
        games.append({'player_1': ai_player, 'player_2': player_one, 'history_file': history_file})

    if not games:
        print(f"No suitable oponents in {player_path} found. Check the existed records.")
        return

    print("Starting tournament: {} vs. {}".format(player_one, ", ".join(evaluation_methods)))

    global app
    app = QtWidgets.QApplication(sys.argv)
    gamer.run_games(games)
    app.exec_()


if __name__ == "__main__":
    app = None

    # Run tournament one player vs. many players
    # You can add other players in evaluation_methods argument
    # run_tournament_one_to_many(player_one="Random",
    #                            evaluation_methods=['Random'],
    #                            turn_time_limit=10)

    # Run a single game between two players
    run_single_game("Random", "Random", rolling_game=False, turn_time_limit=10)
