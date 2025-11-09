import pybullet as p
import pybullet_data
import time
import math
import random
import os

physics_client = p.connect(p.GUI) 
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.resetDebugVisualizerCamera(cameraDistance=15, cameraYaw=45, cameraPitch=-30, cameraTargetPosition=[0, 0, 0])

p.setGravity(0, 0, -9.81)
p.setTimeStep(1.0 / 240.0)
plane_id = p.loadURDF("plane.urdf")

def make_wall(half_extents, pos):
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents),
        baseVisualShapeIndex=p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents, rgbaColor=[0.6, 0.6, 0.6, 1]),
        basePosition=pos
    )

make_wall([0.1, 10, 0.5], [10, 0, 0.5])
make_wall([0.1, 10, 0.5], [-10, 0, 0.5])
make_wall([10, 0.1, 0.5], [0, 10, 0.5])
make_wall([10, 0.1, 0.5], [0, -10, 0.5])

SHELVES = [] 

def create_shelf(pos, orientation_euler=(0, 0, 0)):
    shelf_mass = 0
    shelf_width = 1.0
    shelf_depth = 0.5
    shelf_height = 2.0
    shelf_plate_height = 0.05

    leg_half_extents = [0.05, 0.05, shelf_height / 2.0]
    plate_half_extents = [shelf_width / 2.0, shelf_depth / 2.0, shelf_plate_height / 2.0]

    base_collision_shape_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0, 0, 0])
    base_visual_shape_id = p.createVisualShape(p.GEOM_BOX, halfExtents=[0, 0, 0], rgbaColor=[0, 0, 0, 0])

    link_masses = [0] * 6
    link_collision_shapes = [p.createCollisionShape(p.GEOM_BOX, halfExtents=leg_half_extents) for _ in range(4)]
    link_collision_shapes.extend([p.createCollisionShape(p.GEOM_BOX, halfExtents=plate_half_extents) for _ in range(2)])

    gray = [0.5, 0.5, 0.5, 1]
    light = [0.8, 0.8, 0.8, 1]
    link_visual_shapes = [p.createVisualShape(p.GEOM_BOX, halfExtents=leg_half_extents, rgbaColor=gray) for _ in range(4)]
    link_visual_shapes.extend([p.createVisualShape(p.GEOM_BOX, halfExtents=plate_half_extents, rgbaColor=light) for _ in range(2)])

    joint_positions = [
        [ 0.5,  0.25, shelf_height/2],
        [-0.5,  0.25, shelf_height/2],
        [ 0.5, -0.25, shelf_height/2],
        [-0.5, -0.25, shelf_height/2],
        [ 0.0,  0.0,  shelf_height - shelf_plate_height],    
        [ 0.0,  0.0,  shelf_height/2 - shelf_plate_height],  
    ]

    shelf_id = p.createMultiBody(
        baseMass=shelf_mass,
        baseCollisionShapeIndex=base_collision_shape_id,
        baseVisualShapeIndex=base_visual_shape_id,
        basePosition=pos,
        baseOrientation=p.getQuaternionFromEuler(orientation_euler),
        linkMasses=link_masses,
        linkCollisionShapeIndices=link_collision_shapes,
        linkVisualShapeIndices=link_visual_shapes,
        linkPositions=joint_positions,
        linkOrientations=[[0, 0, 0, 1]] * 6,
        linkInertialFramePositions=[[0, 0, 0]] * 6,
        linkInertialFrameOrientations=[[0, 0, 0, 1]] * 6,
        linkParentIndices=[0] * 6,
        linkJointTypes=[p.JOINT_FIXED] * 6,
        linkJointAxis=[[0, 0, 0]] * 6
    )
    top_level_z = pos[2] + (2.0 - 0.05) + 0.025
    mid_level_z = pos[2] + (1.0 - 0.05) + 0.025

    SHELVES.append({
        "id": shelf_id,
        "pos": pos,
        "levels": [mid_level_z, top_level_z],
        "size": (1.0, 0.5)
    })
    return shelf_id
shelf_spacing = 2.5
shelf_rows = 5
shelf_cols = 3
for row in range(shelf_rows):
    for col in range(shelf_cols):
        pos_x = (col - shelf_cols / 2) * shelf_spacing
        pos_y = (row - shelf_rows / 2) * shelf_spacing
        create_shelf([pos_x, pos_y, 0], (0, 0, 0))

def create_box(size=(0.08, 0.08, 0.08), mass=0.3, color=(1, 0, 0, 1), pos=(0, 0, 1), orn=(0, 0, 0)):
    half = [s / 2 for s in size]
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half)
    vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=color)
    body = p.createMultiBody(baseMass=mass, baseCollisionShapeIndex=col, baseVisualShapeIndex=vis,
                             basePosition=pos, baseOrientation=p.getQuaternionFromEuler(orn))
    p.changeDynamics(body, -1, lateralFriction=0.8, rollingFriction=0.001, spinningFriction=0.001)
    return body

