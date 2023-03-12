import os
from random import randrange
from random import choice

class FieldPart(object):
    main = 'map'
    radar = 'radar'
    weight = 'weight'

class Color:
    yellow2 = '\033[1;35m'
    reset = '\033[0m'
    blue = '\033[0;34m'
    yellow = '\033[1;93m'
    red = '\033[1;93m'
    miss = '\033[0;37m'


# функція, яка забарвлює текст у заданий колір.
def set_color(text, color):
    return color + text + Color.reset


# клас "клітинка". Тут ми задаємо візуальне відображення клітин та їх колір.
# по візуальному відображенні ми перевіряємо якогось типу клітина.
class Cell(object):
    empty_cell = set_color(' ', Color.yellow2)
    ship_cell = set_color('■', Color.blue)
    destroyed_ship = set_color('X', Color.yellow)
    damaged_ship = set_color('□', Color.red)
    miss_cell = set_color('•', Color.miss)


# поле гри складається з трьох частин: карта, де розставлені кораблі гравця,
# радар на якому гравець відзначає свої ходи та результати,
# поле з вагою клітин, використовується для ходів ШІ
class Field(object):

    def __init__(self, size):
        self.size = size
        self.map = [[Cell.empty_cell for _ in range(size)] for _ in range(size)]
        self.radar = [[Cell.empty_cell for _ in range(size)] for _ in range(size)]
        self.weight = [[1 for _ in range(size)] for _ in range(size)]

    def get_field_part(self, element):
        if element == FieldPart.main:
            return self.map
        if element == FieldPart.radar:
            return self.radar
        if element == FieldPart.weight:
            return self.weight

    # Малюємо поле
    def draw_field(self, element):

        field = self.get_field_part(element)
        weights = self.get_max_weight_cells()

        if element == FieldPart.weight:
            for x in range(self.size):
                for y in range(self.size):
                    if (x, y) in weights:
                        print('\033[1;32m', end='')
                    if field[x][y] < self.size:
                        print(" ", end='')
                    if field[x][y] == 0:
                        print(str("" + ". " + ""), end='')
                    else:
                        print(str("" + str(field[x][y]) + " "), end='')
                    print('\033[0;0m', end='')
                print()

        else:
            # Все, що було вище - малювання ваги для налагодження, його можна не використовувати в кінцевій грі.
            # Саме поле малюється лише ось так:
            for x in range(-1, self.size):
                for y in range(-1, self.size):
                    if x == -1 and y == -1:
                        print("  ", end="")
                        continue
                    if x == -1 and y >= 0:
                        print(y + 1, end=" ")
                        continue
                    if x >= 0 and y == -1:
                        print(Game.letters[x], end='')
                        continue
                    print(" " + str(field[x][y]), end='')
                print("")
        print("")

    # Функція перевіряє чи поміщається корабель на конкретну позицію конкретного поля.
    # будемо використовувати при розстановці кораблів, а також при обчисленні ваги клітин
    def check_ship_fits(self, ship, element):

        field = self.get_field_part(element)

        if ship.x + ship.height - 1 >= self.size or ship.x < 0 or \
                ship.y + ship.width - 1 >= self.size or ship.y < 0:
            return False

        x = ship.x
        y = ship.y
        width = ship.width
        height = ship.height

        for p_x in range(x, x + height):
            for p_y in range(y, y + width):
                if str(field[p_x][p_y]) == Cell.miss_cell:
                    return False

        for p_x in range(x - 1, x + height + 1):
            for p_y in range(y - 1, y + width + 1):
                if p_x < 0 or p_x >= len(field) or p_y < 0 or p_y >= len(field):
                    continue
                if str(field[p_x][p_y]) in (Cell.ship_cell, Cell.destroyed_ship):
                    return False

        return True

    # коли корабель знищений необхідно помітити всі клітини навколо нього зіграними (Cell.miss_cell)
    # а всі клітини корабля - знищеними (Cell.destroyed_ship)
    def mark_destroyed_ship(self, ship, element):

        field = self.get_field_part(element)

        x, y = ship.x, ship.y
        width, height = ship.width, ship.height

        for p_x in range(x - 1, x + height + 1):
            for p_y in range(y - 1, y + width + 1):
                if p_x < 0 or p_x >= len(field) or p_y < 0 or p_y >= len(field):
                    continue
                field[p_x][p_y] = Cell.miss_cell

        for p_x in range(x, x + height):
            for p_y in range(y, y + width):
                field[p_x][p_y] = Cell.destroyed_ship

    # додавання корабля: пробігаємося від позиції х у корабля за його висотою і шириною і помічаємо на полі ці клітини
    # параметр element - сюди ми передаємо до якої частини поля ми звертаємося
    def add_ship_to_field(self, ship, element):

        field = self.get_field_part(element)

        x, y = ship.x, ship.y
        width, height = ship.width, ship.height

        for p_x in range(x, x + height):
            for p_y in range(y, y + width):
                field[p_x][p_y] = ship

    # функція повертає список координат з найбільшим коефіцієнтом шансу попадання
    def get_max_weight_cells(self):
        weights = {}
        max_weight = 0
        for x in range(self.size):
            for y in range(self.size):
                if self.weight[x][y] > max_weight:
                    max_weight = self.weight[x][y]
                weights.setdefault(self.weight[x][y], []).append((x, y))

        return weights[max_weight]

    # перерахування ваги клітин
    def recalculate_weight_map(self, available_ships):
        self.weight = [[1 for _ in range(self.size)] for _ in range(self.size)]

        for x in range(self.size):
            for y in range(self.size):
                if self.radar[x][y] == Cell.damaged_ship:

                    self.weight[x][y] = 0

                    if x - 1 >= 0:
                        if y - 1 >= 0:
                            self.weight[x - 1][y - 1] = 0
                        self.weight[x - 1][y] *= 50
                        if y + 1 < self.size:
                            self.weight[x - 1][y + 1] = 0

                    if y - 1 >= 0:
                        self.weight[x][y - 1] *= 50
                    if y + 1 < self.size:
                        self.weight[x][y + 1] *= 50

                    if x + 1 < self.size:
                        if y - 1 >= 0:
                            self.weight[x + 1][y - 1] = 0
                        self.weight[x + 1][y] *= 50
                        if y + 1 < self.size:
                            self.weight[x + 1][y + 1] = 0

        # Перебираємо всі кораблі, що залишилися у противника.

        for ship_size in available_ships:

            ship = Ship(ship_size, 1, 1, 0)
            for x in range(self.size):
                for y in range(self.size):
                    if self.radar[x][y] in (Cell.destroyed_ship, Cell.damaged_ship, Cell.miss_cell) \
                            or self.weight[x][y] == 0:
                        self.weight[x][y] = 0
                        continue
                    for rotation in range(0, 4):
                        ship.set_position(x, y, rotation)
                        if self.check_ship_fits(ship, FieldPart.radar):
                            self.weight[x][y] += 1


