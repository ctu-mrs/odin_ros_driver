cmake_minimum_required(VERSION 3.16)
project(odin_ros_driver)

# Explicitly define ROS2 for any macros relying on it
add_definitions(-DROS2)
message(STATUS "Defining ROS2")

# Platform detection
execute_process(
    COMMAND uname -m
    OUTPUT_VARIABLE ARCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(ARCH STREQUAL "x86_64")
    set(TARGET_PLATFORM "x86")
    message(STATUS "Detected x86_64 architecture")
elseif(ARCH MATCHES "arm|aarch64")
    set(TARGET_PLATFORM "arm")
    message(STATUS "Detected ARM architecture: ${ARCH}")
else()
    message(WARNING "Unsupported architecture: ${ARCH}. Using default settings")
    set(TARGET_PLATFORM "unknown")
endif()

# Set library path
set(LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/lib")
message(STATUS "Library directory: ${LIB_DIR}")

# Set library name based on platform
if(TARGET_PLATFORM STREQUAL "arm")
    set(LYD_HOST_API_LIB_NAME "lydHostApi_arm")
else()
    set(LYD_HOST_API_LIB_NAME "lydHostApi_amd")
endif()

# Find precompiled lydHostApi library
find_library(LYD_HOST_API_LIB
    NAMES
        ${LYD_HOST_API_LIB_NAME}
        lib${LYD_HOST_API_LIB_NAME}.a
        lib${LYD_HOST_API_LIB_NAME}.so
    PATHS ${LIB_DIR}
    NO_DEFAULT_PATH
)

if(LYD_HOST_API_LIB)
    message(STATUS "Found lydHostApi library: ${LYD_HOST_API_LIB}")
else()
    file(GLOB LIB_FILES "${LIB_DIR}/lib${LYD_HOST_API_LIB_NAME}.*")
    if(LIB_FILES)
        message(STATUS "Found library files: ${LIB_FILES}")
        set(LYD_HOST_API_LIB ${LIB_FILES})
    else()
        message(FATAL_ERROR "Could not find precompiled lydHostApi library in ${LIB_DIR}")
    endif()
endif()

# set the correct standards
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find common non-ROS dependencies
find_package(PkgConfig REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(PCL REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(mrs_lib REQUIRED)
find_package(image_transport REQUIRED)
pkg_check_modules(LIBUSB REQUIRED libusb-1.0)

# Find ROS2 specific packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(message_filters REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Shared include directories
include_directories(
    include
    ${EIGEN3_INCLUDE_DIRS}
    ${OpenCV_INCLUDE_DIRS}
    ${PCL_INCLUDE_DIRS}
    ${yaml-cpp_INCLUDE_DIR}
    ${LIBUSB_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Shared library list
set(COMMON_LIBS
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    ${yaml-cpp_LIBRARIES}
    ${OPENSSL_LIBRARIES}
    ${LIBUSB_LIBRARIES}
    pthread
    rt
    ${CMAKE_DL_LIBS}
    ${LYD_HOST_API_LIB}
)

# ---- AE/AWB debug services ----
rosidl_generate_interfaces(${PROJECT_NAME}
    "srv/GetAe.srv"
    "srv/GetAwb.srv"
    "srv/SetAe.srv"
    "srv/SetAwb.srv"
)

# ===== Targets Configuration =====

# host_sdk_sample
add_executable(host_sdk_sample
    src/host_sdk_sample.cpp
    src/yaml_parser.cpp
    src/rawCloudRender.cpp
    src/camera_pose_visualization.cpp
)

target_link_libraries(host_sdk_sample
    ${COMMON_LIBS}
    yaml-cpp
    usb-1.0
    mrs_lib::mrs_lib
)

rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(host_sdk_sample "${cpp_typesupport_target}")

ament_target_dependencies(host_sdk_sample
    rclcpp std_msgs sensor_msgs nav_msgs visualization_msgs
    cv_bridge image_transport tf2 tf2_ros geometry_msgs
    tf2_geometry_msgs ament_index_cpp
)

# pointcloud_depth_converter_ros2
add_library(pointcloud_depth_converter_ros2 src/pointcloud_depth_converter.cpp)
target_link_libraries(pointcloud_depth_converter_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    mrs_lib::mrs_lib
)

# depth_image_ros2_node_lib
add_library(depth_image_ros2_node_lib src/depth_image_ros2_node.cpp)
target_link_libraries(depth_image_ros2_node_lib
    pointcloud_depth_converter_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    mrs_lib::mrs_lib
)
ament_target_dependencies(depth_image_ros2_node_lib
    rclcpp sensor_msgs std_msgs cv_bridge image_transport pcl_conversions message_filters
)

# pcd2depth_ros2_node
add_executable(pcd2depth_ros2_node src/pcd2depth_ros2.cpp)
target_link_libraries(pcd2depth_ros2_node
    depth_image_ros2_node_lib
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    yaml-cpp
    mrs_lib::mrs_lib
)
ament_target_dependencies(pcd2depth_ros2_node
    rclcpp sensor_msgs std_msgs cv_bridge image_transport pcl_conversions message_filters
)

# cloud_reprojector_ros2
add_library(cloud_reprojector_ros2 src/cloud_reprojector.cpp)
target_compile_definitions(cloud_reprojector_ros2 PRIVATE ROS2)
target_link_libraries(cloud_reprojector_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    mrs_lib::mrs_lib
)

# cloud_reprojection_ros2_node
add_executable(cloud_reprojection_ros2_node src/cloud_reprojection_ros.cpp)
target_compile_definitions(cloud_reprojection_ros2_node PRIVATE ROS2)
target_link_libraries(cloud_reprojection_ros2_node
    cloud_reprojector_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    yaml-cpp
    mrs_lib::mrs_lib
)
ament_target_dependencies(cloud_reprojection_ros2_node
    rclcpp sensor_msgs nav_msgs cv_bridge image_transport pcl_conversions message_filters
)

# image_overlay_node
add_executable(image_overlay_node src/image_overlay_node.cpp)
target_compile_definitions(image_overlay_node PRIVATE ROS2)
target_link_libraries(image_overlay_node
    ${OpenCV_LIBS}
    mrs_lib::mrs_lib
)

ament_target_dependencies(image_overlay_node
    rclcpp sensor_msgs cv_bridge image_transport message_filters
)

# ARM platform specific link options
if(TARGET_PLATFORM STREQUAL "arm")
    set_target_properties(host_sdk_sample PROPERTIES
        LINK_FLAGS "-Wl,--no-as-needed -Wl,--rpath=${LIB_DIR}"
    )
    message(STATUS "Adding ARM-specific link options and RPATH")
endif()

# ===== Installation Rules =====

install(TARGETS
    host_sdk_sample
    pcd2depth_ros2_node
    cloud_reprojection_ros2_node
    image_overlay_node
    depth_image_ros2_node_lib
    pointcloud_depth_converter_ros2
    cloud_reprojector_ros2
    EXPORT export_${PROJECT_NAME}
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(FILES package.xml DESTINATION share/${PROJECT_NAME})

install(DIRECTORY include/ DESTINATION include)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch_ROS2")
    install(DIRECTORY launch_ROS2/ DESTINATION share/${PROJECT_NAME}/launch)
    message(STATUS "Installing launch_ROS2 directory to share/${PROJECT_NAME}/launch")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
    install(DIRECTORY launch/ DESTINATION share/${PROJECT_NAME}/launch)
    message(STATUS "Installing launch directory to share/${PROJECT_NAME}/launch")
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/config")
    install(DIRECTORY config/ DESTINATION share/${PROJECT_NAME}/config)
endif()

ament_export_targets(export_${PROJECT_NAME})

ament_export_dependencies(
    rclcpp std_msgs sensor_msgs nav_msgs visualization_msgs cv_bridge
    image_transport pcl_conversions message_filters tf2 tf2_ros
    geometry_msgs tf2_geometry_msgs ament_index_cpp
)

install(
  DIRECTORY tmux
  USE_SOURCE_PERMISSIONS
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
