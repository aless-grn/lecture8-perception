import time
import cv2
import rclpy

from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO

from perception_msgs.msg import Detection, DetectionArray


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        self.bridge = CvBridge()

        self.declare_parameter('image_topic', '/camera/color/image')
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.25)
        self.declare_parameter('view_image', True)

        image_topic = self.get_parameter('image_topic').value
        model_path = self.get_parameter('model_path').value
        self.conf_threshold = float(self.get_parameter('confidence_threshold').value)
        self.view_image = bool(self.get_parameter('view_image').value)

        self.model = YOLO(model_path)
        self.get_logger().info(f'Loaded YOLO model: {model_path}')

        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data
        )

        self.detection_pub = self.create_publisher(
            DetectionArray,
            '/detections',
            10
        )

        self.frame_count = 0
        self.total_inference_time = 0.0
        self.start_time = time.time()

        self.get_logger().info(f'Subscribed to {image_topic}')

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.get_logger().error(f'cv_bridge conversion failed: {e}')
            return

        t0 = time.time()
        results = self.model(frame, verbose=False)
        inference_time = time.time() - t0

        self.frame_count += 1
        self.total_inference_time += inference_time

        detection_array = DetectionArray()
        detection_array.header = msg.header

        annotated = frame.copy()

        if len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    conf = float(box.conf[0].item())
                    if conf < self.conf_threshold:
                        continue

                    cls_id = int(box.cls[0].item())
                    class_name = self.model.names[cls_id]

                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    det = Detection()
                    det.class_name = class_name
                    det.confidence = conf
                    det.x_min = x1
                    det.y_min = y1
                    det.x_max = x2
                    det.y_max = y2
                    detection_array.detections.append(det)

                    label = f'{class_name} {conf:.2f}'
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        annotated,
                        label,
                        (x1, max(y1 - 10, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2
                    )

        self.detection_pub.publish(detection_array)

        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        avg_latency_ms = (
            self.total_inference_time / self.frame_count * 1000.0
            if self.frame_count > 0 else 0.0
        )

        cv2.putText(
            annotated,
            f'FPS: {fps:.2f}',
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )
        cv2.putText(
            annotated,
            f'Latency: {inference_time * 1000.0:.1f} ms',
            (10, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )

        if self.view_image:
            cv2.imshow('YOLO Detections', annotated)
            cv2.waitKey(1)

        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f'Frames: {self.frame_count} | '
                f'Current latency: {inference_time * 1000.0:.1f} ms | '
                f'Average latency: {avg_latency_ms:.1f} ms | '
                f'FPS: {fps:.2f} | '
                f'Detections: {len(detection_array.detections)}'
            )

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()