class Game(object):
    letters = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")
    ships_rules = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4]
    field_size = len(letters)

    def __init__(self):

        self.players = []
        self.current_player = None
        self.next_player = None

        self.status = 'prepare'

    # при старті гри призначаємо поточного та наступного гравця
    def start_game(self):

        self.current_player = self.players[0]
        self.next_player = self.players[1]

    # функція перемикання статусів
    def status_check(self):
        if self.status == 'prepare' and len(self.players) >= 2:
            self.status = 'in game'
            self.start_game()
            return True

        if self.status == 'in game' and len(self.next_player.ships) == 0:
            self.status = 'game over'
            return True

    def add_player(self, player):
        player.field = Field(Game.field_size)
        player.enemy_ships = list(Game.ships_rules)

        self.ships_setup(player)

        player.field.recalculate_weight_map(player.enemy_ships)
        self.players.append(player)

    def ships_setup(self, player):
        # робимо розстановку кораблів за правилами, заданими в класі Game
        for ship_size in Game.ships_rules:
             # задаємо кількість спроб при виставленні кораблів випадковим чином
            retry_count = 30

            ship = Ship(ship_size, 0, 0, 0)

            while True:

                Game.clear_screen()
                if player.auto_ship_setup is not True:
                    player.field.draw_field(FieldPart.main)
                    player.message.append('Куди поставити {} корабель: '.format(ship_size))
                    for _ in player.message:
                        print(_)
                else:
                    print('{}. Розтавляємо кораблі...'.format(player.name))

                player.message.clear()

                x, y, r = player.get_input('ship_setup')
                # якщо користувач ввів щось некоректне функція поверне нулі, значить  робимо continue
                # просто просимо ще раз ввести координати
                if x + y + r == 0:
                    continue

                ship.set_position(x, y, r)

                # якщо корабель поміщається на заданій позиції - додаємо гравцю на поле корабель
                # також додаємо корабель до списку кораблів гравця і переходимо до наступного корабля для розміщення
                if player.field.check_ship_fits(ship, FieldPart.main):
                    player.field.add_ship_to_field(ship, FieldPart.main)
                    player.ships.append(ship)
                    break

                # сюди ми добираємось тільки якщо корабель не помістився. пишемо користувачеві, що позиція неправильна
                # і віднімаємо спробу на розміщення
                player.message.append('Неправильна позиція!')
                retry_count -= 1
                if retry_count < 0:
                    # після заданої кількості невдалих спроб - обнуляємо карту гравця
                    # прибираємо у нього всі кораблі і починаємо розстановку по новій
                    player.field.map = [[Cell.empty_cell for _ in range(Game.field_size)] for _ in
                                        range(Game.field_size)]
                    player.ships = []
                    self.ships_setup(player)
                    return True

    def draw(self):
        if not self.current_player.is_ai:
            self.current_player.field.draw_field(FieldPart.main)
            self.current_player.field.draw_field(FieldPart.radar)
        for line in self.current_player.message:
            print(line)

   # гравці змінюються ось та:
    def switch_players(self):
        self.current_player, self.next_player = self.next_player, self.current_player

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')


