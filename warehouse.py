import time
import math
import pybullet as p
import pybullet_data

SQUARE_SIZE = 2.0
ROBOT_START_POS = (1, 1)

FORCE = 150
VELOCITY = 15
DISTANCE_THRESHOLD = 0.8

# W = WAREHOUSE, . = FLOOR, B = BLOCKED
WAREHOUSE_LAYOUT = [
    "W.W.WB",
    "......B",
    "W.W.WB",
    "......B",
    "W.W.WB"
]

def create_warehouse_grid(layout, square_size):
    print("Creating warehouse grid...")
    tile_half_extents = [square_size / 2, square_size / 2, 0.01]
    wall_half_extents = [square_size / 2, square_size / 2, 0.5]

    COLORS = {
        'W': [0.5, 0.5, 0.5, 1], # Grey for warehouse
        '.': [0.8, 0.8, 0.8, 1], # Light grey for floor
        'B_floor': [0.6, 0.2, 0.2, 1],
        'B_wall': [1, 0, 0, 1] # Bright red for blocked wall
    }

    warehouses = {}

    for row, line in enumerate(layout):
        for col, char in enumerate(line):
            tile_pos = [col * square_size, row * square_size, 0.01]
            
            tile_color = COLORS.get(char, COLORS['.'])
            if char == 'B':
                tile_color = COLORS['B_floor']
                
            visualShapeId = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=tile_half_extents, rgbaColor=tile_color)
            p.createMultiBody(baseMass=0, baseVisualShapeIndex=visualShapeId, basePosition=tile_pos)

            if char == 'W':
                warehouses[(row, col)] = [f"item_{row}_{col}_A", f"item_{row}_{col}_B"]
                
            elif char == 'B': 
                wall_pos = [col * square_size, row * square_size, 0.5]
                visualShapeId = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=wall_half_extents, rgbaColor=COLORS['B_wall'])
                collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=wall_half_extents)
                p.createMultiBody(baseMass=0, baseVisualShapeIndex=visualShapeId, baseCollisionShapeIndex=collisionShapeId, basePosition=wall_pos)

    print("Grid created.")
    return warehouses

def find_warehouse_for_item(item_name, warehouses):
    """Finds the grid coordinates of the warehouse holding a given item."""
    for wh_pos, items in warehouses.items():
        if item_name in items:
            return wh_pos
    return None

def update_ui(orders, ui_text_ids):
    """Draws and updates the UI panel with order information."""
    for item_id in ui_text_ids:
        p.removeUserDebugItem(item_id)
    ui_text_ids.clear()
    
    cam_data = p.getDebugVisualizerCamera()
    cam_pos = cam_data[11]
    
    header_pos = [cam_pos[0] + 4, cam_pos[1] + 8, cam_pos[2] + 2]
    header_id = p.addUserDebugText("--- Orders ---", header_pos, textColorRGB=[1,1,0], textSize=1.5)
    ui_text_ids.append(header_id)

    for i, order in enumerate(orders):
        robot_str = f"Robot {order['robot_id']}" if order['robot_id'] is not None else "Unassigned"
        items_str = ', '.join(order['items_needed']) if order['items_needed'] else "None"
        text = f"Order {order['id']} ({order['status']}) - Items: {items_str} - {robot_str}"
        text_pos = [header_pos[0], header_pos[1], header_pos[2] - (i + 1) * 0.4]
        text_id = p.addUserDebugText(text, text_pos, textColorRGB=[1,1,1], textSize=1.2)
        ui_text_ids.append(text_id)
        
    return ui_text_ids

def set_robot_target(robot, item_name, warehouses):
    target_grid_pos = find_warehouse_for_item(item_name, warehouses)
    if target_grid_pos:
        target_world_pos = (target_grid_pos[1] * SQUARE_SIZE, target_grid_pos[0] * SQUARE_SIZE)
        robot['target_pos'] = target_world_pos
        robot['state'] = 'moving_to_warehouse'
        print(f"Robot {robot['id']} heading to {target_grid_pos} for item {item_name}.")
        return True
    else:
        print(f"Warning: Could not find warehouse for item {item_name}")
        return False

