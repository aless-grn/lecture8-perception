# PX4-Sim

Fully containerized PX4 Autopilot simulation environment with browser-based GUI access.

## What's Included

- **PX4 Autopilot** - Pre-built and ready to use
- **ROS 2 Jazzy** - Latest ROS 2 LTS release
- **Gazebo Harmonic** - Latest Gazebo simulator
- **ROS Gazebo Bridge** (`ros-jazzy-ros-gz-bridge`) - Bidirectional transport bridge between Gazebo and ROS
- **MAVROS** (`ros-jazzy-mavros`) - PX4 to ROS gateway
- **TigerVNC + NoVNC** - Browser-based desktop access
- **XFCE4 Desktop** - Full desktop environment

## Quick Start

### 1. Build the Images

```bash
# Build everything
./build.sh --all

# Or build step by step
./build.sh --base  # ROS 2 + Gazebo
./build.sh --full  # PX4 Autopilot + MAVROS + NoVNC
```

### 2. Run the Container

```bash
# Interactive mode (recommended)
docker-compose up

# Or detached mode
docker-compose up -d
docker attach px4_sitl
```

### 3. Access the GUI

You can access GUI applications in different ways depending on your operating system:

#### macOS

You can access the GUI via built-in **noVNC** using your browser:

- Open: http://localhost:6080/vnc.html
- Password: `1234`

#### Linux

You can use **X11 forwarding** by enabling the appropriate configuration in your `docker-compose.yml` file (uncomment or add the required lines).

```yaml
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw

    environment:
      #- DISPLAY=:1
      - DISPLAY=${DISPLAY}
```

### 4. Control Interface

You can control your vehicle in simulation using different ways:

#### Connect QGroundControl (optional)

This step is required only if you want to control the vehicle using a graphical user interface.

1. Install **QGroundControl** on your host machine:
   http://qgroundcontrol.com

2. Create a custom communication link with the following configuration:

   * Type: UDP
   * Port: `15871`
   * Server: `0.0.0.0:18570`

3. QGroundControl will automatically connect to:

   * `udp://localhost:18570`

#### Offboard mode (alternative)

Alternatively, you can control the vehicle in **offboard mode**. This mode bypasses certain PX4 safety constraints in **PX4 Autopilot** when running in SITL.

Run the following commands in the PX4 SITL console:

```bash
param set COM_ARM_WO_GPS 1
param set COM_RC_IN_MODE 4
param set NAV_DLL_ACT 0
param set NAV_RCL_ACT 0
param set COM_OBL_ACT 0
```

### 5. Run the Simulation

Requires three terminals. Start each in order and wait for it to initialize before proceeding.

**Terminal 1 - PX4 SITL + Gazebo**

Run PX4 SITL:

```bash
docker exec -it px4_sitl bash
cd /root/PX4-Autopilot
make px4_sitl gz_x500
```

You will see:
- Gazebo simulation with a quadcopter
- PX4 console showing startup messages
- Drone ready for commands!

**Terminal 2 - ROS Gazebo Bridge**

Run ROS Gazebo Bridge, below is an example on how to map relevant topics of depth camera from Gazebo to ROS:

```bash
docker exec -it px4_sitl bash
ros2 run ros_gz_bridge parameter_bridge
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image@gz.msgs.Image
/depth_camera@sensor_msgs/msg/Image@gz.msgs.Image
/depth_camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked
--ros-args
-r /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info:=/camera/color/camera_info
-r /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image:=/camera/color/image
-r /depth_camera:=/camera/depth/image
-r /depth_camera/points:=/camera/depth/points
```

**Terminal 3 - MAVROS**

Run MAVROS: 

```bash
docker exec -it px4_sitl bash
ros2 launch mavros px4.launch fcu_url:=udp://:14540@localhost:14557
```

### 6. Integrate a Local Workspace

To test a custom module in PX4 SITL, you can mount your local development workspace into the Docker container as a bind volume. This allows live access to your host-side code from within the simulation environment.

Add the following volume mapping to your `docker-compose.yml` file:

```yaml
    volumes:
      - /home/user/workspace:/root/workspace
```

This binds the host directory /home/user/workspace to /root/workspace inside the container, making your module directly available to PX4 SITL without needing to rebuild the image.

## Usage Examples

### Start/Stop

```bash
# Start (interactive)
docker-compose up

# Start (background)
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f
```

### Attach/Detach

```bash
# Attach to running container
docker attach px4_sitl

# Detach without stopping: Ctrl+P, Ctrl+Q

# Or use exec for new shell
docker exec -it px4_sitl bash
```

### Multiple Terminal Windows

```bash
# Start container
docker-compose up -d

# Terminal 1: Run PX4
docker exec -it px4_sitl bash
cd /root/PX4-Autopilot
make px4_sitl gz_x500

# Terminal 2: Monitor ROS topics
docker exec -it px4_sitl bash
ros2 topic list
ros2 topic echo /mavros/altitude

# Terminal 3: Build custom packages
docker exec -it px4_sitl bash
cd /root/ros2_ws
colcon build
```

### Try Different Vehicles

See full list of vehicles [here](https://docs.px4.io/main/en/sim_gazebo_gz/vehicles).

```bash
# X500 Quadcopter
make px4_sitl gz_x500

# RC Cessna
make px4_sitl gz_rc_cessna

# Ackermann Rover
make px4_sitl gz_rover_ackermann
```

## Network Ports

| Port | Service |
|------|---------|
| 5901 | VNC server |
| 6080 | NoVNC web interface |
| 14550/udp | PX4 MAVLink (QGroundControl) |
| 18570/udp | Local UDP port used when PX4 communicates inside container/VM setups |

## Acknowledgement

- [PX4 Autopilot Documentation](https://docs.px4.io/)
- [ROS 2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic/)
- [ROS Gazebo Bridge](https://github.com/gazebosim/ros_gz/tree/ros2/ros_gz_bridge)
- [MAVROS](https://github.com/mavlink/mavros)
- [QGroundControl](http://qgroundcontrol.com)
- [TigerVNC Documentation](https://tigervnc.org/)


**Happy Simulating!** 🚁