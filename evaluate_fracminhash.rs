use std::collections::HashSet;

// A simple script to evaluate FracMinHash scale factors.
// Simulates the number of hashes retained for small fingerprints.

fn main() {
    // Simulate a small snippet yielding 8, 15, and 30 unique hashes
    let sizes = [8, 15, 30, 100, 1000];
    let scales = [10, 50, 100, 500];

    for &size in &sizes {
        println!("Snippet Size (unique hashes): {}", size);
        for &scale in &scales {
            let threshold = u64::MAX / scale;
            let mut expected_retained = 0.0;
            // Statistically, the fraction of hashes below threshold is 1/scale.
            expected_retained = (size as f64) / (scale as f64);
            
            println!("  Scale {}: Expected retained hashes = {:.2}", scale, expected_retained);
        }
    }
}
