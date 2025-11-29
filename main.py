import sys
import sqlite3
import random
import datetime
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsProxyWidget,
                            QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit,
                            QPushButton, QGroupBox, QFrame, QGraphicsView, QGraphicsLineItem)
from PyQt6.QtCore import Qt, QLineF
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QMessageBox

class GameLogic:
    def __init__(self, database):
        self.database = database
        self.logical_variables = ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'] #Наименования для логических выражений
        self.input = ['A', 'B', 'C']
        self.input_signals = [0, 0, 0]
        self.output = ['D', 'E', 'F']
        self.output_signals = [0, 0, 0]
        self.gate = ['AND', 'OR', 'NAND', 'NOR', 'XOR']
        self.difficulty = 1
        self.gate_chain = []
        self.gate_chain_outputs = {}
        self.correct_guesses = 0
        self.total_problems = 0
        self.current_game_id = None
        self.session_id = random.randint(100000, 999999)
        self.database.new_session(self.session_id)

    def initialize_all(self):
        self.gate_chain_outputs = {}
        for i in range(3):
            self.input_signals[i] = int(random.choice(['0', '1']))
        self.count_groups()
        self.generate_gate_chain()
        self.calculate_outputs()
        self.total_problems += 1
        self.current_game_id = int(time.time()) #генерируем id рандомно с помощью времени
        self.database.new_game(self.current_game_id, self.input_signals, self.output_signals)

    def count_groups(self):
        if self.difficulty == 1:
            self.count_first_group = random.randint(1, 3)
            self.count_second_group = 0
            self.count_third_group = 0
        elif self.difficulty == 2:
            self.count_first_group = 3
            self.count_second_group = random.randint(1, 3)
            self.count_third_group = 0
        elif self.difficulty == 3:
            self.count_first_group = 3
            self.count_second_group = 3
            self.count_third_group = random.randint(1, 3)
        return self.count_first_group, self.count_second_group, self.count_third_group

    def generate_gate_chain(self):
        self.gate_chain = []
        if self.difficulty == 1:
            self.generate_gate_chain_difficulty1()
        elif self.difficulty == 2:
            self.generate_gate_chain_difficulty2()
        elif self.difficulty == 3:
            self.generate_gate_chain_difficulty3()

    def generate_gate_chain_difficulty1(self):
        for i in range(self.count_first_group):
            input_1 = random.choice(['A', 'B', 'C'])
            input_2 = random.choice(['A', 'B', 'C'])
            self.gate_chain.append((self.logical_variables[i], random.choice(self.gate), input_1, input_2))
        if self.difficulty == 1:
            self.generate_outputs_for_gates(['D', 'E', 'F'], 0)

    def generate_gate_chain_difficulty2(self):
        self.generate_gate_chain_difficulty1()
        UNused_inputs = ['A', 'B', 'C']
        for i in self.gate_chain:
            UNused_inputs.append(i[0])
        for i in range(self.count_second_group):
            input_1 = random.choice(UNused_inputs) #рандомно выбираем input из возможных
            input_2 = random.choice(UNused_inputs)
            self.gate_chain.append((self.logical_variables[i + 3], random.choice(self.gate), input_1, input_2))
        if self.difficulty == 2:
            used_outputs = list(self.gate_chain_outputs.values())
            UNused_outputs = []
            for i in ['D', 'E', 'F']:
                if i not in used_outputs: #
                    UNused_outputs.append(i)
            self.generate_outputs_for_gates(UNused_outputs, 3)

    def generate_gate_chain_difficulty3(self):
        self.generate_gate_chain_difficulty2()
        UNused_inputs = ['A', 'B', 'C']
        for i in self.gate_chain:
            UNused_inputs.append(i[0])
        for i in range(self.count_third_group):
            input_1 = random.choice(UNused_inputs)
            input_2 = random.choice(UNused_inputs)
            self.gate_chain.append((self.logical_variables[i + 6], random.choice(self.gate), input_1, input_2))
        if self.difficulty == 3:
            used_outputs = list(self.gate_chain_outputs.values())
            UNused_outputs = []
            for i in ['D', 'E', 'F']:
                if i not in used_outputs:
                    UNused_outputs.append(i)
            self.generate_outputs_for_gates(UNused_outputs, 6)

    def generate_outputs_for_gates(self, available_outputs, start_index):
        gates_to_process = self.gate_chain[start_index:]
        for i, gate in enumerate(gates_to_process):
            if i < len(available_outputs):
                gate_id = gate[0]
                var = random.choice(available_outputs)
                if var not in self.gate_chain_outputs.values():
                    self.gate_chain_outputs[gate_id] = var

    def evaluate_gate(self, gate, input1,  input2):
        if gate == 'AND':
            return input1 and input2
        elif gate == 'OR':
            return input1 or input2
        elif gate == 'NAND':
            return not (input1 and input2)
        elif gate == 'NOR':
            return not (input1 or input2)
        elif gate == 'XOR':
            return input1 != input2
        return None

    def get_signal_value(self, signal_dict, signal_variable): #возвращает сигнал на логическом выражении
        if signal_variable in signal_dict:
            return signal_dict[signal_variable]
        return 0

    def calculate_outputs(self):
        signals = {
            'A': self.input_signals[0],
            'B': self.input_signals[1],
            'C': self.input_signals[2],
            'D': 0, 'E': 0, 'F': 0
        }
        for i in self.logical_variables:
            signals[i] = 0 #
        for gate in self.gate_chain:
            input1_val = self.get_signal_value(signals, gate[2])
            input2_val = self.get_signal_value(signals, gate[3])
            if self.evaluate_gate(gate[1], input1_val, input2_val):
                result = 1
            else:
                result = 0
            if result != signals[gate[0]]:
                signals[gate[0]] = result
        for gate, output in self.gate_chain_outputs.items(): #присваиваем выходным точкам сигналы с соответствующих логических выражений
            if output in ['D', 'E', 'F']:
                signals[output] = signals[gate]
        self.output_signals[0] = signals['D']
        self.output_signals[1] = signals['E']
        self.output_signals[2] = signals['F']
        return None

    def check_user_guess(self, user_guess): #проверка ответа пользователя
        if user_guess == self.output_signals:
            is_correct = True
            gate_str = ''
            self.database.end_game(self.current_game_id, user_guess, is_correct)
            for gate in self.gate_chain:
                gate_str += str(f'{gate[1]}-{gate[2]}-{gate[3]}')
            self.database.add_solved_chain(gate_str, self.input_signals, self.output_signals, self.difficulty,
            self.count_first_group, self.count_second_group, self.count_third_group)
            self.correct_guesses += 1
            if self.correct_guesses == 3:
                if self.difficulty < 3:
                    self.difficulty += 1
                else:
                    self.difficulty = 3
                self.correct_guesses = 0
                self.initialize_all()
            else:
                self.initialize_all()
        else:
            is_correct = False
            self.database.end_game(self.current_game_id, user_guess, is_correct)
            self.correct_guesses = 0
            self.initialize_all()


