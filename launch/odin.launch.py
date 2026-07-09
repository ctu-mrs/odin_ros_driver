
# USAGE: ros2 launch odin_ros_driver odin1_ros2.launch.py
import os
import yaml 
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    # Create launch description
    ld = LaunchDescription()

    pkg_name = "odin_ros_driver"

    this_pkg_path = get_package_share_directory(pkg_name)
    namespace="odin"
    
    # #{ config

    config = LaunchConfiguration('config')

    ld.add_action(DeclareLaunchArgument(
        'config',
        default_value=os.path.join(this_pkg_path, 'config', 'control_command.yaml'),
        description='Path to the default config YAML file'
    ))

    # #} end of config

    # #{ uav_name

    uav_name = LaunchConfiguration('uav_name')

    ld.add_action(DeclareLaunchArgument(
        'uav_name',
        default_value=os.getenv('UAV_NAME', "uav1"),
        description="The uav name used for namespacing.",
    ))

    # #} end of custom_config
    
    ld.add_action(Node(
        package='odin_ros_driver',
        executable='host_sdk_sample',
        name='host_sdk_sample',
        output='screen',
        namespace=namespace,
        parameters=[
            {'odom_frame': "odin_odom"},
            {'map_frame': "odin_map"},
            {'body_frame': "odin_body"},
            {'camera_frame': "odin_camera"},
            {'log_dir': "/tmp/odin/log"},
            {'map_dir': "/tmp/odin/map"},
            {'data_dir': "/tmp/odin/data"},
            {'config_dir': "/tmp/odin/config"},
            {'config': config}
        ]
    ))

    # ld.add_action(
    #     # Nodes under test
    #     Node(
    #         package='tf2_ros',
    #         namespace='',
    #         executable='static_transform_publisher',
    #         name='odin_camera_tf',
    #         arguments=["0.0", "0.0", "0.0", "-1.57", "0", "-1.57", "odin_body", "odin_camera"],
    #     )
    # )

    # pcd2depth_config_path = os.path.join(this_pkg_path, 'config', 'control_command.yaml')
    # with open(pcd2depth_config_path, 'r') as f:
    #     pcd2depth_params = yaml.safe_load(f) 
    # pcd2depth_calib_path = os.path.join(this_pkg_path, 'config', 'calib.yaml')
    # pcd2depth_params['calib_file_path'] = pcd2depth_calib_path 
    # ld.add_action(Node(
    #     package='odin_ros_driver',
    #     executable='pcd2depth_ros2_node',  
    #     name='pcd2depth_ros2_node',
    #     output='screen',
    #     namespace=namespace,
    #     parameters=[pcd2depth_params]
    # ))

    # # Image overlay node - overlays reprojected points on camera image
    # overlay_config_path = os.path.join(this_pkg_path, 'config', 'control_command.yaml')
    # with open(overlay_config_path, 'r') as f:
    #     overlay_params = yaml.safe_load(f)

    # ld.add_action(Node(
    #     package='odin_ros_driver',
    #     executable='image_overlay_node',  
    #     name='image_overlay_node',
    #     output='screen',
    #     namespace=namespace,
    #     parameters=[overlay_params]
    # ))
    
    return ld
