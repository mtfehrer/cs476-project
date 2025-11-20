from typing import List
from warehouse import Warehouse
from importer import Importer
from utils import get_tasks_for_item_sort
from task import Task


class Brain:
    def __init__(self, warehouse: Warehouse, importer: Importer):
        self.warehouse = warehouse
        self.importer = importer
        self.task_queue: List[Task] = []

        self.items_timer = 200
        self.add_items_timer = 0

    def update(self):
        self._handle_imports()
        self._assign_tasks()

    def _handle_imports(self):
        """ Generates new items and tasks periodically """
        self.add_items_timer += 1
        should_add_item = self.add_items_timer >= self.items_timer

        if should_add_item:
            random_shelf = self.warehouse.get_random_shelf()
            item, amount = self.importer.add_random_item(random_shelf)

            new_tasks = get_tasks_for_item_sort(self.warehouse, item, amount, random_shelf.position)
            self.task_queue.extend(new_tasks)
            self.add_items_timer = 0

    def _assign_tasks(self):
        """ Assigns pending tasks to idle robots based on inventory requirements """
        if not self.task_queue:
            return

		# assigns jobs to idle robots
        for robot in self.warehouse.robots:
            if robot.state == "idle":

                task_index = -1

                for i, task in enumerate(self.task_queue):
                    if task.is_pickup:
                        task_index = i
                        break
                    else:
                        # check to see if you can take it
                        amt_in_inventory = robot.inventory.get(task.item_name, 0)
                        if amt_in_inventory >= task.quantity:
                            task_index = i
                            break

                if task_index != -1:
                    task = self.task_queue.pop(task_index)
                    robot.execute_order(task)
