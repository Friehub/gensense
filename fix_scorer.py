import re

filepath_scorer = 'frensense-engine/src/pattern/scorer.rs'
with open(filepath_scorer, 'r') as f:
    scorer = f.read()

raw_dim_repl = """pub struct RawDimensions {
    pub ngram_sim: f64,
    pub ast_sim: f64,
    pub signature_sim: f64,
    pub param_type_sim: f64,
    pub type_usage_sim: f64,
    pub semantic_sim: f64,
    pub cf_sim: f64,
    pub api_sim: f64,
    pub motif_sim: f64,
    pub flow_sim: f64,
    pub tainted_api_sim: f64,
    pub config_sim: f64,
    pub cf_order_sim: f64,
    pub arg_type_sim: f64,
    pub literal_concat_sim: f64,
    // Multi-signal additions
    pub ngram_containment: f64,
    pub api_containment: f64,
    pub flow_containment: f64,
    pub ngram_overlap: f64,
    pub api_overlap: f64,
}

impl RawDimensions {
    pub fn weighted_score(&self, w: &[f64; 20]) -> f64 {
        self.ngram_sim * w[0]
            + self.ast_sim * w[1]
            + self.signature_sim * w[2]
            + self.param_type_sim * w[3]
            + self.type_usage_sim * w[4]
            + self.semantic_sim * w[5]
            + self.cf_sim * w[6]
            + self.api_sim * w[7]
            + self.tainted_api_sim * w[8]
            + self.motif_sim * w[9]
            + self.flow_sim * w[10]
            + self.config_sim * w[11]
            + self.cf_order_sim * w[12]
            + self.arg_type_sim * w[13]
            + self.literal_concat_sim * w[14]
            + self.ngram_containment * w[15]
            + self.api_containment * w[16]
            + self.flow_containment * w[17]
            + self.ngram_overlap * w[18]
            + self.api_overlap * w[19]
    }"""
scorer = re.sub(r'pub struct RawDimensions \{.*?literal_concat_sim \* w\[14\]\n    \}', raw_dim_repl, scorer, flags=re.DOTALL)

old_raw_dim = re.search(r'    pub\(crate\) fn raw_dimensions\(.*?\n        \}\n    \}', scorer, re.DOTALL).group(0)

new_raw_dim = """    pub(crate) fn raw_dimensions(
        candidate: &FunctionFingerprint,
        target: &FunctionFingerprint,
        _is_negative: bool,
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

        // For containment, target is the needle, candidate is the haystack.
        // wait, we want to know if the target (vulnerability) is contained in candidate.
        // minhash::containment_sorted(needle, haystack) means needle ∩ haystack / needle.len().
        let ngram_containment = containment(&target.ngram_hashes, &candidate.ngram_hashes);
        let api_containment = containment(&target.api_calls, &candidate.api_calls);
        let flow_containment = containment(&target.data_flow_path_hashes, &candidate.data_flow_path_hashes);
        
        let ngram_overlap = overlap(&candidate.ngram_hashes, &target.ngram_hashes);
        let api_overlap = overlap(&candidate.api_calls, &target.api_calls);

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
            ngram_containment,
            api_containment,
            flow_containment,
            ngram_overlap,
            api_overlap,
        }
    }"""
scorer = scorer.replace(old_raw_dim, new_raw_dim)

scorer = scorer.replace('weights: &[f64; 15],', 'weights: &[f64; 20],')

worst_neg_old = re.search(r'let mut worst_neg = RawDimensions::default\(\);\n        for negative in negatives \{.*?\n        \}', scorer, re.DOTALL).group(0)
worst_neg_new = """let mut worst_neg = RawDimensions::default();
        for negative in negatives {
            let dim = Self::raw_dimensions(candidate, negative, true);
            if dim.ngram_sim > worst_neg.ngram_sim { worst_neg.ngram_sim = dim.ngram_sim; }
            if dim.ast_sim > worst_neg.ast_sim { worst_neg.ast_sim = dim.ast_sim; }
            if dim.signature_sim > worst_neg.signature_sim { worst_neg.signature_sim = dim.signature_sim; }
            if dim.param_type_sim > worst_neg.param_type_sim { worst_neg.param_type_sim = dim.param_type_sim; }
            if dim.type_usage_sim > worst_neg.type_usage_sim { worst_neg.type_usage_sim = dim.type_usage_sim; }
            if dim.semantic_sim > worst_neg.semantic_sim { worst_neg.semantic_sim = dim.semantic_sim; }
            if dim.cf_sim > worst_neg.cf_sim { worst_neg.cf_sim = dim.cf_sim; }
            if dim.api_sim > worst_neg.api_sim { worst_neg.api_sim = dim.api_sim; }
            if dim.motif_sim > worst_neg.motif_sim { worst_neg.motif_sim = dim.motif_sim; }
            if dim.flow_sim > worst_neg.flow_sim { worst_neg.flow_sim = dim.flow_sim; }
            if dim.tainted_api_sim > worst_neg.tainted_api_sim { worst_neg.tainted_api_sim = dim.tainted_api_sim; }
            if dim.config_sim > worst_neg.config_sim { worst_neg.config_sim = dim.config_sim; }
            if dim.cf_order_sim > worst_neg.cf_order_sim { worst_neg.cf_order_sim = dim.cf_order_sim; }
            if dim.arg_type_sim > worst_neg.arg_type_sim { worst_neg.arg_type_sim = dim.arg_type_sim; }
            if dim.literal_concat_sim > worst_neg.literal_concat_sim { worst_neg.literal_concat_sim = dim.literal_concat_sim; }
            if dim.ngram_containment > worst_neg.ngram_containment { worst_neg.ngram_containment = dim.ngram_containment; }
            if dim.api_containment > worst_neg.api_containment { worst_neg.api_containment = dim.api_containment; }
            if dim.flow_containment > worst_neg.flow_containment { worst_neg.flow_containment = dim.flow_containment; }
            if dim.ngram_overlap > worst_neg.ngram_overlap { worst_neg.ngram_overlap = dim.ngram_overlap; }
            if dim.api_overlap > worst_neg.api_overlap { worst_neg.api_overlap = dim.api_overlap; }
        }"""
scorer = scorer.replace(worst_neg_old, worst_neg_new)

with open(filepath_scorer, 'w') as f:
    f.write(scorer)
