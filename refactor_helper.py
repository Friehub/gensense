import re

filepath = 'frensense-engine/src/fingerprint.rs'
with open(filepath, 'r') as f:
    content = f.read()

# Find the start of the extraction logic inside the loop
start_str = "            let mut function_name = \"anonymous\".to_string();"
start_idx = content.find(start_str)

end_str = "            fingerprints.push((fp, node));\n        }"
end_idx = content.find(end_str, start_idx)

extraction_logic = content[start_idx:end_idx]

# We will create a helper function
helper_fn = """
#[allow(clippy::too_many_arguments)]
fn extract_single_fingerprint(
    node: Node<'_>,
    body: Node<'_>,
    source_code: &str,
    path: &Path,
    language: &str,
    lang: Language,
    window_size: usize,
    import_map: Option<&crate::import_resolver::ImportMap>,
    region: Option<(usize, usize)>,
) -> FunctionFingerprint {
""" + extraction_logic + """
    fp
}
"""

# Wait, `extraction_logic` uses `function_name` heavily, but we can compute it inside the helper!
# And it uses `path`, `language`, `lang`, `window_size`, `import_map`, `node`, `body`, `source_code`.
# We need to change `region: None,` to `region,` in `FunctionFingerprint` initialization inside `extraction_logic`!

extraction_logic = extraction_logic.replace("region: None,", "region,")

new_loop_body = """            let fp = extract_single_fingerprint(
                node, body, source_code, path, &language, lang, window_size, import_map, None,
            );
            fingerprints.push((fp, node));
            
            // Check for region chunking
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
                    if window_end - window_start < 10 {
                        break;
                    }
                    
                    let start_byte = statements[window_start].start_byte();
                    let end_byte = statements[window_end - 1].end_byte();
                    let region_source = &source_code[start_byte..end_byte];
                    
                    // Generate wrapped code to form a valid AST
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
                                        // We reuse the parent function's function_name etc. inside extract_single_fingerprint?
                                        // Wait, extract_single_fingerprint infers the name from the node!
                                        // But for regions, we want the PARENT's name!
                                        // Let's modify extract_single_fingerprint to take `override_function_name: Option<&str>` and `override_line: Option<usize>`
                                    }
                                }
                            }
                        }
                    }
                    
                    window_start += 10; // Stride
                }
            }
"""
