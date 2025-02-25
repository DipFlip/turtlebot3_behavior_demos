from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from os.path import join


def generate_launch_description():
    tb3_world_dir = get_package_share_directory("tb3_worlds")
    tb3_nav2_dir = get_package_share_directory("turtlebot3_navigation2")
    
    # Spawn the world and robot
    spawn_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(tb3_world_dir, "launch", "tb3_world.launch.py")
        ),
        launch_arguments={
            "x_pose": LaunchConfiguration("x_pose", default=0.0),
            "y_pose": LaunchConfiguration("y_pose", default=0.0),
        }.items(),
    )
    
    # For some reason, there is an error with starting both spawn world and nav
    # in this launch file without this delay ???
    spawn_world_delayed = TimerAction(period=3.0, actions=[spawn_world])

    # Start Nav2 with SLAM configuration
    nav2_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(tb3_nav2_dir, "launch", "navigation2.launch.py")
        ),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time", default="true"),
            "slam": "True",
            "map": "",
            "params_file": join("/params", "nav2_slam_params.yaml"),
            "use_composition": "False",
            "autostart": "True"
        }.items(),
    )

    # Replace the initial_pose_node with this new implementation
    initial_pose_pub = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='initial_pose_pub',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    # Spawn blocks
    spawn_blocks = Node(
        package="tb3_worlds",
        executable="block_spawner.py",
        name="block_spawner",
        parameters=[
            {"location_file": join(tb3_world_dir, "maps", "sim_house_locations.yaml")}
        ],
    )

    return LaunchDescription(
        [
            spawn_world_delayed,
            # Delay Nav2 start to ensure Gazebo and robot are ready
            TimerAction(
                period=5.0,
                actions=[nav2_slam]
            ),
            # Delay initial pose until Nav2 is ready
            TimerAction(
                period=10.0,
                actions=[initial_pose_pub]
            ),
            # Delay block spawning until everything else is ready
            TimerAction(
                period=12.0,
                actions=[spawn_blocks]
            )
        ]
    )
