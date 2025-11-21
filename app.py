import cv2
import mediapipe as mp
import numpy as np
import math
import time
from pynput.keyboard import Controller, Key

# ----------------- Input setup (pynput) -----------------
kb = Controller()

def send_key(key_name, hold=0.08):
    """
    Send a real key press using pynput.
    key_name: "up","down","left","right" or a single character like "a","d"
    hold: seconds to hold the key down
    """
    specials = {
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
    }
    k = specials.get(key_name, None)
    try:
        if k is None:
            # assume a character key
            kb.press(key_name)
            time.sleep(hold)
            kb.release(key_name)
        else:
            kb.press(k)
            time.sleep(hold)
            kb.release(k)
    except Exception as e:
        print("[INPUT ERROR] failed to send key:", key_name, e)

# ----------------- Mediapipe setup -----------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.6)

cap = cv2.VideoCapture(0)

def get_finger_states(hand_landmarks):
    """
    Returns boolean list [Thumb, Index, Middle, Ring, Pinky]
    based on whether each finger is extended (True) or folded (False).
    """
    lm = hand_landmarks.landmark
    fingers = []

    # Thumb: compare tip x with mcp x to figure if thumb is open away from palm
    thumb_tip_x = lm[mp_hands.HandLandmark.THUMB_TIP].x
    thumb_mcp_x = lm[mp_hands.HandLandmark.THUMB_MCP].x
    fingers.append(abs(thumb_tip_x - thumb_mcp_x) > 0.03)  # True if thumb noticeably away

    # Other fingers: tip higher (y smaller) than pip => extended
    tips = [mp_hands.HandLandmark.INDEX_FINGER_TIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            mp_hands.HandLandmark.RING_FINGER_TIP,
            mp_hands.HandLandmark.PINKY_TIP]

    pips = [mp_hands.HandLandmark.INDEX_FINGER_PIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
            mp_hands.HandLandmark.RING_FINGER_PIP,
            mp_hands.HandLandmark.PINKY_PIP]

    for tip, pip in zip(tips, pips):
        fingers.append(lm[tip].y < lm[pip].y)

    return fingers  # [Thumb, Index, Middle, Ring, Pinky]

def detect_gesture(left_hand, right_hand):
    """
    Return one of: 'jump', 'left', 'right', 'slide_down', 'tilt_left', 'tilt_right', or None.
    Priority:
      1) jump (index-point)
      2) tilt gestures (4 fingers -> left, 3 fingers -> right) checked before fists
      3) both fists -> slide_down
      4) single-fist -> left/right (turn)
    left_hand/right_hand are lists [Thumb, Index, Middle, Ring, Pinky] or None.
    """

    def is_fist(hand):
        return (hand is not None) and (sum(hand[1:]) == 0)

    def is_index_only(hand):
        return (hand is not None) and (hand[1] and not any(hand[2:]))

    def extended_finger_count(hand):
        return 0 if hand is None else sum(hand[1:])  # count index..pinky (exclude thumb)

    # 1) Jump: index-only on either visible hand
    if is_index_only(left_hand) or is_index_only(right_hand):
        return "jump"

    # 2) Tilt gestures based on number of extended fingers (index..pinky)
    # Priority: 4-finger (left tilt) is checked before 3-finger (right tilt)
    left_count = extended_finger_count(left_hand)
    right_count = extended_finger_count(right_hand)

    if left_count == 4 or right_count == 4:
        return "tilt_left"
    if left_count == 3 or right_count == 3:
        return "tilt_right"

    # 3) Both fists -> slide_down
    if is_fist(left_hand) and is_fist(right_hand):
        return "slide_down"

    # 4) single-fist -> turns
    if is_fist(left_hand) and not is_fist(right_hand):
        return "right"
    if is_fist(right_hand) and not is_fist(left_hand):
        return "left"

    return None

# Cooldown to prevent spamming keys (added tilt keys)
gesture_cooldown = {"jump":0, "slide_down":0, "left":0, "right":0, "tilt_left":0, "tilt_right":0}
cooldown_frames = 8  # tweak as needed

# key mapping - change these to match your game's expected keys if necessary
KEY_MAP = {
    "jump": "up",
    "slide_down": "down",
    "left": "left",
    "right": "right",
    "tilt_left": "a",   # 4-fingers -> left tilt
    "tilt_right": "d",  # 3-fingers -> right tilt
}

print("[INFO] Starting. Make sure BlueStacks is focused (click inside the emulator).")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process original frame so Mediapipe handedness is consistent
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    left_hand = None
    right_hand = None
    action = None

    if result.multi_hand_landmarks and result.multi_handedness:
        for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            hand_label = result.multi_handedness[idx].classification[0].label  # 'Left' or 'Right'
            fingers = get_finger_states(hand_landmarks)
            if hand_label == "Left":
                left_hand = fingers
            else:
                right_hand = fingers
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Decide gesture
    gesture = detect_gesture(left_hand, right_hand)
    if gesture and gesture_cooldown.get(gesture, 0) == 0:
        key_to_send = KEY_MAP.get(gesture)
        if key_to_send:
            send_key(key_to_send)        # <- uses pynput now
            # little extra delay after sending to avoid overlapping gestures
            time.sleep(0.05)
        action = gesture
        gesture_cooldown[gesture] = cooldown_frames

    # Decrease cooldowns
    for key in gesture_cooldown:
        if gesture_cooldown[key] > 0:
            gesture_cooldown[key] -= 1

    # Flip for display (mirror so user sees selfie view)
    disp = cv2.flip(frame, 1)
    if action:
        cv2.putText(disp, f"ACTION: {action.upper()}", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    cv2.imshow("Temple Run Gesture Controller", disp)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