class Database:
    def __init__(self):
        self.db = "game_base.db" #создание базы данных
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()
        self.init_database()

    def init_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS session_achievements ( 
                            id INTEGER PRIMARY KEY,
                            start_time DATETIME,
                            end_time DATETIME,
                            correct_guesses INTEGER,
                            total_problems INTEGER,
                            difficulty INTEGER,
                            total_score INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS games (
                            id INTEGER PRIMARY KEY,
                            inputs TEXT,
                            game_output TEXT,
                            user_guess TEXT,
                            is_correct BOOLEAN,
                            time_taken INTEGER DEFAULT 0)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS solved_chains (
                            id INTEGER PRIMARY KEY,
                            gate TEXT,
                            inputs TEXT,
                            game_output TEXT,
                            time_taken INTEGER DEFAULT 0,
                            difficulty INTEGER DEFAULT 1,
                            count_first_group INTEGER,
                            count_second_group INTEGER,
                            count_third_group INTEGER)''')
        self.conn.commit()

    def new_session(self, session_id): #запускается приложение
        self.cursor.execute('''INSERT INTO session_achievements (id, start_time) VALUES (?, ?)''', (session_id, datetime.datetime.now()))
        self.conn.commit()

    def end_session(self, session_id, correct_guesses, total_problems, difficulty): #пользователь закрывает приложение
        end_time = datetime.datetime.now()
        self.cursor.execute('''UPDATE session_achievements SET end_time = ?, correct_guesses = ?, total_problems = ?, difficulty = ? WHERE id = ?''',
                            (end_time, correct_guesses, total_problems, difficulty, session_id))
        self.conn.commit()

    def new_game(self, game_id, inputs, game_output):#генерируется новая цепочка
        self.start_time = datetime.datetime.now()
        self.cursor.execute('''INSERT INTO games (id, inputs, game_output) 
        VALUES (?, ?, ?)''', (game_id, str(inputs), str(game_output)))
        self.conn.commit()

    def end_game(self, game_id, user_guess, is_correct): #программа переходит к новой цепочке и нужно сохранить старую
        time_taken = int((datetime.datetime.now() - self.start_time).total_seconds())
        if is_correct: #переводим булевое значение в числовое
            is_correct_int = 1
        else:
            is_correct_int = 0
        self.cursor.execute('''UPDATE games SET user_guess = ?, is_correct = ?, time_taken = ? WHERE id = ?''',
                            (str(user_guess), is_correct_int, time_taken, game_id))
        self.conn.commit()

    def add_solved_chain(self, gate, inputs, game_output, difficulty, count_first_group, count_second_group, count_third_group): #сохраняем данные правильно решённых цепей
        time_taken = int((datetime.datetime.now() - self.start_time).total_seconds())
        self.cursor.execute('''INSERT INTO solved_chains (gate, inputs, game_output, time_taken, difficulty, 
        count_first_group, count_second_group, count_third_group) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
(gate, str(inputs), str(game_output), time_taken, difficulty, count_first_group, count_second_group, count_third_group))
        self.conn.commit()

    def get_stats(self): #статистика игрока
        self.cursor.execute('''SELECT COUNT(*) FROM session_achievements''')
        number_sessions = self.cursor.fetchone()[0]
        self.cursor.execute('''SELECT COUNT(*) FROM games''')
        number_games = self.cursor.fetchone()[0]
        self.cursor.execute('''SELECT COUNT(*) FROM games WHERE is_correct = 1''')
        number_correct_answers = self.cursor.fetchone()[0] #Количество правильных ответов
        if number_games > 0:
            accuracy = (number_correct_answers / number_games * 100)
        else:
            return 0
        return {
            'total_sessions': number_sessions,
            'total_games': number_games,
            'correct_answers': number_correct_answers,
            'accuracy': accuracy
        }

