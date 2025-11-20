from task import Task

item_locations = {"Gadget": (0, 0), "Sprocket": (0, 2), "Widget": (0, 4)}

def get_tasks_for_item_sort(warehouse, item, amount, pos):
    tasks = []
    if item_locations[item] != pos:
        tasks.append(Task(warehouse.shelves[pos], item, amount, is_pickup=True))
        tasks.append(Task(warehouse.shelves[item_locations[item]], item, amount, is_pickup=False))
    return tasks


