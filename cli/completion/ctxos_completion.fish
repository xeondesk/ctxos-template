complete -c ctxos -n "__fish_use_subcommand_from_token" -f -a collect -d "Collect signals from configured sources"
complete -c ctxos -n "__fish_use_subcommand_from_token" -f -a graph -d "Build and analyze entity graphs"
complete -c ctxos -n "__fish_use_subcommand_from_token" -f -a risk -d "Calculate risk scores for entities"
complete -c ctxos -n "__fish_use_subcommand_from_token" -f -a agent -d "Run analysis agents"

# Global options
complete -c ctxos -n "__fish_use_subcommand_from_token" -s v -l version -d "Show version"
complete -c ctxos -n "__fish_use_subcommand_from_token" -s p -l project -d "Project name"
complete -c ctxos -n "__fish_use_subcommand_from_token" -s c -l config -d "Config file" -r
complete -c ctxos -n "__fish_use_subcommand_from_token" -l verbose -d "Enable verbose output"
complete -c ctxos -n "__fish_use_subcommand_from_token" -l debug -d "Enable debug mode"
complete -c ctxos -n "__fish_use_subcommand_from_token" -s h -l help -d "Show help"

# Collect command
complete -c ctxos -n "__fish_seen_subcommand_from collect" -s s -l source -d "Collector source" -x -a "all dns osint recon cloud vuln"
complete -c ctxos -n "__fish_seen_subcommand_from collect" -s o -l output -d "Output file" -r
complete -c ctxos -n "__fish_seen_subcommand_from collect" -l parallel -d "Number of parallel collectors" -x

# Graph command
complete -c ctxos -n "__fish_seen_subcommand_from graph" -f -a "build analyze export visualize" -d "Graph action"
complete -c ctxos -n "__fish_seen_subcommand_from graph" -s i -l input -d "Input file" -r
complete -c ctxos -n "__fish_seen_subcommand_from graph" -s o -l output -d "Output file" -r
complete -c ctxos -n "__fish_seen_subcommand_from graph" -s f -l format -d "Output format" -x -a "json graphml dot png"

# Risk command
complete -c ctxos -n "__fish_seen_subcommand_from risk" -s i -l input -d "Input file" -r
complete -c ctxos -n "__fish_seen_subcommand_from risk" -s o -l output -d "Output file" -r
complete -c ctxos -n "__fish_seen_subcommand_from risk" -l engine -d "Scoring engine" -x -a "risk exposure drift all"
complete -c ctxos -n "__fish_seen_subcommand_from risk" -l threshold -d "Risk threshold" -x

# Agent command
complete -c ctxos -n "__fish_seen_subcommand_from agent" -f -a "summarize gap-detect hypothesis explain all" -d "Agent type"
complete -c ctxos -n "__fish_seen_subcommand_from agent" -s i -l input -d "Input file" -r
complete -c ctxos -n "__fish_seen_subcommand_from agent" -s o -l output -d "Output file" -r
complete -c ctxos -n "__fish_seen_subcommand_from agent" -l timeout -d "Execution timeout" -x
