import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from rclpy.qos import qos_profile_sensor_data
import cv2

class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_subscriber')

        self.bridge = CvBridge()
        self.count = 0
        
        self.subscription = self.create_subscription(
            Image,
            '/camera/color/image',
            self.listener_callback,
            qos_profile_sensor_data
        )
        
        self.get_logger().info('Image subscriber started, waiting for frames...')
        
    def listener_callback(self, msg):
        self.count += 1

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        cv2.imshow('Camera Feed', frame)
        cv2.waitKey(1)

        if self.count % 30 == 0:
            self.get_logger().info(f'Frame #{self.count} received')

def main(args=None):
    rclpy.init(args=args)
    node = ImageSubscriber()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()
    