def main():
    physicsClient = p.connect(p.GUI)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -10)
    p.setRealTimeSimulation(0)

    p.loadURDF("plane.urdf")
    
    warehouses = create_warehouse_grid(WAREHOUSE_LAYOUT, SQUARE_SIZE)

    orders = [
        {"id": 1, "items_needed": ["item_0_0_A", "item_2_2_B"], "status": "pending", "robot_id": None},
        {"id": 2, "items_needed": ["item_4_4_A"], "status": "pending", "robot_id": None},
    ]
    
    start_world_pos = [ROBOT_START_POS[1] * SQUARE_SIZE, ROBOT_START_POS[0] * SQUARE_SIZE, 0.5]
    robotId = p.loadURDF("r2d2.urdf", start_world_pos, p.getQuaternionFromEuler([0,0,0]))
    robots = [{"id": 0, "robotId": robotId, "state": "idle", "order_id": None, "target_pos": None}]

    ui_text_ids = []

    try:
        while True:
            ui_text_ids = update_ui(orders, ui_text_ids)

            for robot in robots:
                if robot['state'] == 'idle':
                    next_order = next((o for o in orders if o['status'] == 'pending'), None)
                    if next_order:
                        print(f"Assigning Order {next_order['id']} to Robot {robot['id']}")
                        next_order['status'] = 'assigned'
                        next_order['robot_id'] = robot['id']
                        robot['order_id'] = next_order['id']
                        
                        first_item = next_order['items_needed'][0]
                        if not set_robot_target(robot, first_item, warehouses):
                             next_order['status'] = 'error'
                             robot['state'] = 'idle' 

                elif robot['state'] == 'moving_to_warehouse':
                    pos, orn = p.getBasePositionAndOrientation(robot['robotId'])
                    yaw = p.getEulerFromQuaternion(orn)[2]
                    
                    goal = robot['target_pos']
                    dx = goal[0] - pos[0]
                    dy = goal[1] - pos[1]
                    distance = math.sqrt(dx*dx + dy*dy)

                    if distance < DISTANCE_THRESHOLD:
                        order = next((o for o in orders if o['id'] == robot['order_id']), None)
                        
                        picked_item = order['items_needed'].pop(0)
                        print(f"Robot {robot['id']} picked up {picked_item} for Order {order['id']}.")
                        
                        # small delay for pickup
                        for _ in range(60): # 1/4 second
                            p.setJointMotorControl2(robot['robotId'], 2, p.VELOCITY_CONTROL, targetVelocity=0, force=FORCE)
                            p.setJointMotorControl2(robot['robotId'], 6, p.VELOCITY_CONTROL, targetVelocity=0, force=FORCE)
                            p.stepSimulation()
                            time.sleep(1/240)

                        if not order['items_needed']: 
                            print(f"Order {order['id']} complete!")
                            order['status'] = 'complete'
                            robot['state'] = 'idle'
                            robot['target_pos'] = None
                        else: 
                            next_item = order['items_needed'][0]
                            if not set_robot_target(robot, next_item, warehouses):
                                order['status'] = 'error'
                                robot['state'] = 'idle'
                    else:
                        # Navigation logic
                        target_angle = math.atan2(dy, dx)
                        angle_error = math.atan2(math.sin(target_angle - yaw), math.cos(target_angle - yaw))
                        
                        if abs(angle_error) > 0.2:
                            turn_speed = max(5, min(VELOCITY, VELOCITY * abs(angle_error)))
                            left_vel = -turn_speed if angle_error > 0 else turn_speed
                            right_vel = turn_speed if angle_error > 0 else -turn_speed
                        else:
                            left_vel = right_vel = VELOCITY
                    
                        p.setJointMotorControl2(robot['robotId'], 2, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=FORCE)
                        p.setJointMotorControl2(robot['robotId'], 6, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=FORCE)

            p.stepSimulation()
            time.sleep(1 / 240)

    except p.error as e:
        print(f"PyBullet error: {e}")
    finally:
        if p.isConnected():
            p.disconnect()

if __name__ == "__main__":
    main()