class Player(object):

    def __init__(self, name, is_ai, skill, auto_ship):
        self.name = name
        self.is_ai = is_ai
        self.auto_ship_setup = auto_ship
        self.skill = skill
        self.message = []
        self.ships = []
        self.enemy_ships = []
        self.field = None

    # Хід гравця. Це або розміщення кораблів (input_type == "ship_setup")
    # Або здійснення пострілу (input_type == "shot")
    def get_input(self, input_type):

        if input_type == "ship_setup":

            if self.is_ai or self.auto_ship_setup:
                user_input = str(choice(Game.letters)) + str(randrange(0, self.field.size)) + choice(["H", "V"])
            else:
                user_input = input().upper().replace(" ", "")

            if len(user_input) < 3:
                return 0, 0, 0

            x, y, r = user_input[0], user_input[1:-1], user_input[-1]

            if x not in Game.letters or not y.isdigit() or int(y) not in range(1, Game.field_size + 1) or \
                    r not in ("H", "V"):
                self.message.append('Команда незрозуміла, помилка формату данних')
                return 0, 0, 0

            return Game.letters.index(x), int(y) - 1, 0 if r == 'H' else 1

        if input_type == "shot":

            if self.is_ai:
                if self.skill == 1:
                    x, y = choice(self.field.get_max_weight_cells())
                if self.skill == 0:
                    x, y = randrange(0, self.field.size), randrange(0, self.field.size)
            else:
                user_input = input().upper().replace(" ", "")
                x, y = user_input[0].upper(), user_input[1:]
                if x not in Game.letters or not y.isdigit() or int(y) not in range(1, Game.field_size + 1):
                    self.message.append('Команда незрозуміла, помилка формату данних')
                    return 500, 0
                x = Game.letters.index(x)
                y = int(y) - 1
            return x, y

   # при здійсненні пострілу ми будемо вимагати введення даних з типом shot
    def make_shot(self, target_player):

        sx, sy = self.get_input('shot')

        if sx + sy == 500 or self.field.radar[sx][sy] != Cell.empty_cell:
            return 'retry'
        # результат пострілу це те, що цільовий гравець відповість на наш хід
        # промазав, потрапив чи вбив (у разі вбив повертається корабель)
        shot_res = target_player.receive_shot((sx, sy))

        if shot_res == 'miss':
            self.field.radar[sx][sy] = Cell.miss_cell

        if shot_res == 'get':
            self.field.radar[sx][sy] = Cell.damaged_ship

        if type(shot_res) == Ship:
            destroyed_ship = shot_res
            self.field.mark_destroyed_ship(destroyed_ship, FieldPart.radar)
            self.enemy_ships.remove(destroyed_ship.size)
            shot_res = 'kill'

        self.field.recalculate_weight_map(self.enemy_ships)

        return shot_res

    # тут гравець буде приймати постріл
    def receive_shot(self, shot):

        sx, sy = shot

        if type(self.field.map[sx][sy]) == Ship:
            ship = self.field.map[sx][sy]
            ship.hp -= 1

            if ship.hp <= 0:
                self.field.mark_destroyed_ship(ship, FieldPart.main)
                self.ships.remove(ship)
                return ship

            self.field.map[sx][sy] = Cell.damaged_ship
            return 'get'

        else:
            self.field.map[sx][sy] = Cell.miss_cell
            return 'miss'


