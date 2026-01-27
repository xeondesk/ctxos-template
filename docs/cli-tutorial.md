# CtxOS CLI Documentation

The CtxOS Command Line Interface (CLI) provides a powerful tool for collecting, analyzing, and managing security context data.

## Installation

### From Source
```bash
pip install -e .
```

Or directly:
```bash
python -m pip install .
```

This makes `ctxos` available globally.

## Global Options

All commands support these global options:

```
-p, --project PROJECT   Project name (default: 'default', env: CTXOS_PROJECT)
-c, --config CONFIG     Path to config file (default: 'configs/default.yaml', env: CTXOS_CONFIG)
--verbose               Enable verbose output
--debug                 Enable debug mode
-v, --version           Show version
-h, --help              Show help
```

### Environment Variables

You can set these environment variables to avoid typing options repeatedly:

```bash
export CTXOS_PROJECT="my-project"
export CTXOS_CONFIG="/path/to/config.yaml"
```

## Commands

### `ctxos collect`

Collect security signals from various sources.

```bash
ctxos collect [target] [options]
```

**Arguments:**
- `target`: Domain or asset to collect data for

**Options:**
- `-s, --source {all|dns|osint|recon|cloud|vuln}`: Collector source (default: all)
- `-o, --output FILE`: Output file for results (JSON)
- `--parallel WORKERS`: Number of parallel collectors (default: 4)

**Examples:**
```bash
# Collect from all sources
ctxos collect example.com

# Collect only from DNS and recon
ctxos collect example.com --source dns
ctxos collect example.com --source recon

# Save results to file
ctxos collect example.com -o results.json

# Use more parallel workers
ctxos collect example.com --parallel 8

# Verbose output
ctxos collect example.com --verbose
```

### `ctxos graph`

Build and analyze entity relationship graphs.

```bash
ctxos graph [action] [options]
```

**Arguments:**
- `action`: Graph action - `build`, `analyze`, `export`, `visualize` (default: build)

**Options:**
- `-i, --input FILE`: Input file (JSON) with entities and signals
- `-o, --output FILE`: Output file for results
- `-f, --format {json|graphml|dot|png}`: Output format (default: json)

**Examples:**
```bash
# Build graph from input file
ctxos graph -i entities.json

# Build and export as GraphML
ctxos graph -i entities.json -f graphml -o graph.graphml

# Analyze existing graph
ctxos graph analyze -i entities.json

# Visualize as PNG
ctxos graph visualize -i entities.json -f png -o graph.png
```

### `ctxos risk`

Calculate risk scores for entities.

```bash
ctxos risk [options]
```

**Options:**
- `-i, --input FILE`: Input file (JSON) with entities (required)
- `-o, --output FILE`: Output file for risk results
- `--engine {risk|exposure|drift|all}`: Scoring engine (default: all)
- `--threshold THRESHOLD`: Risk threshold for filtering (default: 0.7)

**Examples:**
```bash
# Calculate risk scores
ctxos risk -i entities.json

# Use specific engine
ctxos risk -i entities.json --engine exposure

# Filter by threshold
ctxos risk -i entities.json --threshold 0.8

# Save results
ctxos risk -i entities.json -o risks.json
```

### `ctxos agent`

Run analysis agents for context analysis.

```bash
ctxos agent [agent] [options]
```

**Arguments:**
- `agent`: Agent type - `summarize`, `gap-detect`, `hypothesis`, `explain`, `all` (default: all)

**Options:**
- `-i, --input FILE`: Input file (JSON) with context data (required)
- `-o, --output FILE`: Output file for agent results
- `--timeout SECONDS`: Execution timeout (default: 300)

**Examples:**
```bash
# Run all agents
ctxos agent -i context.json

# Run specific agent
ctxos agent summarize -i context.json

# Detect gaps
ctxos agent gap-detect -i context.json -o gaps.json

# Generate hypothesis with custom timeout
ctxos agent hypothesis -i context.json --timeout 600
```

## Configuration Files

CtxOS uses YAML configuration files for project settings.

### Default Config Location
- `configs/default.yaml` (if not specified with `--config`)

