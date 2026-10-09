#include <iostream>

int main() {
    std::cout << "INIT test" << std::endl;
    return 0;
}

// config
struct OuterLoopConfig {
    float kp = 3.5f;           // proportional gain
    float ki = 0.2f;           // integral gain
    float kd = 0.05f;          // derivative gain
    float maxR_cmd = 1.57f; // max target rate limit (rad/s, e.g. ~90 deg/s)
    float max_int = 0.3f;  // anti-windup clamping threshold
};
// data in
struct AttitudeState {
    float theta;     // current pitch  (rad)
    float phi;       // current roll  (rad)
    float psi;       // current yaw  (rad)
};
// target setpoints
struct GuidanceReference {
    float theta_tar; // desired pitch  (rad)
    float phi_tar;   // desired roll  (rad)
    float psi_tar;   // desired yaw  (rad)
};
// output
struct RateCommands {
    float omega_y_cmd; // target pitch rate (rad/s)
    float omega_x_cmd; // target roll rate (rad/s)
    float omega_z_cmd; // target yaw rate (rad/s)
};
// state variables maintained across execution frames
struct LoopState {
    float error_integral = 0.0f;
    float prev_error = 0.0f;
};
// error calculation
float computeAttitudeError(float ref, float current) {
    float error = ref - current;
    // Normalize angle difference between -PI and +PI to handle wrap-around
    while (error >  3.14159265f) error -= 6.2831853f;
    while (error < -3.14159265f) error += 6.2831853f;
    return error;
}

//



/**
 * @brief PID core algorithm for a single axis.
 * 
 * @param error The current tracking error (setpoint - actual).
 * @param dt Time step in seconds since last update.
 * @param cfg Reference to the PID configuration parameters.
 * @param state Reference to the loop state (integral and previous error).
 * @return The computed rate command for the axis (clamped to limits).
 */
float stepSingleAxis(float error, float dt, const OuterLoopConfig& cfg, LoopState& state) {
    // 1. Proportional Term
    float p_out = cfg.kp * error;

    // 2. Integral Term with Anti-Windup Clamping
    state.error_integral += error * dt;
    if (state.error_integral > cfg.max_int)  state.error_integral = cfg.max_int;
    if (state.error_integral < -cfg.max_int) state.error_integral = -cfg.max_int;
    float i_out = cfg.ki * state.error_integral;

    // 3. Derivative Term (Derivative of Error)
    float d_error = 0.0f;
    if (dt != 0.0f) {
        d_error = (error - state.prev_error) / dt;
    }
    float d_out = cfg.kd * d_error;
    state.prev_error = error;

    // Total Unclamped Rate Command
    float raw_rate_cmd = p_out + i_out + d_out;

    // 4. Output Saturation Limiter
    if (raw_rate_cmd > cfg.maxR_cmd)  return cfg.maxR_cmd;
    if (raw_rate_cmd < -cfg.maxR_cmd) return -cfg.maxR_cmd;
    
    return raw_rate_cmd;
}

//eci
class OuterLoopController {
public:
    OuterLoopController(const OuterLoopConfig& config) : cfg_(config) {}

    // main update execution call
    RateCommands update(const GuidanceReference& ref, const AttitudeState& actual, float dt) {
        RateCommands cmd;

        // calculate independent tracking errors for pitch & yaw
        float pitch_error = computeAttitudeError(ref.theta_tar, actual.theta);
        float yaw_error   = computeAttitudeError(ref.psi_tar, actual.psi);

        // compute commanded rates for the inner loop
        cmd.omega_y_cmd = stepSingleAxis(pitch_error, dt, cfg_, pitch_state_);
        cmd.omega_z_cmd = stepSingleAxis(yaw_error, dt, cfg_, yaw_state_);
        cmd.omega_x_cmd = 0.0f; // roll rate handled separately o/ kept zero

        return cmd;
    }

    void resetIntegrators() {
        pitch_state_ = LoopState();
        yaw_state_   = LoopState();
    }

private:
    OuterLoopConfig cfg_;
    LoopState pitch_state_;
    LoopState yaw_state_;
};

//exec guard(prevents int buildup)
enum class FlightPhase { PAD, POWERED_FLIGHT, COAST, RECOVERY };

void processOuterLoopFrame(FlightPhase phase, const AttitudeState& actual, float dt) {
    static OuterLoopConfig config;
    static OuterLoopController outer_loop(config);

    if (phase == FlightPhase::POWERED_FLIGHT) {
        GuidanceReference ref = {0.0f, 0.0f, 0.0f}; // e.g. Vertical gravity turn target
        RateCommands target_rates = outer_loop.update(ref, actual, dt);

        // Pass target_rates to inner rate loop...
    } else {
        outer_loop.resetIntegrators(); // Keep integrators zeroed out on pad/coast
    }
}
