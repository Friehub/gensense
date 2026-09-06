import re

filepath = 'frensense-engine/src/pattern/scorer.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Restore jaccard inside raw_dim and assign both
# Previously I changed:
# let jaccard = |a: &[u64], b: &[u64]| -> f64 { ... minhash::overlap_coefficient_sorted(a, b) };
# to overlap_sorted.

repl_raw_dim = """    fn raw_dimensions(
        candidate: &FunctionFingerprint,
        target: &FunctionFingerprint,
        penalize_subset: bool,
    ) -> RawDimensions {
        let jaccard = |a: &[u64], b: &[u64]| minhash::jaccard_similarity_sorted(a, b);
        let overlap = |a: &[u64], b: &[u64]| minhash::overlap_coefficient_sorted(a, b);
        let containment = |a: &[u64], b: &[u64]| minhash::containment_sorted(a, b);

        let ngram_sim = if candidate.weighted_ngram_hashes.is_empty()
            || target.weighted_ngram_hashes.is_empty()
        {
            jaccard(&candidate.ngram_hashes, &target.ngram_hashes)
        } else {
            let mut intersection = 0.0f64;
            let mut union_sum = 0.0f64;
            for (h, w) in &candidate.weighted_ngram_hashes {
                union_sum += *w as f64;
                if target.weighted_ngram_hashes.contains_key(h) {
                    intersection += *w as f64;
                }
            }
            for w in target.weighted_ngram_hashes.values() {
                union_sum += *w as f64;
            }
            if union_sum == 0.0 {
                0.0
            } else {
                intersection / union_sum
            }
        };

        let semantic_sim = jaccard(&candidate.semantic_markers, &target.semantic_markers);

        let ast_sim = if !candidate.skeleton_hashes.is_empty() && !target.skeleton_hashes.is_empty() {
            1.0 - crate::ast_distance::tree_edit_distance(
                &candidate.skeleton_hashes,
                &target.skeleton_hashes,
            )
        } else {
            jaccard(&candidate.structural_markers, &target.structural_markers)
        };

        let signature_sim = jaccard(&candidate.signature_ngrams, &target.signature_ngrams);
        let param_type_sim = jaccard(&candidate.param_type_ngrams, &target.param_type_ngrams);
        let type_usage_sim = type_usage_overlap(candidate, target);
        let cf_sim = jaccard(&candidate.control_flow_hashes, &target.control_flow_hashes);

        let api_sim = jaccard(&candidate.api_calls, &target.api_calls)
            .max(jaccard(&candidate.api_call_segments, &target.api_call_segments));
        let motif_sim = jaccard(&candidate.motif_hashes, &target.motif_hashes);
        let flow_sim = jaccard(
            &candidate.data_flow_path_hashes,
            &target.data_flow_path_hashes,
        );
        let tainted_api_sim = jaccard(&candidate.tainted_api_calls, &target.tainted_api_calls);
        let config_sim = jaccard(&candidate.config_literal_hashes, &target.config_literal_hashes);
        let cf_order_sim = jaccard(&candidate.control_flow_sequence, &target.control_flow_sequence);
        let arg_type_sim = jaccard(&candidate.argument_call_types, &target.argument_call_types);
        let literal_concat_sim = jaccard(&candidate.literal_pattern_hashes, &target.literal_pattern_hashes);

        let ngram_overlap = overlap(&candidate.ngram_hashes, &target.ngram_hashes);
        let api_overlap = overlap(&candidate.api_calls, &target.api_calls);
        let size_ratio = minhash::size_ratio(candidate.ngram_hashes.len(), target.ngram_hashes.len());

        RawDimensions {
            ngram_sim,
            ast_sim,
            signature_sim,
            param_type_sim,
            type_usage_sim,
            semantic_sim,
            cf_sim,
            api_sim,
            motif_sim,
            flow_sim,
            tainted_api_sim,
            config_sim,
            cf_order_sim,
            arg_type_sim,
            literal_concat_sim,
            ngram_overlap,
            api_overlap,
            size_ratio,
        }
    }"""
content = re.sub(r'fn raw_dimensions\(\n.*?\}\n    \}', repl_raw_dim, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)
