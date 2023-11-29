from __future__ import division
from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from heapq import heappush, heappop
import numpy as np


class Cell(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Box(Agent):
    def __init__(self, unique_id, model, robot):
        super().__init__(unique_id, model)
        self.peso = np.random.randint(0, 10)
        self.robot = robot


class Shelf(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.limit = 1
        self.stored_box = None


class ConveyorBelt(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_empty = True
        self.box = None
        self.move = 0

    def find_nearest_robot(self, position):
        distancias = []
        for cell in self.model.grid.coord_iter():
            cell_content, pos = cell
            x, y = pos
            for obj in cell_content:
                if isinstance(obj, Robot):
                    distancias.append([abs(position[0] - x) + abs(position[1] - y), pos])

        distancias.sort(key=lambda x: x[0])

        while True:
            if len(distancias) == 0:
                return None

            robot = \
            [robot for robot in self.model.grid.get_cell_list_contents(distancias[0][1]) if isinstance(robot, Robot)][0]

            if robot.battery > 25 and robot.destination is None:
                celdas = self.model.grid.get_cell_list_contents(position)
                robot.destination = [celda for celda in celdas if isinstance(celda, Cell)][0]

                return robot

            distancias.pop(0)

    def step(self):
        if self.is_empty:
            if self.random.random() < self.model.box_percentage:
                if self.pos == (12, 6):
                    self.box = Box(self.model.box_id, self.model, self.find_nearest_robot((11, 6)))
                    self.model.grid.place_agent(self.box, (self.pos[0] + 1, 12))
                else:
                    self.box = Box(self.model.box_id, self.model, self.find_nearest_robot((11, 10)))
                    self.model.grid.place_agent(self.box, (self.pos[0] + 1, 12))

                self.is_empty = False
                self.model.box_id += 1
                self.move = 7
        elif self.move == 1:
            if self.pos == (12, 6):
                self.model.grid.move_agent(self.box, (self.box.pos[0] - 1, self.box.pos[1]))
            else:
                self.model.grid.move_agent(self.box, (self.box.pos[0] + 1, self.box.pos[1]))
            self.move -= 1
        elif self.move != 0:
            if self.pos == (12, 6):
                self.model.grid.move_agent(self.box, (self.box.pos[0], self.box.pos[1] - 1))
            else:
                self.model.grid.move_agent(self.box, (self.box.pos[0], self.box.pos[1] + 1))
            self.move -= 1

        if not self.is_empty and self.box.robot is None:
            if self.pos == (12, 6):
                self.box.robot = self.find_nearest_robot((11, 6))
            else:
                self.box.robot = self.find_nearest_robot((11, 10))


class Charger(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_occupied = False


class Robot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.next_pos = None
        self.destination = None
        self.route = []
        self.idx_rute = 0
        self.battery = 50
        self.box = None
        self.moves = 0
        self.waiting = False

    def available_cells(self, position):
        return [neighbour for neighbour in self.model.grid.get_neighbors(position, moore=True, include_center=False) if
                isinstance(neighbour, (Cell, Charger))]

    def find_closest_shelf(self):
        closest_shelf = None
        min_distance = float('inf')
        for shelf in self.model.shelves:
            distance = self.manhattan_distance(self.pos, shelf.pos)
            if distance and distance < min_distance:
                min_distance = distance
                closest_shelf = shelf

        self.destination = closest_shelf

    def find_closest_charger(self):
        closest_charger = None
        min_distance = float('inf')
        for charger in self.model.chargers:
            distance = self.manhattan_distance(self.pos, charger)
            if distance and distance < min_distance:
                min_distance = distance
                closest_charger = charger

        self.destination = closest_charger

        return closest_charger

    def manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_closest_unoccupied_shelf(self, shelves_row):
        min_distance = float('inf')
        closest_shelf = None
        for pos in shelves_row:
            contents = self.model.grid.get_cell_list_contents(pos)
            if contents and contents[0].limit > 0 and contents[0].stored_box is None:
                distance = self.manhattan_distance(self.pos, pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_shelf = pos
        return closest_shelf

    def shortest_path(self, start, end, robot=None):
        width, height = self.model.grid.width, self.model.grid.height

        start_pos = start.pos if hasattr(start, 'pos') else start
        end_pos = end.pos if hasattr(end, 'pos') else end

        open_set = []
        heappush(open_set, (0, start_pos))

        came_from = {start_pos: None}
        g_score = {start_pos: 0}
        f_score = {start_pos: self.manhattan_distance(start_pos, end_pos)}

        while open_set:
            current = heappop(open_set)[1]

            # Check if we have reached the goal position
            if any(self.manhattan_distance(current, shelf_pos) == 1
                   for shelf_row in self.model.shelves for shelf_pos in shelf_row) and self.box is not None:
                end_pos = current

            if any(self.manhattan_distance(current, charger_pos) == 1 for charger_pos in self.model.chargers):
                end_pos = current

            if current == end_pos:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height:
                    if self.is_obstacle_or_robot(neighbor, robot):
                        continue

                    tentative_g_score = g_score[current] + 1

                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.manhattan_distance(neighbor, end_pos)
                        if neighbor not in [item[1] for item in open_set]:
                            heappush(open_set, (f_score[neighbor], neighbor))

        return [-1]

    def is_obstacle_or_robot(self, pos, robot=None):
        for shelf_row in self.model.shelves:
            if pos in shelf_row:
                return True

        if pos in self.model.chargers or pos in self.model.conveyor_belt:
            return True

        cell_contents = self.model.grid.get_cell_list_contents(pos)
        for content in cell_contents:
            if isinstance(content, Robot) and content != robot:
                return True

        return False

    def pickup_box(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)
        box = [box for box in neighbors if isinstance(box, Box)]
        if len(box) == 0:
            self.next_pos = self.pos
            self.waiting = True
        elif self.waiting:
            self.next_pos = self.pos
            self.waiting = False
        else:
            box = box[0]
            belt = [belt for belt in neighbors if isinstance(belt, ConveyorBelt)][0]
            self.box = box

            self.model.grid.remove_agent(box)
            belt.is_empty = True

            closest_shelves_index = None
            min_distance_to_row = float('inf')

            for i, shelf_row in enumerate(self.model.shelves):
                shelf_available = False
                for shelf_pos in shelf_row:
                    shelf = self.get_shelf_at_pos(shelf_pos)
                    if shelf and shelf.stored_box is None:
                        shelf_available = True
                        break
                if shelf_available:
                    distance_to_row = self.manhattan_distance(self.pos, shelf_row[0])
                    if distance_to_row < min_distance_to_row:
                        min_distance_to_row = distance_to_row
                        closest_shelves_index = i

            if closest_shelves_index is not None:
                closest_shelf = self.find_closest_unoccupied_shelf(self.model.shelves[closest_shelves_index])
                if closest_shelf:
                    self.destination = closest_shelf
                    self.route = self.shortest_path(self.pos, self.destination, self)
                    if self.route and len(self.route) > 1:
                        self.idx_rute = 1
                        self.next_pos = self.route[self.idx_rute]
                        self.idx_rute += 1
                    else:
                        self.next_pos = self.pos

    # Método auxiliar para obtener el estante en una posición dada
    def get_shelf_at_pos(self, pos):
        contents = self.model.grid.get_cell_list_contents(pos)
        for content in contents:
            if isinstance(content, Shelf):
                return content
        return None

    def drop_off(self):
        neighbors = \
        [neighbour for neighbour in self.model.grid.get_neighbors(self.pos, moore=False, include_center=False) if
         isinstance(neighbour, Shelf)][0]

        neighbors.stored_box = self.box
        self.box = None
        self.destination = None
        self.route = []
        self.idx_rute = 0

    def charging(self):
        if self.battery + 20 < 100:
            self.battery += 20
        else:
            self.battery = 100
            self.destination = None
            self.route = []
            self.idx_rute = 0

    def step(self):
        if self.destination is None or self.destination in self.model.chargers:
            if self.box is None and self.battery <= 25:
                charging_station = self.find_closest_charger()
                if charging_station:
                    self.route = self.shortest_path(self.pos, charging_station)
                    self.idx_rute = 0

        if self.route:
            if self.pos == self.route[-1]:
                if self.pos == (11, 6) and self.box is None:
                    self.pickup_box()
                elif self.pos in self.model.chargers:
                    self.charging()
                else:
                    neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False)

                    for neighbor in neighbors:
                        if isinstance(neighbor,
                                      Shelf) and neighbor.stored_box is None and self.destination == neighbor.pos:
                            self.drop_off()
            elif self.idx_rute < len(self.route):
                self.next_pos = self.route[self.idx_rute]
                self.idx_rute += 1
            else:
                self.next_pos = self.pos
                self.idx_rute = 0

        if self.destination and not self.route:
            self.route = self.shortest_path(self.pos, self.destination)
            if self.route == [-1]:
                self.route = []

            self.idx_rute = 0

    def advance(self):
        neighbours = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        other_robots = [neighbour for neighbour in neighbours if isinstance(neighbour, Robot)]

        for robot in other_robots:
            if robot.next_pos == self.next_pos:
                if self.destination is None:
                    y = self.pos[1]
                    if y in [1, 5, 10]:
                        self.next_pos = (self.pos[0], self.pos[1] + 1)
                    else:
                        self.next_pos = (self.pos[0], self.pos[1] - 1)
                elif robot.destination is None:
                    y = robot.pos[1]
                    if y in [1, 5, 10]:
                        robot.next_pos = (robot.pos[0], self.pos[1] + 1)
                    else:
                        robot.next_pos = (robot.pos[0], self.pos[1] - 1)

        if isinstance(self.next_pos, tuple) and len(self.next_pos) == 2:
            if self.pos != self.next_pos:
                self.moves += 1
                self.battery -= 0.5
                self.model.grid.move_agent(self, self.next_pos)
        else:
            self.next_pos = self.pos


def get_robot_data(model):
    robot_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, Robot):
            robot_data.append({
                "unique_id": agent.unique_id,
                "position": agent.pos,
                "has_box": agent.box is not None,
                "battery": agent.battery
            })
    return robot_data


# Function to collect data about conveyor belts
def get_conveyor_belt_data(model):
    conveyor_belt_data = []
    for agent in model.schedule_cinta.agents:
        if isinstance(agent, ConveyorBelt):
            conveyor_belt_data.append({
                "unique_id": agent.unique_id,
                "position": agent.pos,
                "has_box": agent.box is not None
            })
    return conveyor_belt_data


# Function to collect data about shelves
def get_shelf_data(model):
    shelf_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, Shelf):
            shelf_data.append({
                "unique_id": agent.unique_id,
                "position": agent.pos,
                "stored_box": agent.stored_box.unique_id if agent.stored_box else None
            })
    return shelf_data


def get_box_data(model):
    box_data = []
    coords = model.grid.coord_iter()
    # First, get boxes that are on the grid
    for contents in coords:
        for agent in contents:
            if isinstance(agent, Box):
                box_data.append({
                    "unique_id": agent.unique_id,
                    "position": contents[1],
                    "weight": agent.peso,
                    "carried_by_robot": agent.robot.unique_id if agent.robot else None
                })

    # Then, get boxes that are carried by robots
    for agent in model.schedule.agents:
        if isinstance(agent, Robot) and agent.box is not None:
            box_data.append({
                "unique_id": agent.box.unique_id,
                "position": agent.pos,
                "weight": agent.box.peso,
                "carried_by_robot": agent.unique_id
            })
    return box_data


def get_charger_data(model):
    charger_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, Charger):
            charger_data.append({
                "unique_id": agent.unique_id,
                "position": agent.pos,
                "is_occupied": agent.is_occupied
            })
    return charger_data


class Warehouse(Model):
    def __init__(self, num_robots, box_percentage):
        self.num_robots = num_robots
        self.box_percentage = box_percentage
        self.shelves = [[(i, 0) for i in range(2, 7)], [(i, 3) for i in range(2, 7)], [(i, 4) for i in range(2, 7)],
                        [(i, 8) for i in range(2, 7)], [(i, 9) for i in range(2, 7)], [(i, 12) for i in range(2, 7)]]
        self.conveyor_belt = [(12, 6)]
        self.conveyor_belt.extend([(13, i) for i in range(6, 13)])
        self.chargers = [(13, i) for i in range(0, 5)]
        self.box_id = 1000

        # Creación del Grid
        self.grid = MultiGrid(14, 13, False)
        self.schedule = SimultaneousActivation(self)
        self.schedule_cinta = SimultaneousActivation(self)

        available_positions = [pos for _, pos in self.grid.coord_iter()]

        key = 0
        for shelf_pos in self.shelves:
            for pos in shelf_pos:
                shelf = Shelf(key, self)
                key += 1
                self.grid.place_agent(shelf, pos)
                self.schedule.add(shelf)
                available_positions.remove(pos)

        for pos in self.conveyor_belt:
            belt = ConveyorBelt(key, self)
            key += 1
            self.grid.place_agent(belt, pos)

            if pos == (12, 6):
                self.schedule_cinta.add(belt)

            available_positions.remove(pos)

        for pos in self.chargers:
            charger = Charger(key, self)
            key += 1
            self.grid.place_agent(charger, pos)
            self.schedule.add(charger)
            available_positions.remove(pos)

        pos_robots = self.random.sample(available_positions, self.num_robots)

        for pos in available_positions:
            celda = Cell(key, self)
            key += 1
            self.grid.place_agent(celda, pos)

        robots = []

        for pos in pos_robots:
            x_rob, y_rob = pos
            bot = {
                "unique_id": key,
                "x": x_rob,
                "y": y_rob
            }
            robots.append(bot)
            robot = Robot(key, self)
            key += 1
            self.grid.place_agent(robot, pos)
            self.schedule.add(robot)
            available_positions.remove(pos)

        self.datacollector = DataCollector(
            model_reporters={
                "Robots": get_robot_data,
                "ConveyorBelts": get_conveyor_belt_data,
                "Shelves": get_shelf_data,
                "Boxes": get_box_data,
                "Chargers": get_charger_data
            }
        )

    def collect_detailed_data(self):
        step_data = {
            "Robots": get_robot_data(self),
            "ConveyorBelts": get_conveyor_belt_data(self),
            "Shelves": get_shelf_data(self),
            "Boxes": get_box_data(self),
            "Chargers": get_charger_data(self)
        }
        return step_data

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        self.schedule_cinta.step()


def get_grid(model: Model) -> np.ndarray:
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        x, y = pos
        for obj in cell_content:
            if isinstance(obj, Robot):
                grid[x][y] = 2
    return grid
