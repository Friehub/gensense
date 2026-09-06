import re

filepath = 'frensense-engine/src/pattern/scorer.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Expand RawDimensions
repl_raw = """pub struct RawDimensions {
    ngram_sim: f64,
    ast_sim: f64,
    signature_sim: f64,
    param_type_sim: f64,
    type_usage_sim: f64,
    semantic_sim: f64,
    cf_sim: f64,
    api_sim: f64,
    motif_sim: f64,
    flow_sim: f64,
    tainted_api_sim: f64,
    config_sim: f64,
    cf_order_sim: f64,
    arg_type_sim: f64,
    literal_concat_sim: f64,
    ngram_overlap: f64,
    api_overlap: f64,
    size_ratio: f64,
}

impl RawDimensions {
    fn weighted_score(&self, w: &[f64; 18]) -> f64 {
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
            + self.ngram_overlap * w[15]
            + self.api_overlap * w[16]
            + self.size_ratio * w[17]
    }"""
content = re.sub(r'pub struct RawDimensions \{.*?literal_concat_sim \* w\[14\]\n    \}', repl_raw, content, flags=re.DOTALL)

# Add to Default
repl_default = """    fn default() -> Self {
        Self {
            ngram_sim: 0.0,
            ast_sim: 0.0,
            signature_sim: 0.0,
            param_type_sim: 0.0,
            type_usage_sim: 0.0,
            semantic_sim: 0.0,
            cf_sim: 0.0,
            api_sim: 0.0,
            motif_sim: 0.0,
            flow_sim: 0.0,
            tainted_api_sim: 0.0,
            config_sim: 0.0,
            cf_order_sim: 0.0,
            arg_type_sim: 0.0,
            literal_concat_sim: 0.0,
            ngram_overlap: 0.0,
            api_overlap: 0.0,
            size_ratio: 0.0,
        }
    }"""
content = re.sub(r'fn default\(\) -> Self \{.*?\}\n    \}', repl_default, content, flags=re.DOTALL)

# Also need to fix worst_neg updates
repl_worst = """        let mut worst_neg = RawDimensions::default();
        for negative in negatives {
            let dim = raw_dim(negative, true);
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
            if dim.ngram_overlap > worst_neg.ngram_overlap { worst_neg.ngram_overlap = dim.ngram_overlap; }
            if dim.api_overlap > worst_neg.api_overlap { worst_neg.api_overlap = dim.api_overlap; }
            if dim.size_ratio > worst_neg.size_ratio { worst_neg.size_ratio = dim.size_ratio; }
        }"""
content = re.sub(r'let mut worst_neg = RawDimensions::default\(\);\n        for negative in negatives \{.*?\n        \}', repl_worst, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)
