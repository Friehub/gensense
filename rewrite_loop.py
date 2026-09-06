import re

filepath = 'frensense-engine/src/fingerprint.rs'
with open(filepath, 'r') as f:
    content = f.read()

loop_start = content.find('    loop {\n        let node = cursor.node();')
loop_end = content.find('    fingerprints.extend(with_nodes.into_iter().map(|(fp, _)| fp));', loop_start)

# We will just rewrite extract_fingerprints_with_nodes entirely!

new_fn = """pub fn extract_fingerprints_with_nodes<'a>(
    root: Node<'a>,
    source_code: &str,
    path: &Path,
    fingerprints: &mut Vec<(FunctionFingerprint, Node<'a>)>,
    window_size: usize,
    import_map: Option<&crate::import_resolver::ImportMap>,
) {
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
    let language = crate::parser::ext_to_language(ext).to_string();

    let lang: Language = match ext {
        "rs" => Language::Rust,
        "ts" | "tsx" => Language::TypeScript,
        "js" | "jsx" => Language::JavaScript,
        "c" | "h" => Language::C,
        "py" | "pyi" => Language::Python,
        _ => return,
    };

    let mut cursor = root.walk();
    loop {
        let node = cursor.node();
        let kind = node.kind();
        if matches!(
            kind,
            "function_item" | "function_declaration" | "method_definition" | "arrow_function"
        ) && let Some(body) = node.child_by_field_name("body")
        {
            let mut function_name = "anonymous".to_string();
            if let Some(name_node) = node.child_by_field_name("name") {
                function_name =
                    source_code[name_node.start_byte()..name_node.end_byte()].to_string();
            } else if let Some(inferred) =
                crate::route_registry::infer_function_name(node, source_code)
            {
                function_name = inferred;
            }

            let body_code = &source_code[body.start_byte()..body.end_byte()];
            let tokens: Vec<String> = body_code
                .split_whitespace()
                .filter(|t| !t.is_empty() && !t.starts_with("//"))
                .map(|t| normalize_token(t).to_string())
                .collect();

            let total_bytes = body.end_byte() - body.start_byte();
            let comment_bytes = count_comment_bytes(body, source_code);
            let sig_tokens = extract_signature_tokens(node, source_code);
            let param_types = extract_param_types(node, source_code);
            let name_segments = split_name_segments(&function_name);

            let mut multi_scale_hashes = token_ngrams_positional(&tokens, window_size);
            multi_scale_hashes.extend(token_ngrams_positional(&tokens, window_size + 2));
            multi_scale_hashes.extend(token_ngrams_positional(&tokens, window_size + 5));

            let control_flow = extract_control_flow(body, source_code);
            let control_flow_sequence = extract_cf_sequence(body, source_code);
            let raw_call_names = collect_raw_call_names(body, source_code);
            let mut api_calls_set = FxHashSet::default();
            let mut api_call_segments_set = FxHashSet::default();
            for name in &raw_call_names {
                let is_macro = name.starts_with("macro_");
                let mut h = FxHasher::default();
                name.hash(&mut h);
                api_calls_set.insert(h.finish());
                if !is_macro {
                    if let Some(dot_pos) = name.rfind('.') {
                        let method = &name[dot_pos + 1..];
                        let mut h2 = FxHasher::default();
                        method.hash(&mut h2);
                        api_call_segments_set.insert(h2.finish());
                    }
                }
            }
            let mut api_calls: Vec<u64> = api_calls_set.into_iter().collect();
            api_calls.sort_unstable();
            let mut api_call_segments: Vec<u64> = api_call_segments_set.into_iter().collect();
            api_call_segments.sort_unstable();

            let property_accesses = extract_property_accesses(body, source_code);
            let semantic_markers = extract_semantic_markers(
                body,
                source_code,
                &api_calls,
                &api_call_segments,
                &property_accesses,
            );

            let param_names: Vec<String> = node
                .child_by_field_name("parameters")
                .map(|p| {
                    let mut names = Vec::new();
                    let mut c = p.walk();
                    if c.goto_first_child() {
                        loop {
                            let child = c.node();
                            if let Some(name) = child
                                .child_by_field_name("pattern")
                                .or_else(|| child.child_by_field_name("name"))
                            {
                                let text = &source_code[name.start_byte()..name.end_byte()];
                                if child.kind() == "identifier"
                                    || child.kind() == "required_parameter"
                                {
                                    names.push(text.to_string());
                                }
                            }
                            if !c.goto_next_sibling() {
                                break;
                            }
                        }
                    }
                    names
                })
                .unwrap_or_default();
            let tainted_api_calls = extract_tainted_calls(body, source_code, &param_names);
            let motif_hashes =
                extract_motif_hashes(&raw_call_names, &crate::corpus::motifs::MOTIF_LOOKUP);
            let data_flow_path_hashes =
                crate::corpus::flow_fingerprint::extract_flow_paths(body, source_code, import_map);
            let argument_call_types = extract_argument_call_types(body, source_code);
            let literal_pattern_hashes = extract_literal_patterns(body, source_code);

            let skeleton = crate::ast_distance::extract_skeleton(body, source_code);
            let mut skeleton_hashes = Vec::with_capacity(skeleton.len());
            for s in &skeleton {
                let mut hasher = rustc_hash::FxHasher::default();
                std::hash::Hash::hash(s, &mut hasher);
                skeleton_hashes.push(std::hash::Hasher::finish(&hasher));
            }
            let has_http_decorator =
                crate::decorator::has_routing_decorator(node, source_code).is_some();
            let is_registered_handler =
                crate::route_registry::is_function_registered_in_file(node, source_code, "")
                    || crate::route_registry::is_inline_registered_handler(node, source_code);

            let fp = FunctionFingerprint {
                file_path: path.to_string_lossy().to_string(),
                function_name: function_name.clone(),
                region: None,
                line: node.start_position().row + 1,
                language: language.clone(),
                ngram_hashes: multi_scale_hashes.clone(),
                weighted_ngram_hashes: multi_scale_hashes.clone().into_iter().map(|h| (h, 1.0)).collect(),
                signature_ngrams: token_ngrams_sorted(&sig_tokens, 3.min(sig_tokens.len().max(1))),
                param_type_ngrams: token_ngrams_sorted(
                    &param_types,
                    2.min(param_types.len().max(1)),
                ),
                name_segments: name_segments.clone(),
                structural_markers: collect_structural_markers(body, source_code, lang),
                type_usages: {
                    let mut tu = collect_type_usages(body, source_code);
                    tu.extend(crate::decorator::collect_param_decorator_types(
                        node,
                        source_code,
                    ));
                    tu
                },
                comment_density: if total_bytes > 0 {
                    comment_bytes as f64 / total_bytes as f64
                } else {
                    0.0
                },
                semantic_markers: semantic_markers.clone(),
                skeleton: skeleton.clone(),
                skeleton_hashes: skeleton_hashes.clone(),
                control_flow_hashes: control_flow.clone(),
                control_flow_sequence: control_flow_sequence.clone(),
                api_calls: api_calls.clone(),
                api_call_segments: api_call_segments.clone(),
                property_accesses: property_accesses.clone(),
                motif_hashes: motif_hashes.clone(),
                data_flow_path_hashes: data_flow_path_hashes.clone(),
                raw_call_names: raw_call_names.clone(),
                param_names: param_names.clone(),
                tainted_api_calls: tainted_api_calls.clone(),
                argument_call_types: argument_call_types.clone(),
                literal_pattern_hashes: literal_pattern_hashes.clone(),
                has_http_decorator,
                is_registered_handler,
            };

            fingerprints.push((fp.clone(), node));
            
            // Region Chunking for Giant Functions
            let mut statements = Vec::new();
            let mut c = body.walk();
            for child in body.children(&mut c) {
                if child.is_named() {
                    statements.push(child);
                }
            }
            
            if statements.len() > 20 {
                let mut window_start = 0;
                while window_start < statements.len() {
                    let window_end = (window_start + 20).min(statements.len());
                    if window_end - window_start < 5 {
                        break;
                    }
                    
                    let start_byte = statements[window_start].start_byte();
                    let end_byte = statements[window_end - 1].end_byte();
                    let region_source = &source_code[start_byte..end_byte];
                    
                    // Parse the region
                    let region_code = match lang {
                        Language::Rust => format!("fn _region() {{\n{}\n}}", region_source),
                        Language::Python => {
                            let indented = region_source.lines()
                                .map(|l| format!("    {}", l))
                                .collect::<Vec<_>>()
                                .join("\\n");
                            format!("def _region():\\n{}", indented)
                        },
                        _ => format!("function _region() {{\n{}\n}}", region_source),
                    };
                    
                    let mut parser = tree_sitter::Parser::new();
                    if let Ok(ts_lang) = crate::parser::ParserRegistry::get_language_by_name(&language) {
                        if parser.set_language(&ts_lang).is_ok() {
                            if let Some(tree) = parser.parse(&region_code, None) {
                                let r_root = tree.root_node();
                                let mut r_cursor = r_root.walk();
                                let mut r_node = None;
                                for child in r_root.children(&mut r_cursor) {
                                    let kind = child.kind();
                                    if matches!(kind, "function_item" | "function_declaration" | "method_definition" | "arrow_function") {
                                        r_node = Some(child);
                                        break;
                                    }
                                }
                                
                                if let Some(r_node) = r_node {
                                    if let Some(r_body) = r_node.child_by_field_name("body") {
                                        
                                        // Extract region-specific features!
                                        let mut r_api_calls_set = FxHashSet::default();
                                        let mut r_api_call_segments_set = FxHashSet::default();
                                        let r_raw_call_names = collect_raw_call_names(r_body, &region_code);
                                        for name in &r_raw_call_names {
                                            let is_macro = name.starts_with("macro_");
                                            let mut h = FxHasher::default();
                                            name.hash(&mut h);
                                            r_api_calls_set.insert(h.finish());
                                            if !is_macro {
                                                if let Some(dot_pos) = name.rfind('.') {
                                                    let method = &name[dot_pos + 1..];
                                                    let mut h2 = FxHasher::default();
                                                    method.hash(&mut h2);
                                                    r_api_call_segments_set.insert(h2.finish());
                                                }
                                            }
                                        }
                                        let mut r_api_calls: Vec<u64> = r_api_calls_set.into_iter().collect();
                                        r_api_calls.sort_unstable();
                                        let mut r_api_call_segments: Vec<u64> = r_api_call_segments_set.into_iter().collect();
                                        r_api_call_segments.sort_unstable();

                                        let r_property_accesses = extract_property_accesses(r_body, &region_code);
                                        let r_semantic_markers = extract_semantic_markers(
                                            r_body,
                                            &region_code,
                                            &r_api_calls,
                                            &r_api_call_segments,
                                            &r_property_accesses,
                                        );

                                        let r_tokens: Vec<String> = region_source
                                            .split_whitespace()
                                            .filter(|t| !t.is_empty() && !t.starts_with("//"))
                                            .map(|t| normalize_token(t).to_string())
                                            .collect();
                                        let mut r_multi_scale_hashes = token_ngrams_positional(&r_tokens, window_size);
                                        r_multi_scale_hashes.extend(token_ngrams_positional(&r_tokens, window_size + 2));
                                        r_multi_scale_hashes.extend(token_ngrams_positional(&r_tokens, window_size + 5));

                                        let mut r_fp = fp.clone();
                                        r_fp.region = Some((window_start, window_end));
                                        
                                        // Overwrite the features that are region-specific
                                        r_fp.api_calls = r_api_calls;
                                        r_fp.api_call_segments = r_api_call_segments;
                                        r_fp.property_accesses = r_property_accesses;
                                        r_fp.semantic_markers = r_semantic_markers;
                                        r_fp.raw_call_names = r_raw_call_names.clone();
                                        r_fp.ngram_hashes = r_multi_scale_hashes.clone();
                                        r_fp.weighted_ngram_hashes = r_multi_scale_hashes.into_iter().map(|h| (h, 1.0)).collect();
                                        
                                        r_fp.control_flow_hashes = extract_control_flow(r_body, &region_code);
                                        r_fp.control_flow_sequence = extract_cf_sequence(r_body, &region_code);
                                        r_fp.tainted_api_calls = extract_tainted_calls(r_body, &region_code, &param_names);
                                        r_fp.motif_hashes = extract_motif_hashes(&r_raw_call_names, &crate::corpus::motifs::MOTIF_LOOKUP);
                                        r_fp.argument_call_types = extract_argument_call_types(r_body, &region_code);
                                        r_fp.literal_pattern_hashes = extract_literal_patterns(r_body, &region_code);
                                        r_fp.structural_markers = collect_structural_markers(r_body, &region_code, lang);
                                        r_fp.type_usages = collect_type_usages(r_body, &region_code);
                                        
                                        let r_skeleton = crate::ast_distance::extract_skeleton(r_body, &region_code);
                                        let mut r_skeleton_hashes = Vec::with_capacity(r_skeleton.len());
                                        for s in &r_skeleton {
                                            let mut hasher = rustc_hash::FxHasher::default();
                                            std::hash::Hash::hash(s, &mut hasher);
                                            r_skeleton_hashes.push(std::hash::Hasher::finish(&hasher));
                                        }
                                        r_fp.skeleton = r_skeleton;
                                        r_fp.skeleton_hashes = r_skeleton_hashes;
                                        
                                        // Push the region fingerprint. Note: we reuse `node` (the whole function's node) for data flow engine compatibility
                                        fingerprints.push((r_fp, node));
                                    }
                                }
                            }
                        }
                    }
                    
                    window_start += 10;
                }
            }
        }
        
        if cursor.goto_first_child() {
            continue;
        }
        loop {
            if cursor.goto_next_sibling() {
                break;
            }
            if !cursor.goto_parent() {
                return;
            }
        }
    }
}
"""

start_idx = content.find("pub fn extract_fingerprints_with_nodes<'a>(")
end_idx = content.find("pub fn extract_fingerprints(", start_idx)

content = content[:start_idx] + new_fn + "\n" + content[end_idx:]

with open(filepath, 'w') as f:
    f.write(content)

