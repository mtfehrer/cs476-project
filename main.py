import pybullet as p
import time
import pybullet_data

physicsClient = p.connect(p.GUI)
p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -10)

planeId = p.loadURDF("plane.urdf")
visualShapeId = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.5], rgbaColor=[1, 0, 0, 1])
collisionShapeId = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.5])

p.createMultiBody(
    baseMass=1,
    baseVisualShapeIndex=visualShapeId,
    baseCollisionShapeIndex=collisionShapeId,
    basePosition=[0, 0, 1],
)

for i in range(10000):
    p.stepSimulation()
    time.sleep(1 / 240)

p.disconnect()
