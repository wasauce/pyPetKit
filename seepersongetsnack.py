#!/usr/bin/env python3

from pathlib import Path
import cv2
import depthai as dai
import numpy as np
import time
import argparse
import datetime
import time

from pypetkit import PetKitAPI
from settings import (
    API_USERNAME,
    API_PASSWORD,
    API_COUNTRY_CODE,
    API_LOCALE_CODE,
    API_TIMEZONE,
)

from pprint import pprint

petkit_api = PetKitAPI(
    API_USERNAME, API_PASSWORD, API_COUNTRY_CODE, API_LOCALE_CODE, API_TIMEZONE
)

petkit_api.request_token()



labelMap = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow",
            "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

nnPathDefault = str((Path(__file__).parent / Path('./models/mobilenet-ssd_openvino_2021.4_6shave.blob')).resolve().absolute())
parser = argparse.ArgumentParser()
parser.add_argument('nnPath', nargs='?', help="Path to mobilenet detection network blob", default=nnPathDefault)
parser.add_argument('-ff', '--full_frame', action="store_true", help="Perform tracking on full RGB frame", default=False)

args = parser.parse_args()

fullFrameTracking = args.full_frame


def main():
    # Create pipeline
    pipeline = dai.Pipeline()

    # Define sources and outputs
    camRgb = pipeline.create(dai.node.ColorCamera)
    detectionNetwork = pipeline.create(dai.node.MobileNetDetectionNetwork)
    objectTracker = pipeline.create(dai.node.ObjectTracker)

    xlinkOut = pipeline.create(dai.node.XLinkOut)
    trackerOut = pipeline.create(dai.node.XLinkOut)

    xlinkOut.setStreamName("preview")
    trackerOut.setStreamName("tracklets")

    # Properties
    camRgb.setPreviewSize(300, 300)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setInterleaved(False)
    camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    camRgb.setFps(40)

    # testing MobileNet DetectionNetwork
    detectionNetwork.setBlobPath(args.nnPath)
    detectionNetwork.setConfidenceThreshold(0.5)
    detectionNetwork.input.setBlocking(False)

    objectTracker.setDetectionLabelsToTrack([15])  # track only person
    # possible tracking types: ZERO_TERM_COLOR_HISTOGRAM, ZERO_TERM_IMAGELESS, SHORT_TERM_IMAGELESS, SHORT_TERM_KCF
    objectTracker.setTrackerType(dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM)
    # take the smallest ID when new object is tracked, possible options: SMALLEST_ID, UNIQUE_ID
    objectTracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.SMALLEST_ID)

    # Linking
    camRgb.preview.link(detectionNetwork.input)
    objectTracker.passthroughTrackerFrame.link(xlinkOut.input)

    if fullFrameTracking:
        camRgb.video.link(objectTracker.inputTrackerFrame)
    else:
        detectionNetwork.passthrough.link(objectTracker.inputTrackerFrame)

    detectionNetwork.passthrough.link(objectTracker.inputDetectionFrame)
    detectionNetwork.out.link(objectTracker.inputDetections)
    objectTracker.out.link(trackerOut.input)

    # Connect to device and start pipeline
    with dai.Device(pipeline) as device:

        preview = device.getOutputQueue("preview", 4, False)
        tracklets = device.getOutputQueue("tracklets", 4, False)

        startTime = time.monotonic()
        counter = 0
        fps = 0
        frame = None
        past_dt = None

        while (True):
            imgFrame = preview.get()
            track = tracklets.get()

            counter += 1
            current_time = time.monotonic()
            if (current_time - startTime) > 1:
                fps = counter / (current_time - startTime)
                counter = 0
                startTime = current_time

            color = (255, 0, 0)
            frame = imgFrame.getCvFrame()
            trackletsData = track.tracklets
            for t in trackletsData:
                roi = t.roi.denormalize(frame.shape[1], frame.shape[0])
                x1 = int(roi.topLeft().x)
                y1 = int(roi.topLeft().y)
                x2 = int(roi.bottomRight().x)
                y2 = int(roi.bottomRight().y)

                try:
                    label = labelMap[t.label]
                except:
                    label = t.label
                print(f'label: {label}. current_time: {current_time}')

                if str(label) == 'person':
                    now = datetime.datetime.utcnow()
                    if past_dt:
                        test_dt = past_dt + datetime.timedelta(seconds=60)
                        if now > test_dt:
                            past_dt = now
                            # give a snack
                            print(f'Give snack')
                            petkit_api.send_api_request(
                                "d4/saveDailyFeed", params={"deviceId": 10020257, "amount": 10, "time": -1}
                            )
                    else:
                        past_dt = now
                        # give a snack
                        print(f'Give snack')
                        petkit_api.send_api_request(
                            "d4/saveDailyFeed", params={"deviceId": 10020257, "amount": 10, "time": -1}
                        )

                cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                cv2.putText(frame, f"ID: {[t.id]}", (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                cv2.putText(frame, t.status.name, (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)

            cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4,
                        color)

            cv2.imshow("tracker", frame)

            if cv2.waitKey(1) == ord('q'):
                break

if __name__ == "__main__":
    """
    """
    main()
