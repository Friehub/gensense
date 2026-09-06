import re

filepath = 'frensense-engine/src/pattern/weight_learner.rs'
with open(filepath, 'r') as f:
    content = f.read()

repl = """fn compute_features(candidate: &FunctionFingerprint, target: &FunctionFingerprint) -> FeatureVec {
    let raw = crate::pattern::scorer::Scorer::raw_dimensions(candidate, target, false);
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
        raw.ngram_overlap,
        raw.api_overlap,
        raw.size_ratio,
    ]
}"""
content = re.sub(r'fn compute_features\(candidate: &FunctionFingerprint, target: &FunctionFingerprint\) -> FeatureVec \{.*?\n\}', repl, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)