def create_cylinder(radius=0.04, height=0.12, mass=0.25, color=(0.2, 0.6, 1, 1), pos=(0, 0, 1), orn=(0, 0, 0)):
    col = p.createCollisionShape(p.GEOM_CYLINDER, radius=radius, height=height)
    vis = p.createVisualShape(p.GEOM_CYLINDER, radius=radius, length=height, rgbaColor=color)
    body = p.createMultiBody(baseMass=mass, baseCollisionShapeIndex=col, baseVisualShapeIndex=vis,
                             basePosition=pos, baseOrientation=p.getQuaternionFromEuler(orn))
    p.changeDynamics(body, -1, lateralFriction=0.9, rollingFriction=0.001, spinningFriction=0.001)
    return body

def create_bin(size=(0.18, 0.14, 0.1), wall=0.01, mass=0.4, color=(0.2, 0.8, 0.2, 1), pos=(0, 0, 1)):
    sx, sy, sz = size
    parts = []
    base = create_box((sx, sy, wall), mass=mass*0.2, color=color, pos=(pos[0], pos[1], pos[2]))
    parts.append(base)
    halfx, halfy = sx/2, sy/2
    zc = pos[2] + wall/2 + sz/2
    parts.append(create_box((wall, sy, sz), mass=mass*0.2, color=color, pos=(pos[0]+halfx-wall/2, pos[1], zc)))
    parts.append(create_box((wall, sy, sz), mass=mass*0.2, color=color, pos=(pos[0]-halfx+wall/2, pos[1], zc)))
    parts.append(create_box((sx, wall, sz), mass=mass*0.2, color=color, pos=(pos[0], pos[1]+halfy-wall/2, zc)))
    parts.append(create_box((sx, wall, sz), mass=mass*0.2, color=color, pos=(pos[0], pos[1]-halfy+wall/2, zc)))
    return parts

def place_on_shelf(shelf, obj_dims, x_offset=0.0, y_offset=0.0, level_index=0, margin=0.02):
    shelf_x, shelf_y, shelf_z = shelf["pos"]
    w, d = shelf["size"]
    level_z = shelf["levels"][level_index]

    if isinstance(obj_dims, tuple) and len(obj_dims) == 3:
        half_z = obj_dims[2] / 2.0
    else:
        half_z = 0.05

    x = shelf_x + max(-w/2 + margin, min(w/2 - margin, x_offset))
    y = shelf_y + max(-d/2 + margin, min(d/2 - margin, y_offset))
    z = level_z + half_z + 0.001
    return (x, y, z)

random.seed(3)
OBJECTS = []
for shelf in SHELVES:
    for level_i in [0, 1]:
        for k in range(3):
            dx = (k - 1) * 0.25
            dy = random.uniform(-0.15, 0.15)
            choice = random.choice(["box", "cyl", "bin"])
            if choice == "box":
                size = (0.08, 0.08, 0.08)
                pos = place_on_shelf(shelf, size, dx, dy, level_i)
                obj = create_box(size=size, mass=0.25, color=(1, 0.3, 0.3, 1), pos=pos)
                OBJECTS.append(obj)
            elif choice == "cyl":
                radius, height = 0.04, 0.12
                pos = place_on_shelf(shelf, (radius*2, radius*2, height), dx, dy, level_i)
                obj = create_cylinder(radius=radius, height=height, mass=0.2, color=(0.2, 0.6, 1, 1), pos=pos)
                OBJECTS.append(obj)
            else:
                size = (0.18, 0.14, 0.1)
                pos = place_on_shelf(shelf, size, dx, dy, level_i)
                parts = create_bin(size=size, pos=pos)
                OBJECTS.extend(parts)

robot_start_pos = [2.5, -3.0, 0.0]   
robot_start_orn = p.getQuaternionFromEuler([0, 0, math.pi/2]) 
panda_uid = p.loadURDF("franka_panda/panda.urdf", robot_start_pos, robot_start_orn, useFixedBase=True)

def print_joint_table(body_uid, title="Robot joints and links"):
    print("\n" + title)
    print("idx  joint_name                link_name")
    print("----------------------------------------")
    for i in range(p.getNumJoints(body_uid)):
        ji = p.getJointInfo(body_uid, i)
        jn = ji[1].decode() if isinstance(ji[1], bytes) else ji[1]
        ln = ji[12].decode() if isinstance(ji[12], bytes) else ji[12]
        print(f"{i:2d}   {jn:24s}   {ln}")
    print("----------------------------------------\n")

