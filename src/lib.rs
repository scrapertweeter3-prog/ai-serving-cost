//! Serving cost math for AI workloads.
//!
//! An API bill is a token count times a rate, minus whatever the cache
//! knocks off, plus a per-request floor. These functions compute that
//! math so an audit can restate the invoice instead of trusting it.

/// Dollar cost of a token count at a per-million-token rate.
///
/// ```
/// let c = ai_serving_cost::token_cost(1_000_000.0, 3.0);
/// assert!((c - 3.0).abs() < 1e-9);
/// ```
pub fn token_cost(tokens: f64, rate_per_million: f64) -> f64 {
    tokens / 1_000_000.0 * rate_per_million
}

/// Cost of one request when input, output, and per-request fees all land
/// on the same bill. Cache hits bill the discounted input rate.
///
/// ```
/// let r = ai_serving_cost::request_cost(10_000.0, 500.0, 3.0, 15.0, 0.3, 0.0005);
/// assert!((r - 0.029).abs() < 1e-9);
/// ```
pub fn request_cost(
    input_tokens: f64,
    output_tokens: f64,
    input_rate: f64,
    output_rate: f64,
    cache_share: f64,
    per_request: f64,
) -> f64 {
    let share = cache_share.clamp(0.0, 1.0);
    let in_cost = token_cost(input_tokens, input_rate) * (1.0 - share);
    let out_cost = token_cost(output_tokens, output_rate);
    in_cost + out_cost + per_request
}

/// Cache discount: dollars a cached share of input traffic saves at a
/// given volume, floored at zero when the share is nonsense.
///
/// ```
/// let s = ai_serving_cost::cache_savings(50_000_000.0, 3.0, 0.4);
/// assert!((s - 60.0).abs() < 1e-9);
/// ```
pub fn cache_savings(tokens: f64, input_rate: f64, cache_share: f64) -> f64 {
    let share = cache_share.clamp(0.0, 1.0);
    token_cost(tokens, input_rate) * share
}

/// Monthly bill for a workload: request cost times requests per day,
/// over a 30-day month.
///
/// ```
/// let m = ai_serving_cost::monthly_bill(0.029, 20_000.0);
/// assert!((m - 17_400.0).abs() < 1e-6);
/// ```
pub fn monthly_bill(cost_per_request: f64, requests_per_day: f64) -> f64 {
    cost_per_request * requests_per_day * 30.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rate_is_per_million_not_per_token() {
        assert!(token_cost(2_000_000.0, 3.0) > 5.9);
    }

    #[test]
    fn cache_share_lowers_input_cost() {
        let full = request_cost(10_000.0, 500.0, 3.0, 15.0, 0.0, 0.0005);
        let cached = request_cost(10_000.0, 500.0, 3.0, 15.0, 0.5, 0.0005);
        assert!(cached < full);
    }

    #[test]
    fn savings_vanish_at_zero_share() {
        assert!(cache_savings(1_000_000.0, 3.0, 0.0).abs() < 1e-12);
    }

    #[test]
    fn monthly_scales_linearly() {
        assert!(monthly_bill(0.046, 40_000.0) > monthly_bill(0.046, 20_000.0));
    }

    #[test]
    fn negative_share_is_clamped_not_negative_cost() {
        let r = request_cost(10_000.0, 0.0, 3.0, 15.0, -0.5, 0.0);
        assert!(r >= 0.0);
    }
}
