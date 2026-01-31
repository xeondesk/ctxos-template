#!/bin/bash
# CtxOS CLI Demo Workflows
# Demonstrates practical usage of the CLI

set -e  # Exit on error

echo "======================================"
echo "CtxOS CLI Demo Workflows"
echo "======================================"

# Demo 1: Basic Collection
echo -e "\n[Demo 1] Basic Collection"
echo "Command: ctxos collect example.com"
echo "This would collect signals from all available sources for example.com"
# ctxos collect example.com -o demo_collected.json --verbose

# Demo 2: Targeted Collection
echo -e "\n[Demo 2] Targeted Collection (DNS only)"
echo "Command: ctxos collect example.com --source dns -o dns_results.json"
echo "This collects only DNS-related signals"
# ctxos collect example.com --source dns -o dns_results.json

# Demo 3: Parallel Collection
echo -e "\n[Demo 3] Parallel Collection (8 workers)"
echo "Command: ctxos collect example.com --parallel 8 -o fast_results.json"
echo "This uses 8 parallel workers for faster collection"
# ctxos collect example.com --parallel 8 -o fast_results.json

# Demo 4: Build Graph
echo -e "\n[Demo 4] Build Entity Graph"
echo "Command: ctxos graph build -i collected_data.json -o entity_graph.json"
echo "This builds an entity relationship graph from collected data"
# ctxos graph -i collected_data.json -o entity_graph.json

# Demo 5: Export Graph in Different Format
echo -e "\n[Demo 5] Export Graph as GraphML"
echo "Command: ctxos graph export -i collected_data.json -f graphml -o graph.graphml"
echo "This exports the graph for use in graph visualization tools"
# ctxos graph export -i collected_data.json -f graphml -o graph.graphml

# Demo 6: Analyze Risk
echo -e "\n[Demo 6] Analyze Risk with All Engines"
echo "Command: ctxos risk -i collected_data.json --engine all -o risks.json"
echo "This scores risk using all available engines"
# ctxos risk -i collected_data.json --engine all -o risks.json

# Demo 7: Filter High-Risk Items
echo -e "\n[Demo 7] Filter High-Risk Items (threshold 0.9)"
echo "Command: ctxos risk -i collected_data.json --threshold 0.9 -o high_risks.json"
echo "This only returns entities with risk scores above 0.9"
# ctxos risk -i collected_data.json --threshold 0.9 -o high_risks.json

# Demo 8: Run All Agents
echo -e "\n[Demo 8] Run All Analysis Agents"
echo "Command: ctxos agent all -i collected_data.json -o analysis.json"
echo "This runs all available agents for comprehensive analysis"
# ctxos agent all -i collected_data.json -o analysis.json

# Demo 9: Gap Detection
echo -e "\n[Demo 9] Detect Security Gaps"
echo "Command: ctxos agent gap-detect -i collected_data.json -o gaps.json"
echo "This identifies missing coverage or blind spots"
# ctxos agent gap-detect -i collected_data.json -o gaps.json

# Demo 10: Context Summarization
echo -e "\n[Demo 10] Summarize Context"
echo "Command: ctxos agent summarize -i collected_data.json -o summary.json"
echo "This generates a high-level summary of the collected context"
# ctxos agent summarize -i collected_data.json -o summary.json

# Demo 11: Complete Workflow
echo -e "\n[Demo 11] Complete Security Analysis Workflow"
echo "This demonstrates a complete analysis pipeline:"
echo ""
echo "1. Collect signals:"
echo "   ctxos collect example.com -o data.json"
echo ""
echo "2. Build graph:"
echo "   ctxos graph -i data.json -o graph.json"
echo ""
echo "3. Analyze risks:"
echo "   ctxos risk -i data.json -o risks.json"
echo ""
echo "4. Run analysis:"
echo "   ctxos agent all -i data.json -o analysis.json"
echo ""
echo "5. Generate report:"
echo "   cat analysis.json | jq . > report.json"

# Demo 12: Multi-Project Setup
echo -e "\n[Demo 12] Multi-Project Setup"
echo "Collect for multiple customers using project names:"
echo ""
echo "Customer A:"
echo "  ctxos --project customer-a collect customer-a-domain.com -o customer_a.json"
echo ""
echo "Customer B:"
echo "  ctxos --project customer-b collect customer-b-domain.com -o customer_b.json"

