Project Overview:-

Temple Run Gesture Controller converts real-time webcam hand gestures into keyboard inputs for games (Temple Run or any game that accepts arrow-key input). It uses MediaPipe Hands to detect hand landmarks, OpenCV for video capture and visualization, and the keyboard library to send key events to the system.

This allows players to use hand poses and palm tilt to perform game actions like jump, slide, dodge left, dodge right — simulating phone tilt and swipe controls on a laptop.

Features:-
* Real-time hand landmark detection (MediaPipe Hands)
* Gesture recognition for:
* Jump (index finger up)
* Slide (both fists)
* Move left / Move right (single-fist detection)
* Tilt left / Tilt right ('A' key for left, 'D' key for right)
* Cooldown mechanism to avoid gesture spamming
* On-screen debug overlay showing detected action and roll angles
* Easy-to-tune thresholds and cooldowns

Requirements:-
* Python 3.8+ (3.10 recommended)
* webcam (built-in or USB)

* Libraries:
    ->opencv-python
    ->mediapipe
    ->numpy
    ->keyboard
* Optional: virtualenv
Install libraries with:-
"pip install opencv-python mediapipe numpy keyboard"

Installation:-
1. Clone the repository or copy the script into a working folder.
2. Create and activate a virtual environment (optional but recommended):
"python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate"
3. Install dependencies:
"pip install -r requirements.txt
# or
pip install opencv-python mediapipe numpy keyboard"
4. Run the script:
"python temple_run_gesture_controller.py"

Running the Project:-
When you run the script:
* The webcam opens and a window appears showing the camera feed.
* MediaPipe draws hand landmarks and connections.
* The overlay displays:
  ->ACTION: <action> when a gesture triggers
  ->Gesture events are translated to arrow-key presses (up, down, left, right) via the keyboard library.
* Exit by pressing ESC in the OpenCV window.

How It Works — Technical Details
1. MediaPipe Hands
* MediaPipe returns 21 normalized 2D landmarks per detected hand:
* Landmarks include fingertips, joints, and palm points.
* Coordinates are normalized to [0,1] relative to the image size.
2. Finger State Detection
* get_finger_states(hand_landmarks) compares fingertip y-coordinate to the PIP joint y-coordinate:
* If tip.y < pip.y → finger is considered up (visible as higher on the frame; note: frame is flipped).
* Thumb state uses x-coordinate comparison between TIP and IP because thumb opens sideways.
3. Gesture Rules
* Simple boolean logic derived from finger states determines gestures:
* Eg. thumb up + others down → Jump.
* sum(finger_states[1:]) == 0 → all non-thumb fingers down (fist).
4. Cooldown System
* A per-gesture counter prevents repeated triggers every frame.
* After triggering, the gesture cooldown counter is set (e.g., cooldown_frames=10) and decremented each frame.
5. Keyboard Integration
* keyboard.send('<key>') triggers system-level key events for arrow keys.
* This is what actually interacts with the target game (Temple Run running in a window).

Performance Tips:-
* Use 640×480 or 320×240 if you need higher framerate.
* Close other applications that compete for CPU/GPU.
* If jitter persists, increase smoothing factor and cooldown frames.
* If using multiple hands, averaging both hands' roll (if both visible) can increase robustness.

Extending / Customizing:-
* Different key mappings: Replace keyboard.send('left') with other keys or custom events.
* Single-hand mode: Limit to left or right hand only and change gesture logic accordingly.
* Additional gestures: Build patterns using combinations of extended fingers (e.g., two-finger swipe detection by observing movement of fingertip positions across frames).
* Game integration: Instead of sending keys, use a socket or API to directly control a connected game engine (Unity/Unreal) if developing a custom game.

Limitations:-
* Tracking depends on camera view, lighting, and occlusions.
* Finger detection may fail for very fast movement or extreme orientations.
* keyboard library may need OS-specific permissions for global key events.
* Not a perfect replacement for gyroscope tilt; tilt is inferred from palm roll and can be less precise than real IMU sensors.