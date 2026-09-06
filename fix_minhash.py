import re

filepath = 'frensense-engine/src/minhash.rs'
with open(filepath, 'r') as f:
    content = f.read()

# We need to move the nested functions out.
# Find overlap_coefficient_sorted
start = content.find('pub fn overlap_coefficient_sorted')
end = content.find('    let intersection = intersect_sorted(a, b);\n    let min_len = std::cmp::min(a.len(), b.len());\n    intersection as f64 / min_len as f64\n}', start)
end_bracket = end + len('    let intersection = intersect_sorted(a, b);\n    let min_len = std::cmp::min(a.len(), b.len());\n    intersection as f64 / min_len as f64\n}')

new_fns = """pub fn overlap_coefficient_sorted(a: &[u64], b: &[u64]) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 1.0;
    }
    if a.is_empty() || b.is_empty() {
        return 0.0;
    }
    let intersection = intersect_sorted(a, b);
    let min_len = std::cmp::min(a.len(), b.len());
    intersection as f64 / min_len as f64
}

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

content = content[:start] + new_fns + content[end_bracket:]
with open(filepath, 'w') as f:
    f.write(content)