# Demo 13: Custom Configuration
echo -e "\n[Demo 13] Using Custom Configuration"
echo "Create project-specific config:"
echo "  cp configs/default.yaml configs/production.yaml"
echo "  # Edit production.yaml with custom settings"
echo ""
echo "Use custom config:"
echo "  ctxos --config configs/production.yaml collect example.com -o prod.json"

# Demo 14: Batch Processing
echo -e "\n[Demo 14] Batch Processing Multiple Domains"
echo "Process multiple domains in a script:"
echo ""
echo "  for domain in \$(cat domains.txt); do"
echo "    echo \"Processing \$domain...\""
echo "    ctxos collect \"\$domain\" -o \"results/\${domain}.json\""
echo "  done"

# Demo 15: Data Pipeline
echo -e "\n[Demo 15] Data Pipeline with JSON Processing"
echo "Process and filter results:"
echo ""
echo "Collect data:"
echo "  ctxos collect example.com -o data.json"
echo ""
echo "Extract specific fields:"
echo "  jq '.entities[] | {name: .name, risk: .risk_score}' data.json"
echo ""
echo "Filter by criteria:"
echo "  jq '.entities[] | select(.risk_score > 0.7)' data.json > high_risk.json"

# Demo 16: Environment Variables
echo -e "\n[Demo 16] Using Environment Variables"
echo "Set defaults to avoid repeating options:"
echo ""
echo "  export CTXOS_PROJECT=\"my-project\""
echo "  export CTXOS_CONFIG=\"configs/my-project.yaml\""
echo ""
echo "Then just use:"
echo "  ctxos collect example.com"
echo "  ctxos graph -i data.json"
echo "  ctxos risk -i data.json"

# Demo 17: Shell Completion
echo -e "\n[Demo 17] Shell Completion Demo"
echo "After installing completions, try:"
echo ""
echo "  ctxos <TAB>              # Show commands"
echo "  ctxos collect <TAB>      # Show options"
echo "  ctxos risk --engine <TAB> # Show engine choices"

# Demo 18: Verbose Mode
echo -e "\n[Demo 18] Verbose Output for Debugging"
echo "Enable verbose logging:"
echo "  ctxos --verbose collect example.com"
echo ""
echo "Enable debug mode:"
echo "  ctxos --debug collect example.com"

# Demo 19: Getting Help
echo -e "\n[Demo 19] Getting Help"
echo "General help:"
echo "  ctxos --help"
echo ""
echo "Command help:"
echo "  ctxos collect --help"
echo "  ctxos graph --help"
echo "  ctxos risk --help"
echo "  ctxos agent --help"

# Demo 20: Real-World Security Workflow
echo -e "\n[Demo 20] Real-World Security Assessment Workflow"
echo ""
echo "#!/bin/bash"
echo "# Security assessment for a domain"
echo "DOMAIN=\"example.com\""
echo "PROJECT=\"security-assessment-\$(date +%Y%m%d)\""
echo ""
echo "# 1. Collect comprehensive data"
echo "ctxos --project \$PROJECT collect \$DOMAIN \\"
echo "  --source all \\"
echo "  --parallel 8 \\"
echo "  -o \${PROJECT}/collected.json \\"
echo "  --verbose"
echo ""
echo "# 2. Build knowledge graph"
echo "ctxos --project \$PROJECT graph build \\"
echo "  -i \${PROJECT}/collected.json \\"
echo "  -o \${PROJECT}/graph.json"
echo ""
echo "# 3. Identify risks"
echo "ctxos --project \$PROJECT risk \\"
echo "  -i \${PROJECT}/collected.json \\"
echo "  --engine all \\"
echo "  -o \${PROJECT}/risks.json"
echo ""
echo "# 4. Run analysis agents"
echo "ctxos --project \$PROJECT agent all \\"
echo "  -i \${PROJECT}/collected.json \\"
echo "  --timeout 600 \\"
echo "  -o \${PROJECT}/analysis.json"
echo ""
echo "# 5. Generate final report"
echo "echo \"Assessment complete. Results in \${PROJECT}/ directory:\""
echo "ls -lh \${PROJECT}/"

echo -e "\n======================================"
echo "Demo Complete!"
echo "======================================"
echo ""
echo "To run these workflows, uncomment the '#' from any demo command."
echo "Make sure ctxos is installed first:"
echo "  pip install -e ."
echo ""
echo "Then test basic functionality:"
echo "  ctxos --help"
echo "  ctxos collect --help"
