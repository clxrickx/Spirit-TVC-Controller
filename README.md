# SPIRIT TVC CONTROLLER

## Architecture Overview:
The spirit TVC controller architecture consists of a basic nested control loop system, containing of an outer and inner loop. The outer loop extracts in-flight data including; rocket orientation(Euler x/y/z, degrees), rocket position relative to launch origin(x/y, metres), and rocket altitude relative to launch origin(z, metres). These variables are then processed and compared to the desired flight path route, where a correction angle and output is then calculated and sent to the inner loop. The inner loop runs at a faster loop speed and executes corrections made by the outer loop.

## Kinematic & Force Transformation Modules:
Once target pitch and angles/engine torque is determined and calculated, SPIRIT makes use of a direction cosine matrix(DCM) to convert engine torques into individual actuator angles. Then, the implicit gimbal roll constraint angle is calculated as a function of pitch and yaw angles to prevent kinematic errors caused by non-coplanar actuator mounting geometry.

## Control Laws:
Proportional-derivative control is used by the baseline attitude indicator to regulate pitch and yaw, while an integral gain is added for auto-trim and prevents steady-state errors caused by centre of gravity offsets, thrust asymmetries, mounting misalignment, etc.