class SignalCircle(QGraphicsProxyWidget): #создаём круг
        def __init__(self, x, y, signal_name, is_input=True):
            super().__init__()
            self.signal_name = signal_name
            self.is_input = is_input
            self.circle_widget = QWidget() #виджет круга
            self.circle_widget.setFixedSize(20, 20) #устанавливаем размер
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(self.circle_widget)
            label = QLabel(signal_name) #имя сигнала
            label.setAlignment(Qt.AlignmentFlag.AlignCenter) #выравнивание по центру
            layout.addWidget(label)
            self.setWidget(container)
            self.setPos(x, y) #устанавливаем позицию
            self.update_color(False)

        def update_color(self, is_active): #обновляем цвет
            if is_active:
                color = 'green'
            else:
                color = 'red'
            if not self.is_input:
                color = 'gray'
            self.circle_widget.setStyleSheet(
                f"background-color: {color}; border-radius: 10px; border: 1px solid black;")


class Wire(QGraphicsLineItem): #рисование проводов
    def __init__(self, start_x, start_y, end_x, end_y):
        line = QLineF(start_x, start_y, end_x, end_y)
        super().__init__(line)
        colours = [Qt.GlobalColor.black, Qt.GlobalColor.green, Qt.GlobalColor.blue, Qt.GlobalColor.red, Qt.GlobalColor.darkYellow, Qt.GlobalColor.red]
        random_colour = random.choice(colours)
        self.setPen(QPen(random_colour, 2))