def resolve_panda_indices(body_uid):
    num_j = p.getNumJoints(body_uid)
    joint_name_to_idx = {}
    link_name_to_idx = {}
    for i in range(num_j):
        ji = p.getJointInfo(body_uid, i)
        jname = ji[1].decode("utf-8") if isinstance(ji[1], bytes) else ji[1]
        lname = ji[12].decode("utf-8") if isinstance(ji[12], bytes) else ji[12]
        joint_name_to_idx[jname] = i
        link_name_to_idx[lname] = i

    ee_candidates = ["panda_hand", "hand", "panda_grasptarget", "panda_link8", "link7", "tool0", "tcp"]
    ee_link_index = None
    for name in ee_candidates:
        if name in link_name_to_idx:
            ee_link_index = link_name_to_idx[name]
            break
    if ee_link_index is None and link_name_to_idx:
        ee_link_index = max(link_name_to_idx.values())

    finger1 = None
    finger2 = None
    finger1_candidates = ["panda_finger_joint1", "finger_joint1", "finger1_joint", "leftfinger_joint"]
    finger2_candidates = ["panda_finger_joint2", "finger_joint2", "finger2_joint", "rightfinger_joint"]
    for name in finger1_candidates:
        if name in joint_name_to_idx:
            finger1 = joint_name_to_idx[name]
            break
    for name in finger2_candidates:
        if name in joint_name_to_idx:
            finger2 = joint_name_to_idx[name]
            break
    if finger1 is None or finger2 is None:
        finger_idxs = [idx for nm, idx in joint_name_to_idx.items() if "finger" in nm]
        finger_idxs = sorted(set(finger_idxs))
        if len(finger_idxs) >= 2:
            if finger1 is None:
                finger1 = finger_idxs[0]
            if finger2 is None:
                finger2 = finger_idxs[1]
    if finger1 is None or finger2 is None:
        print_joint_table(body_uid, "Could not auto-detect Panda finger joints. Here is the table:")
        raise RuntimeError("Set finger1 and finger2 to the correct joint indices printed above.")
    return ee_link_index, finger1, finger2

print_joint_table(panda_uid)
ee_link_index, finger1, finger2 = resolve_panda_indices(panda_uid)

def set_gripper(opening=0.04):
    p.setJointMotorControl2(panda_uid, finger1, p.POSITION_CONTROL, targetPosition=opening/2, force=20)
    p.setJointMotorControl2(panda_uid, finger2, p.POSITION_CONTROL, targetPosition=opening/2, force=20)

def step_for(dt=1.0):
    steps = int(dt / (1.0 / 240.0))
    for _ in range(steps):
        p.stepSimulation()
        time.sleep(1.0 / 240.0)

def move_ee(target_pos, target_rpy=(math.pi, 0, 0), settle_time=0.75):
    target_orn = p.getQuaternionFromEuler(target_rpy)
    joint_poses = p.calculateInverseKinematics(panda_uid, ee_link_index, target_pos, target_orn)
    for j in range(7):  # first 7 are the arm
        p.setJointMotorControl2(panda_uid, j, p.POSITION_CONTROL, joint_poses[j], force=200)
    step_for(settle_time)


def get_body_pos(body_id):
    pos, _ = p.getBasePositionAndOrientation(body_id)
    return list(pos)

def dist2(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2

robot_xy = robot_start_pos[:2]
target_obj = min(OBJECTS, key=lambda oid: dist2(get_body_pos(oid), robot_xy))
obj_pos = get_body_pos(target_obj)

pregrasp_pos = [obj_pos[0], obj_pos[1] - 0.30, obj_pos[2] + 0.25]
grasp_pos    = [obj_pos[0], obj_pos[1],      obj_pos[2] + 0.05]
lift_pos     = [obj_pos[0], obj_pos[1],      obj_pos[2] + 0.35]
place_pos    = [robot_start_pos[0]-0.5, robot_start_pos[1]+0.6, 0.25]


set_gripper(0.06)
move_ee(pregrasp_pos, target_rpy=(math.pi, 0, 0))
move_ee([grasp_pos[0], grasp_pos[1], pregrasp_pos[2]], target_rpy=(math.pi, 0, 0))
move_ee(grasp_pos, target_rpy=(math.pi, 0, 0))

set_gripper(0.0)
step_for(0.4)

cid = p.createConstraint(
    parentBodyUniqueId=panda_uid, parentLinkIndex=ee_link_index,
    childBodyUniqueId=target_obj, childLinkIndex=-1,
    jointType=p.JOINT_FIXED, jointAxis=[0, 0, 0],
    parentFramePosition=[0, 0, 0.02], childFramePosition=[0, 0, 0]
)

move_ee(lift_pos, target_rpy=(math.pi, 0, 0))
move_ee([place_pos[0], place_pos[1], lift_pos[2]], target_rpy=(math.pi, 0, 0))
move_ee([place_pos[0], place_pos[1], place_pos[2]+0.05], target_rpy=(math.pi, 0, 0))

p.removeConstraint(cid)
set_gripper(0.06)
step_for(0.4)

move_ee([place_pos[0], place_pos[1]-0.3, place_pos[2]+0.3], target_rpy=(math.pi, 0, 0))
print("Pick and place demo done. You can explore the scene now.")

while p.isConnected():
    p.stepSimulation()
    time.sleep(1.0 / 2400.0)

p.disconnect()
