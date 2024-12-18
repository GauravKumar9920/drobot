from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def generate_launch_description():
    object_name = LaunchConfiguration("object_name")
    use_sim = LaunchConfiguration("use_sim")
    z_block = LaunchConfiguration("z_block")

    args = [
        DeclareLaunchArgument(
            "object_name",
            default_value="model",
            description="Name of the object model to load",
        ),
        DeclareLaunchArgument(
            "use_sim",
            default_value="true",
            description="Flag to indicate whether to use simulation",
        ),
        DeclareLaunchArgument(
            "z_block",
            default_value="0.25",
            description="Initial z position for apriltag_block",
        ),
    ]

    description_file = PathJoinSubstitution(
        [
            FindPackageShare("drobot_object_models"),
            "description",
            object_name,
            "model.sdf",
        ]
    )

    gz_spawner = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", object_name, 
                   "-file", description_file,
                   "-z", z_block],
        output="both",
        condition=IfCondition(use_sim),
        parameters=[{"use_sim_time": use_sim}],
    )

    nodes = [gz_spawner]

    event_handlers = [
        RegisterEventHandler(
            OnProcessExit(target_action=gz_spawner, on_exit=LogInfo(msg="Model Uploaded"))
        )
    ]

    return LaunchDescription(args + nodes + event_handlers)