class GateWidget(QGraphicsProxyWidget): #рисование логических выражений
    def __init__(self, gate_type, x, y):
        super().__init__()
        widget = QWidget()
        widget.setStyleSheet("background-color: white; border: 1px solid black;")
        layout = QVBoxLayout(widget)
        label = QLabel(gate_type)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(label)
        self.setWidget(widget)
        self.setPos(x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_game()

    # noinspection PyUnresolvedReferences
    def setup_ui(self): #графическая реализация программы
        self.setWindowTitle("Логикааа")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        info_group = QGroupBox("Информация") #группа с информацией
        info_layout = QHBoxLayout(info_group)
        self.difficulty_label = QLabel("Сложность: 1")
        self.correct_label = QLabel("Правильных ответов: 0/3")
        self.total_label = QLabel("Всего задач: 0")
        info_layout.addWidget(self.difficulty_label)
        info_layout.addWidget(self.correct_label)
        info_layout.addWidget(self.total_label)
        layout.addWidget(info_group)
        circuit_group = QGroupBox("Логическая цепь") #группа для показа цепи
        circuit_layout = QVBoxLayout(circuit_group)
        self.scene = QGraphicsScene() #сцена для элементов
        self.graphics_view = QGraphicsView(self.scene) #отображение сцены
        circuit_layout.addWidget(self.graphics_view)
        layout.addWidget(circuit_group)
        signals_group = QGroupBox("Сигналы")
        signals_layout = QHBoxLayout(signals_group)
        inputs_widget = QWidget() #входные сигналы (A, B, C)
        inputs_layout = QVBoxLayout(inputs_widget)
        inputs_layout.addWidget(QLabel("Входные сигналы:"))
        inputs_container = QWidget()
        inputs_container_layout = QHBoxLayout(inputs_container)
        self.input_frames = {}
        for i in ['A', 'B', 'C']:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            frame = QFrame() #круг что отображает состояние сигнала
            frame.setFixedSize(20, 20)
            frame.setStyleSheet("background-color: red; border-radius: 10px; border: 1px solid black;")
            label = QLabel(i)
            container_layout.addWidget(frame)
            container_layout.addWidget(label)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inputs_container_layout.addWidget(container)
            self.input_frames[i] = frame #сохраняем ссылку на элемент
        inputs_layout.addWidget(inputs_container)
        signals_layout.addWidget(inputs_widget)
        outputs_widget = QWidget() #выходные сигналы (D, E, F)
        outputs_layout = QVBoxLayout(outputs_widget)
        outputs_layout.addWidget(QLabel("Выходные сигналы:"))
        outputs_container = QWidget()
        outputs_container_layout = QHBoxLayout(outputs_container)
        self.output_frames = {}
        for i in ['D', 'E', 'F']: #аналогично с for i in ['A', 'B', 'C']
            container = QWidget()
            container_layout = QVBoxLayout(container)
            frame = QFrame()
            frame.setFixedSize(20, 20)
            frame.setStyleSheet("background-color: gray; border-radius: 10px; border: 1px solid black;")
            label = QLabel(i)
            container_layout.addWidget(frame)
            container_layout.addWidget(label)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outputs_container_layout.addWidget(container)
            self.output_frames[i] = frame
        outputs_layout.addWidget(outputs_container)
        signals_layout.addWidget(outputs_widget)
        layout.addWidget(signals_group)
        answer_group = QGroupBox("Ввод ответа") #группа для ввода ответа
        answer_layout = QHBoxLayout(answer_group)
        answer_layout.addWidget(QLabel("Выходы D E F:"))
        self.answer_input = QLineEdit() #поле для пользователя ввода ответа
        answer_layout.addWidget(self.answer_input)
        self.check_button = QPushButton("Проверить")
        self.check_button.clicked.connect(self.check_answer)
        answer_layout.addWidget(self.check_button)
        layout.addWidget(answer_group)
        self.stats_button = QPushButton("Статистика") #статистика из базы данных
        self.stats_button.clicked.connect(self.show_stats)
        answer_layout.addWidget(self.stats_button)
        layout.addWidget(answer_group)

    def show_stats(self): #показывает статистику
        stats = self.database.get_stats()
        text = f"""
        Статистика игрока:

        Всего сессий: {stats['total_sessions']}
        Всего решено задач: {stats['total_games']}
        Правильных ответов: {stats['correct_answers']}
        Точность: {stats['accuracy']:.1f}%
        """
        dialog = QMessageBox()
        dialog.setWindowTitle("Твоя статистика")
        dialog.setText(text)
        dialog.exec()

    def setup_game(self): #подключаем работу самой игры
        self.database = Database()
        self.game_logic = GameLogic(self.database)
        self.difficulty = 1
        self.correct_guesses = 0
        self.total_problems = 0
        self.new_circuit()

    def new_circuit(self): #новая цепочка
        self.game_logic.initialize_all()
        self.gate_chain = self.game_logic.gate_chain
        self.gate_outputs = self.game_logic.gate_chain_outputs
        self.input_signals = self.game_logic.input_signals
        self.output_signals = self.game_logic.output_signals
        self.draw_circuit()
        self.answer_input.clear()
        self.total_problems += 1
        self.update_ui()

    def draw_circuit(self): #рисуем саму цепочку
        self.scene.clear() #очищаем сцену перед новой цепью
        input_circles = {}
        for i, var in enumerate(['A', 'B', 'C']):
            circle = SignalCircle(50, 100 + i * 80, var, True) #такие числа взяты для красоты
            circle.update_color(bool(self.input_signals[i]))
            input_circles[var] = circle
            self.scene.addItem(circle)
            if self.input_signals[i]:
                color = "green"
            else:
                color = "red"
            self.input_frames[var].setStyleSheet(f"background-color: {color}; border-radius: 10px; border: 1px solid black;")
        output = {}
        for i, signal in enumerate(['D', 'E', 'F']):
            circle = SignalCircle(850, 100 + i * 80, signal, False) #такие числа взяты для красоты
            output[signal] = circle
            self.scene.addItem(circle)
        gate_positions = {}
        col_width = 250 #такие числа взяты для красоты
        start_x = 150 #такие числа взяты для красоты
        for i, gate in enumerate(self.gate_chain): #рассчитываем координаты логических выражений
            gate_id, gate_type, input1, input2 = gate
            col = i % 3
            row = i // 3
            x = start_x + col * col_width
            y = 80 + row * 100 #такие числа взяты для красоты
            gate_widget = GateWidget(gate_type, x, y)
            self.scene.addItem(gate_widget)
            gate_positions[gate_id] = (x + 40, y + 20) #такие числа взяты для красоты
        self.draw_wires(input_circles, gate_positions, output)

    def draw_wires(self, input_circles, gate_positions, output_circles): #рисуем провода
        for gate in self.gate_chain:
            gate_id, gate_type, input1, input2 = gate
            gate_x, gate_y = gate_positions[gate_id]
            for input_signal, y in [(input1, -5), (input2, 5)]: #определяем координаты выхода и входа проводов (по два провода на каждое выражение)
                if input_signal in input_circles: #если для логического выражения input это A, B или С
                    input_circle = input_circles[input_signal]
                    start_x = input_circle.x() + 25
                    start_y = input_circle.y() + 25
                    end_x = gate_x - 40
                    end_y = gate_y + y
                    wire = Wire(start_x, start_y, end_x, end_y)
                    self.scene.addItem(wire)
                elif input_signal in gate_positions: #если для логического выражения input это другое выражение
                    start_x, start_y = gate_positions[input_signal]
                    end_x = gate_x - 40
                    end_y = gate_y + y
                    wire = Wire(start_x, start_y, end_x, end_y)
                    self.scene.addItem(wire)
            if gate_id in self.gate_outputs: #если логическое выражение выводит своё значение в один из трёх outputs
                output_signal = self.gate_outputs[gate_id]
                output_circle = output_circles[output_signal]
                start_x = gate_x
                start_y = gate_y
                end_x = output_circle.x() + 10
                end_y = output_circle.y() + 25
                wire = Wire(start_x, start_y, end_x, end_y)
                self.scene.addItem(wire)

    def update_ui(self): #обновляем данные пользователя на экране
        self.difficulty_label.setText(f"Сложность: {self.game_logic.difficulty}")
        self.correct_label.setText(f"Правильных ответов: {self.game_logic.correct_guesses}/3")
        self.total_label.setText(f"Всего задач: {self.game_logic.total_problems}")

    def check_answer(self):
        answer_text = self.answer_input.text().strip()
        numbers = answer_text.split()
        if len(numbers) != 3: #если ввод не из 3 символов
            self.answer_input.clear()
            return
        user_guess = []
        value = True
        for num in numbers:
            if num == '0':
                user_guess.append(0)
            elif num == '1':
                user_guess.append(1)
            else:
                value = False
                break
        if not value: #если ввод не соответствует условиям
            self.answer_input.clear()
            return
        self.game_logic.check_user_guess(user_guess)
        self.update_ui()
        self.answer_input.clear()
        self.gate_chain = self.game_logic.gate_chain
        self.gate_outputs = self.game_logic.gate_chain_outputs
        self.input_signals = self.game_logic.input_signals
        self.output_signals = self.game_logic.output_signals
        self.draw_circuit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
