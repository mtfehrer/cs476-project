import heapq
import random
from typing import List, Tuple, Dict, Optional
from task import Task


class Robot:

    def __init__(self, position: Tuple[int, int], robot_id: int, warehouse):
        self.position = position
        self.robot_id = robot_id
        self.warehouse = warehouse
        self.path: List[Tuple[int, int]] = []
        self.current_order: Optional[Task] = None
        self.inventory: Dict[str, int] = {}
        self.state = "idle"

    def get_position_at_time(self, time_offset: int) -> Tuple[int, int]:
        """ Predicts where the robot will be time_offset steps later """
        if time_offset == 0:
            return self.position

        if self.path and len(self.path) > 0:
            index = time_offset - 1
            if index < len(self.path):
                return self.path[index]
            else:
                return self.path[-1]

        return self.position

    def scatter(self):
        """ Moves to a random valid neighbor to get out of the way """
        possible_moves = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            r, c = self.position[0] + dr, self.position[1] + dc

            if 0 <= r < len(self.warehouse.map_) and 0 <= c < len(self.warehouse.map_[0]):
                if self.warehouse.map_[r][c] == 0:
                    if not self.warehouse.is_position_occupied(r, c):
                        possible_moves.append((r, c))

        if possible_moves:
            target = random.choice(possible_moves)
            print(f"Robot {self.robot_id} moving to {target}")
            self.goto(target)
        else:
            print(f"Robot {self.robot_id} really really stuck")

    def goto(self, target: Tuple[int, int], avoid_next_pos: Optional[Tuple[int, int]] = None):
        """Calculates a path to the target."""
        occupant = self.warehouse.get_robot_at(target[0], target[1])
        if occupant and occupant.robot_id != self.robot_id and occupant.state == "idle":
            print(f"Robot {self.robot_id} is blocked by {occupant.robot_id}, moving him")
            occupant.scatter()

        self.path = self._astar(self.position, target, avoid_next_pos)

        if avoid_next_pos:
            print(f"Robot {self.robot_id} replanning with blocked on {avoid_next_pos}")

        if self.path:
            self.path = self.path[1:] 
            self.state = "moving"
        else:
            print(f"Robot {self.robot_id} could not find path to {target}")

    def _astar(self, start: Tuple[int, int], goal: Tuple[int, int], avoid_next_pos: Optional[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        
        def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def get_neighbors(pos: Tuple[int, int], time: int) -> List[Tuple[int, int]]:
            neighbors = []
            dirs = [(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)]

            for dr, dc in dirs:
                new_r, new_c = pos[0] + dr, pos[1] + dc
                new_time = time + 1

                if (new_time == 1 and avoid_next_pos and (new_r, new_c) == avoid_next_pos):
                    continue

                if 0 <= new_r < len(self.warehouse.map_) and 0 <= new_c < len(self.warehouse.map_[0]):

                    is_obstacle = self.warehouse.map_[new_r][new_c] != 0
                    is_goal = (new_r, new_c) == goal

                    if not is_obstacle or is_goal:
                        # check if it WILL be occupied
                        if not self.warehouse.is_occupied_at_time(new_r, new_c, new_time, exclude_robot_id=self.robot_id):
                            neighbors.append((new_r, new_c))

            return neighbors

        start_time = 0
        frontier = [(0, start_time, start)]

        came_from = {}  # (row, col, time) -> (prev_row, prev_col, prev_time)
        cost_so_far = {}  # (row, col, time) -> cost

        start_state = (start[0], start[1], start_time)
        came_from[start_state] = None
        cost_so_far[start_state] = 0

        max_time_depth = 50

        best_goal_state = None

        while frontier:
            _, current_time, current_pos = heapq.heappop(frontier)

            if current_pos == goal:
                best_goal_state = (current_pos[0], current_pos[1], current_time)
                break

            if current_time >= max_time_depth:
                continue

            for next_pos in get_neighbors(current_pos, current_time):
                next_time = current_time + 1
                new_cost = (cost_so_far[(current_pos[0], current_pos[1], current_time)] + 1)

                next_state = (next_pos[0], next_pos[1], next_time)

                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    priority = new_cost + manhattan(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_time, next_pos))
                    came_from[next_state] = (
                        current_pos[0],
                        current_pos[1],
                        current_time
                    )

        if not best_goal_state:
            return []
        
        path = []
        current = best_goal_state
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path
    
    def execute_order(self, order: Task):
        self.current_order = order
        self.goto(order.shelf.position)
    
    def update(self, should_move: bool):
        if self.state == "moving" and self.path and should_move:
            next_pos = self.path[0]

            if not self.warehouse.is_position_occupied(next_pos[0], next_pos[1], exclude_robot=self.robot_id):
                self.position = next_pos
                self.path = self.path[1:]
                
                # if end of path, stop moving
                if not self.path:
                    self.state = "idle"
                    if self.current_order:
                        self._fulfill_order()
            else:
                # path is blocked
                print(f"Robot {self.robot_id} blocked at {next_pos}. replanning...")

                # if destination is blocked by idle robot, move that robot
                blocker = self.warehouse.get_robot_at(next_pos[0], next_pos[1])
                if blocker and blocker.state == "idle":
                    blocker.scatter()

                if self.current_order:
                    self.goto(self.current_order.shelf.position, avoid_next_pos=next_pos)

                    wait_steps = random.randint(1, 3)
                    for _ in range(wait_steps):
                        self.path.insert(0, self.position)

    def _fulfill_order(self):
        if not self.current_order:
            return
        
        order = self.current_order
        
        if order.is_pickup:
            # pick up 
            if order.shelf.remove_item(order.item_name, order.quantity):
                if order.item_name in self.inventory:
                    self.inventory[order.item_name] += order.quantity
                else:
                    self.inventory[order.item_name] = order.quantity
                print(f"Robot {self.robot_id} picked up {order.quantity}x {order.item_name}")
        else:
            # drop off
            if order.item_name in self.inventory and self.inventory[order.item_name] >= order.quantity:
                order.shelf.add_item(order.item_name, order.quantity)
                self.inventory[order.item_name] -= order.quantity
                if self.inventory[order.item_name] == 0:
                    del self.inventory[order.item_name]
                print(f"Robot {self.robot_id} dropped off {order.quantity}x {order.item_name}")
        
        self.current_order = None