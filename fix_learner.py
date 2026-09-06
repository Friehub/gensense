import re

filepath = 'frensense-engine/src/pattern/weight_learner.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Replace FeatureVec definition
content = content.replace("pub type FeatureVec = [f64; 15];", "pub type FeatureVec = [f64; 20];")

# Replace DEFAULT_WEIGHTS
repl_default = """pub(crate) const DEFAULT_WEIGHTS: FeatureVec = [
    0.08, 0.10, 0.08, 0.04, 0.03, 0.10, 0.10, 0.10, 0.14, 0.12, 0.16, 0.03, 0.02, 0.04, 0.04,
    // New dimensions: ngram_containment, api_containment, flow_containment, ngram_overlap, api_overlap
    0.02, 0.02, 0.02, 0.01, 0.01,
];"""
content = re.sub(r'pub\(crate\) const DEFAULT_WEIGHTS: FeatureVec = \[\n.*?\];', repl_default, content, flags=re.DOTALL)

# Replace compute_features to delegate to scorer
repl_compute = """fn compute_features(candidate: &FunctionFingerprint, target: &FunctionFingerprint) -> FeatureVec {
    let raw = crate::pattern::scorer::PatternScorer::raw_dimensions(candidate, target, false);
    [
        raw.ngram_sim,
        raw.ast_sim,
        raw.signature_sim,
        raw.param_type_sim,
        raw.type_usage_sim,
        raw.semantic_sim,
        raw.cf_sim,
        raw.api_sim,
        raw.tainted_api_sim,
        raw.motif_sim,
        raw.flow_sim,
        raw.config_sim,
        raw.cf_order_sim,
        raw.arg_type_sim,
        raw.literal_concat_sim,
        raw.ngram_containment,
        raw.api_containment,
        raw.flow_containment,
        raw.ngram_overlap,
        raw.api_overlap,
    ]
}"""
content = re.sub(r'fn compute_features\(.*?\) -> FeatureVec \{.*?\n\}', repl_compute, content, flags=re.DOTALL)

# Fix train_weights initialization
content = content.replace("let mut w = [0.0; 15];", "let mut w = [0.0; 20];")
content = content.replace("for (i, weight) in w.iter_mut().enumerate().take(15) {", "for (i, weight) in w.iter_mut().enumerate().take(20) {")
content = content.replace("for j in 0..15 {", "for j in 0..20 {")


with open(filepath, 'w') as f:
    f.write(content)

