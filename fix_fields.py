import re

filepath = 'frensense-engine/src/pattern/scorer.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Replace the duplicated RawDimensions
repl = """pub struct RawDimensions {
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
    pub ngram_overlap: f64,
    pub api_overlap: f64,
    pub size_ratio: f64,
}"""
content = re.sub(r'pub struct RawDimensions \{.*?literal_concat_sim: f64,\n\}', repl, content, flags=re.DOTALL)
# One more fix because I had another old definition possibly?
# Let's just use regex to replace pub struct RawDimensions { ... } entirely
content = re.sub(r'pub struct RawDimensions \{.*?(?=\nimpl RawDimensions)', repl, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)

