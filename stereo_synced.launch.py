# -----------------------------------------------------------------------------
# Copyright 2022 Bernd Pfrommer <bernd.pfrommer@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument as LaunchArg
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration as LaunchConfig
from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


primary_camera_params = {
    'debug': False,
    'compute_brightness': True,
    'dump_node_map': False,
    'adjust_timestamp': True,
    'pixel_format': 'BGR8',
    'gain_auto': 'Continuous',
    'exposure_auto': 'Continuous',
    'line1_selector': 'Line1',
    'line1_linemode': 'Output',
    'line2_selector': 'Line2',
    'line2_v33enable': True,
    'trigger_selector': 'FrameStart',
    'trigger_mode': 'Off',
    'chunk_mode_active': True,
    'chunk_selector_frame_id': 'FrameID',
    'chunk_enable_frame_id': True,
    'chunk_selector_exposure_time': 'ExposureTime',
    'chunk_enable_exposure_time': True,
    'chunk_selector_gain': 'Gain',
    'chunk_enable_gain': True,
    'chunk_selector_timestamp': 'Timestamp',
    'chunk_enable_timestamp': True,
}

secondary_camera_params = {
    'debug': False,
    'compute_brightness': True,
    'dump_node_map': False,
    'adjust_timestamp': True,
    'pixel_format': 'BGR8',
    'gain_auto': 'Continuous',
    'exposure_auto': 'Continuous',
    'line3_selector': 'Line3',
    'line3_linemode': 'Input',
    'trigger_selector': 'FrameStart',
    'trigger_mode': 'On',
    'trigger_source': 'Line3',
    'trigger_overlap': 'ReadOut',
    'chunk_mode_active': True,
    'chunk_selector_frame_id': 'FrameID',
    'chunk_enable_frame_id': True,
    'chunk_selector_exposure_time': 'ExposureTime',
    'chunk_enable_exposure_time': True,
    'chunk_selector_gain': 'Gain',
    'chunk_enable_gain': True,
    'chunk_selector_timestamp': 'Timestamp',
    'chunk_enable_timestamp': True,
}

def make_primary_camera_node(name,camera_type, serial):
    parameter_file = PathJoinSubstitution(
        [FindPackageShare('spinnaker_camera_driver'), 'config',
         camera_type + '.yaml'])


    node = ComposableNode(
        package='spinnaker_camera_driver',
        plugin='spinnaker_camera_driver::CameraDriver',
        name=name,
        parameters=[primary_camera_params, 
                    {'parameter_file': parameter_file,
                    'serial_number': serial}],
        remappings=[('~/control', '/exposure_control/control')],
        extra_arguments=[{'use_intra_process_comms': True}]
    )
    return node

def make_secondary_camera_node(name, camera_type,serial):
    parameter_file = PathJoinSubstitution(
        [FindPackageShare('spinnaker_camera_driver'), 'config',
         camera_type + '.yaml'])

    node = ComposableNode(
        package='spinnaker_camera_driver',
        plugin='spinnaker_camera_driver::CameraDriver',
        name=name,
        parameters=[secondary_camera_params, 
                    {'parameter_file': parameter_file,
                    'serial_number': serial}],
        remappings=[('~/control', '/exposure_control/control')],
        extra_arguments=[{'use_intra_process_comms': True}]
    )
    return node

def launch_setup(context, *args, **kwargs):
    container = ComposableNodeContainer(
        name='stereo_camera_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            make_primary_camera_node(LaunchConfig('cam_0_name').perform(context),
                                    LaunchConfig('cam_0_type').perform(context),                        
                                     LaunchConfig('cam_0_serial').perform(context)),
            make_secondary_camera_node(LaunchConfig('cam_1_name').perform(context),
                                       LaunchConfig('cam_0_type').perform(context),    
                                       LaunchConfig('cam_1_serial').perform(context)),
            ComposableNode(
                package='cam_sync_ros2',
                plugin='cam_sync_ros2::CamSync',
                name='sync',
                parameters=[],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                package='exposure_control_ros2',
                plugin='exposure_control_ros2::ExposureControl',
                name='exposure_control',
                parameters=[{'cam_name': LaunchConfig('cam_0_name').perform(context),
                             'max_gain': 20.0,
                             'gain_priority': False,
                             'brightness_target': 100,
                             'max_exposure_time': 9500.0,
                             'min_exposure_time': 1000.0}],
                remappings=[('~/meta', ['/', LaunchConfig('cam_0_name').perform(context), '/meta'])],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
        ],
        output='screen',
    )
    return [container]


def generate_launch_description():
    """Create composable node by calling opaque function."""
    return LaunchDescription([
        LaunchArg('cam_0_name', default_value=['right_flir_camera'],
                  description='camera name (ros node name) of camera 0'),
        LaunchArg('cam_1_name', default_value=['left_flir_camera'],
                  description='camera name (ros node name) of camera 1'),
        LaunchArg('cam_0_type', default_value='blackfly_s',
                  description='type of camera 0'),
        LaunchArg('cam_1_type', default_value='blackfly_s',
                  description='type of camera 1'),
        LaunchArg('cam_0_serial', default_value="22092309",
                  description='FLIR serial number of camera 0 (in quotes!!)'),
        LaunchArg('cam_1_serial', default_value="22092307",
                  description='FLIR serial number of camera 1 (in quotes!!)'),
        OpaqueFunction(function=launch_setup)
        ])