class Ship:

    def __init__(self, size, x, y, rotation):

        self.size = size
        self.hp = size
        self.x = x
        self.y = y
        self.rotation = rotation
        self.set_rotation(rotation)

    def __str__(self):
        return Cell.ship_cell

    def set_position(self, x, y, r):
        self.x = x
        self.y = y
        self.set_rotation(r)

    def set_rotation(self, r):

        self.rotation = r

        if self.rotation == 0:
            self.width = self.size
            self.height = 1
        elif self.rotation == 1:
            self.width = 1
            self.height = self.size
        elif self.rotation == 2:
            self.y = self.y - self.size + 1
            self.width = self.size
            self.height = 1
        elif self.rotation == 3:
            self.x = self.x - self.size + 1
            self.width = 1
            self.height = self.size


if __name__ == '__main__':

    # тут робимо список із двох гравців та задаємо їм основні параметри
    players = []
    players.append(Player(name='Username', is_ai=False, auto_ship=True, skill=1))
    players.append(Player(name='IQ180', is_ai=True, auto_ship=True, skill=1))

    # створюємо саму гру
    game = Game()

    while True:
        # ккожен початок ходу перевіряємо статус і далі вже діємо виходячи зі статусу гри
        game.status_check()

        if game.status == 'prepare':
            game.add_player(players.pop(0))

        if game.status == 'in game':
            # в основній частині гри ми очищаємо екран, додаємо повідомлення для поточного гравця і малюємо гру
            Game.clear_screen()
            game.current_player.message.append("Чекаємо команду: ")
            game.draw()
            # Очищаємо список повідомлень для гравця. Наступного ходу він уже отримає новий список повідомлень
            game.current_player.message.clear()
            # жчекаємо результату пострілу на основі пострілу поточного гравця в наступного
            shot_result = game.current_player.make_shot(game.next_player)
            # в залежності від результату накидаємо повідомлень і поточному гравцю та наступному
            # ну і якщо схибив - передаємо хід наступному гравцю.
            if shot_result == 'miss':
                game.next_player.message.append('На цей раз {}, схибив! '.format(game.current_player.name))
                game.next_player.message.append('Ваш хід {}!'.format(game.next_player.name))
                game.switch_players()
                continue
            elif shot_result == 'retry':
                game.current_player.message.append('Спробуйте ще раз!')
                continue
            elif shot_result == 'get':
                game.current_player.message.append('Хороший постріл, продовжуйте!')
                game.next_player.message.append('Наш корабель потрапив під обстріл!')
                continue
            elif shot_result == 'kill':
                game.current_player.message.append('Корабель супротивника знищений!')
                game.next_player.message.append('Погані новини, наш корабель був знищений :(')
                continue

        if game.status == 'game over':
            Game.clear_screen()
            game.next_player.field.draw_field(FieldPart.main)
            game.current_player.field.draw_field(FieldPart.main)
            print('Це був останній корабель {}'.format(game.next_player.name))
            print('{} виграв матч! Вітання!'.format(game.current_player.name))
            break

    print('Дякую за гру!')
    input('')

