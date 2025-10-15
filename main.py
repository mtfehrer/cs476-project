import time
import math
import pybullet as p
import pybullet_data

physicsClient = p.connect(p.GUI)
p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -10)

planeId = p.loadURDF("plane.urdf")
robotId = p.loadURDF("r2d2.urdf", [0, 0, 0.5], p.getQuaternionFromEuler([0,0,0]))

goal = (5, 6)
force = 100
velocity = 50

#place goal marker
visualShapeId = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.5], rgbaColor=[1, 0, 0, 1])
collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.5])
p.createMultiBody(
    baseMass=1,
    baseVisualShapeIndex=visualShapeId,
    baseCollisionShapeIndex=collisionShapeId,
    basePosition=[goal[0], goal[1], 2],
)

while True:
    pos, orn = p.getBasePositionAndOrientation(robotId)
    x, y, z = pos
    yaw = p.getEulerFromQuaternion(orn)[2]

    dx = goal[0] - x
    dy = goal[1] - y
    distance = math.sqrt(dx*dx + dy*dy)
    target_angle = -math.atan2(dy, dx)
    angle_error = target_angle - yaw

    if distance < 1:  # close enough
        left_vel = right_vel = 0
    elif abs(angle_error) > 0.2:  # turn towards goal
        left_vel = velocity if angle_error > 0 else -velocity
        right_vel = -velocity if angle_error > 0 else velocity
    else:  # go straight
        left_vel = right_vel = -velocity

    # 2 right_front_wheel_joint
    # 6 left_front_wheel_joint
    p.setJointMotorControl2(robotId, 2, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=force)
    p.setJointMotorControl2(robotId, 6, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=force)
    p.stepSimulation()
    time.sleep(1 / 240)

p.disconnect()
