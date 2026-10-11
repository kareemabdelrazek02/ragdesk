# ROS 2 Navigation Notes

ROS 2 organizes software into nodes that exchange messages over topics. A node publishes sensor readings such as LiDAR scans, and other nodes subscribe to them. Communication runs on DDS middleware, which handles discovery and quality of service settings.

The Nav2 stack provides autonomous navigation for mobile robots. It uses a global planner to compute a path across the costmap and a local controller to follow that path while avoiding obstacles. Behavior trees coordinate recovery actions such as clearing the costmap or backing up when the robot gets stuck.

A URDF file describes the robot geometry, joints and sensor frames. The transform tree, managed by tf2, links the map, odom and base_link frames so that sensor data can be placed in a common coordinate frame.

Simulation in a digital twin lets teams test navigation safely before deploying to a physical robot. Sensor noise and latency should be modeled so that results transfer to the real system.
