import cv2
import numpy as np
from ultralytics import YOLO
from mail_alert import send_email_alert  # Import from the email module

# Load YOLOv5 Model
model = YOLO("yolov5s.pt")
model.conf = 0.2  # Lowered to detect more objects

# Load Video
video_path = "videoplayback.webm"
cap = cv2.VideoCapture(video_path)

# Get Video Properties
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define Output Video Writer
out = cv2.VideoWriter("output.mp4", cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

# Motion Detection Variables
prev_frame = None
motion_threshold = 10  # General motion threshold
object_motion_threshold = 35  # Motion threshold for "person"
motion_counter = 0  # Counter for general motion events

# YOLO Settings
YOLO_PROCESS_EVERY = 3  # Process YOLO every 3 frames
frame_count = 0
COUNTER_THRESHOLD = 5  # Send email only after 5 general motion events

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Convert to grayscale for motion detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if prev_frame is None:
        prev_frame = gray
        continue

    # Compute frame difference with smoothing
    diff = cv2.absdiff(prev_frame, gray)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)  # Reduce noise
    prev_frame = gray
    motion_value = np.sum(diff) / (frame_width * frame_height)  # Normalized motion
    print(f"Frame {frame_count} - General Motion Value: {motion_value:.2f}")

    # Check general motion and update counter
    if motion_value > motion_threshold:
        motion_counter += 1
        print(f"⚠️ General motion event detected (Counter: {motion_counter}) - Running YOLO")

        # Highlight frame with red border for high motion
        cv2.rectangle(frame, (0, 0), (frame_width - 1, frame_height - 1), (0, 0, 255), 5)

        # Send email if counter exceeds threshold
        if motion_counter >= COUNTER_THRESHOLD:
            print(f"⚠️ Sustained Motion Confirmed: Sending alert (Counter: {motion_counter})")
            reason = f"Theft detected - sustained high motion detected (Motion Value: {motion_value:.2f})"
            send_email_alert(reason)  # Call the email function from the module
            motion_counter = 0  # Reset counter after email

        # Run YOLO for object detection (optional visualization)
        if frame_count % YOLO_PROCESS_EVERY == 0:
            yolo_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model(yolo_frame)

            if len(results) == 0 or len(results[0].boxes) == 0:
                print("No objects detected by YOLO")
            else:
                print(f"Detected {len(results[0].boxes)} objects")

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = model.names[int(box.cls[0])]
                    confidence = box.conf[0]

                    # Clamp coordinates to frame boundaries
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(frame_width, x2), min(frame_height, y2)

                    # Draw bounding boxes for ALL detected objects
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Optional: Log ROI motion for "person"
                    if label == "person":
                        roi_diff = diff[y1:y2, x1:x2]  # Motion in bounding box
                        if roi_diff.size > 0 and (x2 - x1) > 10 and (y2 - y1) > 10:
                            roi_motion = np.sum(roi_diff) / ((x2 - x1) * (y2 - y1))
                            print(f"ROI Motion for {label} at ({x1}, {y1}, {x2}, {y2}): {roi_motion:.2f}")
                            if roi_motion >= object_motion_threshold:
                                print(f"🔍 Person motion high ({roi_motion:.2f} >= {object_motion_threshold})")
                            else:
                                print(f"🔍 Person motion low ({roi_motion:.2f} < {object_motion_threshold})")
                        else:
                            print(f"⚠️ Skipping ROI motion check: ROI too small or invalid ({x2-x1}, {y2-y1})")

    # Save & Display Video
    out.write(frame)
    cv2.imshow("Robbery Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()