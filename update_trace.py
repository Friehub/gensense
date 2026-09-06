import re

with open('frensense-engine/src/data_flow/confidence.rs', 'r') as f:
    content = f.read()

# Replace constants
content = content.replace("const MAX_HOPS: usize = 3;", """/// Maximum states to visit during backward data-flow trace.
const MAX_STATES: usize = 10_000;
/// Safety ceiling on backward depth, prevents path explosion.
const MAX_DEPTH: usize = 100;""")

# Add use statement for collections
if "use std::collections::" not in content:
    content = content.replace("use std::path::Path;", "use std::path::Path;\nuse std::collections::{HashSet, VecDeque};")

# Replace trace_hops_to_source
# Find start of trace_hops_to_source
start_idx = content.find("fn trace_hops_to_source")
if start_idx != -1:
    # Find #[allow(clippy::too_many_arguments)]
    allow_idx = content.rfind("#[allow(clippy::too_many_arguments)]", 0, start_idx)
    if allow_idx != -1:
        start_idx = allow_idx
        
    end_idx = content.find("fn extract_sink_var_from_ast", start_idx)
    if end_idx != -1:
        new_fn = """#[allow(clippy::too_many_arguments)]
fn trace_hops_to_source(
    def_use: &crate::cfg::def_use::DefUseChain,
    start_use_idx: usize,
    source: &str,
    root: tree_sitter::Node,
    registry: &CorpusSourceSinkRegistry,
    local_tainted_vars: Option<&[String]>,
) -> Option<usize> {
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    // queue elements: (use_idx, current_depth)
    queue.push_back((start_use_idx, 0));
    visited.insert(start_use_idx);
    
    let mut states_visited = 0;
    
    while let Some((use_idx, depth)) = queue.pop_front() {
        if depth >= MAX_DEPTH || states_visited >= MAX_STATES {
            continue;
        }
        states_visited += 1;
        
        // Check all definitions that reach this use.
        for def in def_use.defs_reaching(use_idx) {
            if is_real_source(def, source, root, registry, local_tainted_vars) {
                return Some(depth);
            }
            
            // This def derives from an RHS expression referencing other variable(s)
            for (rhs_use_idx, rhs_use) in def_use.uses.iter().enumerate() {
                if rhs_use.block_id == def.block_id
                    && rhs_use.name != def.name
                    && rhs_use.start_byte >= def.start_byte
                    && rhs_use.end_byte <= def.end_byte + SINK_USE_WINDOW_BYTES
                {
                    if !visited.contains(&rhs_use_idx) {
                        visited.insert(rhs_use_idx);
                        queue.push_back((rhs_use_idx, depth + 1));
                    }
                }
            }
        }
    }
    None
}

"""
        content = content[:start_idx] + new_fn + content[end_idx:]

# Update the caller in adjust_confidence
caller_old = """if let Some(hops) = trace_hops_to_source(
                &def_use,
                use_idx,
                source,
                root,
                registry,
                local_tainted_vars,
                0,
            ) {"""
caller_new = """if let Some(hops) = trace_hops_to_source(
                &def_use,
                *use_idx,
                source,
                root,
                registry,
                local_tainted_vars,
            ) {"""
content = content.replace(caller_old, caller_new)

with open('frensense-engine/src/data_flow/confidence.rs', 'w') as f:
    f.write(content)
