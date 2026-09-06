with open('frensense-engine/src/minhash.rs', 'r') as f:
    content = f.read()

new_metrics = """
pub fn containment_sorted(a: &[u64], b: &[u64]) -> f64 {
    if a.is_empty() {
        return 1.0;
    }
    if b.is_empty() {
        return 0.0;
    }
    let intersection = intersect_sorted(a, b);
    intersection as f64 / a.len() as f64
}

pub fn size_ratio(a_len: usize, b_len: usize) -> f64 {
    if a_len == 0 && b_len == 0 {
        return 1.0;
    }
    if a_len == 0 || b_len == 0 {
        return 0.0;
    }
    let min_len = std::cmp::min(a_len, b_len);
    let max_len = std::cmp::max(a_len, b_len);
    min_len as f64 / max_len as f64
}
"""

# Insert new metrics after overlap_coefficient_sorted
idx = content.find("pub fn overlap_coefficient_sorted")
end_idx = content.find("}", idx) + 1
if idx != -1:
    content = content[:end_idx] + "\n" + new_metrics + content[end_idx:]

with open('frensense-engine/src/minhash.rs', 'w') as f:
    f.write(content)