### Config Structure
```yaml
# Project settings
project:
  name: "default"
  description: "CtxOS default project"

# Collector configuration
collectors:
  dns:
    enabled: true
    timeout: 30
  osint:
    enabled: true
    timeout: 60
  recon:
    enabled: true
    parallel: 4

# Engine configuration
engines:
  risk:
    enabled: true
    model: "default"
  exposure:
    enabled: true
  drift:
    enabled: false

# Output settings
output:
  format: "json"
  indent: 2
  include_metadata: true
```

## Shell Completions

CtxOS provides completions for bash, zsh, and fish shells.

### Installation

```bash
# Install all completions
ctxos-install-completions

# Or manually
sudo cp cli/completion/ctxos_completion.bash /etc/bash_completion.d/ctxos
sudo cp cli/completion/ctxos_completion.zsh /usr/share/zsh/site-functions/_ctxos
cp cli/completion/ctxos_completion.fish ~/.config/fish/completions/ctxos.fish
```

### Usage

```bash
# Show available commands
ctxos <TAB>

# Show command options
ctxos collect <TAB>

# Show option values
ctxos graph --format <TAB>
```

## Examples

### Complete Workflow

```bash
# 1. Collect data
ctxos collect example.com -o entities.json --verbose

# 2. Build graph
ctxos graph -i entities.json -f json -o graph.json

# 3. Calculate risks
ctxos risk -i entities.json -o risks.json

# 4. Run analysis
ctxos agent -i entities.json -o analysis.json

# 5. View results
cat analysis.json
```

### Multi-Project Setup

```bash
# Work with different projects
ctxos --project project-a collect target.com
ctxos --project project-b collect target.com

# Use different configs
ctxos --config configs/production.yaml collect example.com
ctxos --config configs/staging.yaml collect staging.example.com
```

### Parallel Collection

```bash
# Fast collection with 8 parallel workers
ctxos collect example.com --parallel 8 --source all
```

### Generate Reports

```bash
# Collect, analyze, and save everything
ctxos collect example.com -o data.json
ctxos graph -i data.json -o graph.json -f graphml
ctxos risk -i data.json -o risks.json
ctxos agent -i data.json -o analysis.json

# Create a summary
echo "=== Collection Report ===" > report.txt
echo "Data points: $(jq '.entities | length' data.json)" >> report.txt
echo "Risks identified: $(jq '.risks | length' risks.json)" >> report.txt
echo "Gaps detected: $(jq '.gaps | length' analysis.json)" >> report.txt
```

## Troubleshooting

### Command Not Found
```bash
# Install the package
pip install -e .

# Or add to PATH
export PATH="/path/to/cli:$PATH"
```

### Permission Denied
```bash
# Make script executable
chmod +x cli/ctxos.py

# Or run with python
python cli/ctxos.py collect example.com
```

### Config File Not Found
```bash
# Specify full path
ctxos --config /absolute/path/to/config.yaml collect example.com

# Or set environment variable
export CTXOS_CONFIG=/path/to/config.yaml
ctxos collect example.com
```

### Debug Output
```bash
# Enable debug logging
ctxos --debug collect example.com

# Or verbose output
ctxos --verbose collect example.com
```

## Exit Codes

- `0`: Success
- `1`: Command failed or invalid arguments
- `2`: Missing required file or configuration
- `3`: Permission denied
- `4`: Timeout

## Best Practices

1. **Use project names** to organize work by customer or engagement
2. **Set environment variables** to avoid repeating options
3. **Enable verbose mode** when troubleshooting
4. **Save outputs** for later analysis and reporting
5. **Use shell completions** for faster command entry
6. **Check configs** before collecting from production systems

## Advanced Usage

### Custom Configurations

Create project-specific configs:

```bash
mkdir -p configs
cp configs/default.yaml configs/my-project.yaml

# Edit my-project.yaml with project-specific settings
ctxos --config configs/my-project.yaml collect example.com
```

### Piping and Scripting

```bash
# Pipe results to jq for processing
ctxos collect example.com -o data.json
jq '.entities[] | .name' data.json

# Use in scripts
for domain in $(cat domains.txt); do
  ctxos collect "$domain" -o "results/$domain.json"
done
```

### Integration with Other Tools

```bash
# Export for use in other systems
ctxos risk -i entities.json --engine all -o risk-report.json
jq . risk-report.json | send-to-siem
```

## Getting Help

```bash
# Show general help
ctxos --help

# Show command-specific help
ctxos collect --help
ctxos graph --help
ctxos risk --help
ctxos agent --help

# Enable debug output
ctxos --debug <command>
```
