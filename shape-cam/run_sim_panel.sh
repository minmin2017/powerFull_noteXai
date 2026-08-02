#!/bin/bash
# Panel กล้องแขนกลในซิม Gazebo — เปิด http://localhost:8090
# ต้องรันซิมก่อน: ros2 launch arm_bringup arm_gazebo.launch.py (ใน arm_sim_ws)
source /opt/ros/humble/setup.bash
source "$HOME/arm_sim_ws/install/setup.bash"
exec python3 "$(dirname "$0")/shape_cam_ros.py" "$@"
