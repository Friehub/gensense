import re

with open('frensense-engine/src/pattern/scorer.rs', 'r') as f:
    content = f.read()

# Replace weighted_jaccard definition
old_weighted = """pub fn weighted_jaccard(
    a: &rustc_hash::FxHashMap<u64, f32>,
    b: &rustc_hash::FxHashMap<u64, f32>,
) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 0.0;
    }
    let mut intersection = 0.0f64;
    let mut union = 0.0f64;
    let all_keys: rustc_hash::FxHashSet<_> = a.keys().chain(b.keys()).collect();
    for key in all_keys {
        let wa = f64::from(a.get(key).copied().unwrap_or(0.0));
        let wb = f64::from(b.get(key).copied().unwrap_or(0.0));
        intersection += wa.min(wb);
        union += wa.max(wb);
    }
    if union == 0.0 {
        0.0
    } else {
        intersection / union
    }
}"""

new_weighted = """pub fn weighted_overlap_coefficient(
    a: &rustc_hash::FxHashMap<u64, f32>,
    b: &rustc_hash::FxHashMap<u64, f32>,
) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 0.0;
    }
    let mut intersection = 0.0f64;
    let mut sum_a = 0.0f64;
    let mut sum_b = 0.0f64;
    
    for (k, wa) in a.iter() {
        let wa_f = f64::from(*wa);
        sum_a += wa_f;
        if let Some(&wb) = b.get(k) {
            intersection += wa_f.min(f64::from(wb));
        }
    }
    for wb in b.values() {
        sum_b += f64::from(*wb);
    }
    
    let min_sum = sum_a.min(sum_b);
    if min_sum == 0.0 {
        0.0
    } else {
        intersection / min_sum
    }
}"""

content = content.replace(old_weighted, new_weighted)

# Replace the inner jaccard closures in raw_dimensions
old_closures = """        let jaccard = |a: &[u64], b: &[u64]| -> f64 {
            if a.is_empty() && b.is_empty() {
                return 0.5; // Both empty — neutral
            }
            if a.is_empty() || b.is_empty() {
                return 0.0;
            }
            minhash::jaccard_similarity_sorted(a, b)
        };
        let jaccard_sorted = |a: &[u64], b: &[u64]| -> f64 {
            if a.is_empty() && b.is_empty() {
                return 0.5; // Both empty — neutral
            }
            if a.is_empty() || b.is_empty() {
                return 0.0;
            }
            minhash::jaccard_similarity_sorted(a, b)
        };"""

new_closures = """        let overlap = |a: &[u64], b: &[u64]| -> f64 {
            if a.is_empty() && b.is_empty() {
                return 0.5; // Both empty — neutral
            }
            if a.is_empty() || b.is_empty() {
                return 0.0;
            }
            minhash::overlap_coefficient_sorted(a, b)
        };
        let overlap_sorted = |a: &[u64], b: &[u64]| -> f64 {
            if a.is_empty() && b.is_empty() {
                return 0.5; // Both empty — neutral
            }
            if a.is_empty() || b.is_empty() {
                return 0.0;
            }
            minhash::overlap_coefficient_sorted(a, b)
        };"""

content = content.replace(old_closures, new_closures)

# Update usage of jaccard to overlap
content = content.replace("jaccard(&candidate.ngram_hashes, &target.ngram_hashes)", "overlap(&candidate.ngram_hashes, &target.ngram_hashes)")
content = content.replace("weighted_jaccard(", "weighted_overlap_coefficient(")
content = content.replace("jaccard(&candidate.semantic_markers, &target.semantic_markers)", "overlap(&candidate.semantic_markers, &target.semantic_markers)")
content = content.replace("jaccard_sorted(&candidate.data_flow_edges, &target.data_flow_edges)", "overlap_sorted(&candidate.data_flow_edges, &target.data_flow_edges)")
content = content.replace("jaccard_sorted(&candidate.cfg_edges, &target.cfg_edges)", "overlap_sorted(&candidate.cfg_edges, &target.cfg_edges)")
content = content.replace("jaccard_sorted(&candidate.api_calls, &target.api_calls)", "overlap_sorted(&candidate.api_calls, &target.api_calls)")

with open('frensense-engine/src/pattern/scorer.rs', 'w') as f:
    f.write(content)
