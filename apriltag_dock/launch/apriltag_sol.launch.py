from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

from launch_ros.actions import Node



def launch_setup(context, *args, **kwargs):
    paused = LaunchConfiguration("paused")
    gui = LaunchConfiguration("gui")
    use_sim_time = LaunchConfiguration("use_sim_time")
    debug = LaunchConfiguration("debug")
    headless = LaunchConfiguration("headless")
    verbose = LaunchConfiguration("verbose")
    namespace = LaunchConfiguration("namespace")
    world_name = LaunchConfiguration("world_name")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    roll = LaunchConfiguration("roll")
    pitch = LaunchConfiguration("pitch")
    yaw = LaunchConfiguration("yaw")
    z_block = LaunchConfiguration("z_block")
    use_ned_frame = LaunchConfiguration("use_ned_frame")
    apriltag_share = get_package_share_directory('apriltag_ros')
    config = os.path.join(get_package_share_directory('apriltag_dock'), 'param', 'movus.yaml') 

    if world_name.perform(context) != "empty.sdf":
        world_name = LaunchConfiguration("world_name").perform(context)
        world_filename = f"{world_name}.world"
        world_filepath = PathJoinSubstitution(
            [FindPackageShare("drobot_worlds"), "worlds", world_filename]
        )
        gz_args = [world_filepath]
    else:
        gz_args = [world_name]

    if headless.perform(context) == "true":
        gz_args.append(" -s")
    if paused.perform(context) == "false":
        gz_args.append(" -r")
    if debug.perform(context) == "true":
        gz_args.append(" -v ")
    if verbose.perform(context) == "true":
        gz_args.append(" -v ")

    object_name = LaunchConfiguration("object_name")
    use_sim = LaunchConfiguration("use_sim")

    # Include the first launch file
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("ros_gz_sim"),
                        "launch",
                        "gz_sim.launch.py",
                    ]
                )
            ]
        ),
        # DeclareLaunchArgument(
        #     "rviz",
        #     default_value="false",
        #     description="Flag to enable RViz",
        # ),
        launch_arguments=[
            ("gz_args", gz_args),
        ],
        condition=IfCondition(gui),
    )

    # Include the second launch file with model name
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("drobot_robot_models"),
                        "launch",
                        "upload_robot.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "gui": gui,
            "use_sim_time": use_sim_time,
            "namespace": namespace,
            "x": x,
            "y": y,
            "z": z,
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
            "use_ned_frame": use_ned_frame,
        }.items(),
    )
    
    # Include the third launch file with model name
    model_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("drobot_object_models"),
                        "launch",
                        "upload_object.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "object_name": object_name,
            "use_sim": use_sim,
            "z": z_block,

        }.items(),
    )
    
    # pkg_drobot_rviz = get_package_share_directory('drobot_rviz')
    
    # RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([FindPackageShare("drobot_rviz"), "rviz", "movus.rviz"])],
        # condition=IfCondition(LaunchConfiguration('rviz', default='true'))
    )
    
    # launch apriltag detection node
    apriltag_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(apriltag_share, 'launch', 'apriltag_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time
        }.items()
    )
    
    docking_node = Node(
        package='apriltag_dock',
        executable='controller',
        name='autodock_controller',
        output='screen',
        parameters = [config])
    
    
    # custom_plugin = Node(
    #     package='apriltag_dock',
    #     executable='tf_plugin',
    #     name='custom_tf_plugin',
    #     output='screen',)
    
    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/model/movus/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
                   '/model/movus/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
                   '/camera/image@sensor_msgs/msg/Image@gz.msgs.Image',
                   '/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
                   '/world/empty/model/movus/link/camera_depth_frame/sensor/camera_with_intrinsics_tag/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
                   '/world/empty/model/movus/link/camera_depth_frame/sensor/camera_with_intrinsics_tag/depth_image@sensor_msgs/msg/Image@gz.msgs.Image',
                   '/world/empty/model/movus/link/camera_depth_frame/sensor/camera_with_intrinsics_tag/depth_image/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
                   '/model/movus/pose@geometry_msgs/msg/PoseArray@gz.msgs.Pose_V'],
            
        parameters=[{'qos_overrides./model/movus.subscriber.reliability': 'reliable'}],
        output='screen'
    )

    include = [gz_sim_launch, robot_launch, model_launch, rviz, bridge, docking_node, apriltag_launch]

    return include


def generate_launch_description():
    
    # Declare the launch arguments with default values
    args = [
        DeclareLaunchArgument(
            "paused",
            default_value="true",
            description="Start the simulation paused",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Flag to enable the gazebo gui",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Flag to indicate whether to use simulation time",
        ),
        DeclareLaunchArgument(
            "debug",
            default_value="false",
            description="Flag to enable the gazebo debug flag",
        ),
        DeclareLaunchArgument(
            "headless",
            default_value="false",
            description="Flag to enable the gazebo headless mode",
        ),
        DeclareLaunchArgument(
            "verbose",
            default_value="0",
            description="Adjust level of console verbosity",
        ),
        DeclareLaunchArgument(
            "world_name",
            default_value="empty.sdf",
            description="Gazebo world file to launch",
        ),
        DeclareLaunchArgument(
            "namespace",
            default_value="movus",
            description="Namespace",
        ),
        DeclareLaunchArgument(
            "x",
            default_value="0.0",
            description="Initial x position",
        ),
        DeclareLaunchArgument(
            "y",
            default_value="0.0",
            description="Initial y position",
        ),
        DeclareLaunchArgument(
            "z",
            default_value="0.0",
            description="Initial z position",
        ),
        DeclareLaunchArgument(
            "roll",
            default_value="0.0",
            description="Initial roll angle",
        ),
        DeclareLaunchArgument(
            "pitch",
            default_value="0.0",
            description="Initial pitch angle",
        ),
        DeclareLaunchArgument(
            "yaw",
            default_value="3.14",
            description="Initial yaw angle",
        ),
        DeclareLaunchArgument(
            "use_ned_frame",
            default_value="false",
            description="Flag to indicate whether to use the north-east-down frame",
        ),
        DeclareLaunchArgument(
            "object_name",
            default_value="apriltag_block",
            description="Name of the object model to load",
        ),
        DeclareLaunchArgument(
            "z_block",
            default_value="1.00",
            description="Initial z position for apriltag_block",
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="true",
            description="Flag to indicate whether to use simulation",
        ),
    ]

    return LaunchDescription(args + [OpaqueFunction(function=launch_setup)])
