#compdef ctxos

# Zsh completion script for ctxos CLI
# Installation: cp ctxos_completion.zsh /usr/share/zsh/site-functions/_ctxos

_ctxos() {
    local ret=1
    local -a state line
    local -A opt_args
    
    _arguments -C \
        '(-v --version)'{-v,--version}'[Show version]' \
        '(-p --project)'{-p,--project}'[Project name]:project:' \
        '(-c --config)'{-c,--config}'[Config file]:config file:_files' \
        '--verbose[Enable verbose output]' \
        '--debug[Enable debug mode]' \
        '(-h --help)'{-h,--help}'[Show help]' \
        '*::command:->command' \
        && ret=0
    
    case $state in
        command)
            local -a commands
            commands=(
                'collect:Collect signals from configured sources'
                'graph:Build and analyze entity graphs'
                'risk:Calculate risk scores for entities'
                'agent:Run analysis agents'
            )
            _describe 'command' commands
            ;;
    esac
    
    case $words[1] in
        collect)
            _ctxos_collect
            ;;
        graph)
            _ctxos_graph
            ;;
        risk)
            _ctxos_risk
            ;;
        agent)
            _ctxos_agent
            ;;
    esac
    
    return $ret
}

_ctxos_collect() {
    _arguments \
        'target::Target domain or asset' \
        '(-s --source)'{-s,--source}'[Collector source]:(all dns osint recon cloud vuln)' \
        '(-o --output)'{-o,--output}'[Output file]:file:_files' \
        '--parallel[Number of parallel collectors]:workers:(1 2 4 8 16)' \
        '(-p --project)'{-p,--project}'[Project name]:project:' \
        '(-c --config)'{-c,--config}'[Config file]:config file:_files' \
        '--verbose[Verbose output]' \
        --help'[Show help]'
}

_ctxos_graph() {
    _arguments \
        'action::Graph action:(build analyze export visualize)' \
        '(-i --input)'{-i,--input}'[Input file]:file:_files' \
        '(-o --output)'{-o,--output}'[Output file]:file:_files' \
        '(-f --format)'{-f,--format}'[Output format]:(json graphml dot png)' \
        '(-p --project)'{-p,--project}'[Project name]:project:' \
        '(-c --config)'{-c,--config}'[Config file]:config file:_files' \
        '--verbose[Verbose output]' \
        --help'[Show help]'
}

_ctxos_risk() {
    _arguments \
        '(-i --input)'{-i,--input}'[Input file]:file:_files' \
        '(-o --output)'{-o,--output}'[Output file]:file:_files' \
        '--engine[Scoring engine]:(risk exposure drift all)' \
        '--threshold[Risk threshold]:threshold:(0.5 0.7 0.9)' \
        '(-p --project)'{-p,--project}'[Project name]:project:' \
        '(-c --config)'{-c,--config}'[Config file]:config file:_files' \
        '--verbose[Verbose output]' \
        --help'[Show help]'
}

_ctxos_agent() {
    _arguments \
        'agent::Agent type:(summarize gap-detect hypothesis explain all)' \
        '(-i --input)'{-i,--input}'[Input file]:file:_files' \
        '(-o --output)'{-o,--output}'[Output file]:file:_files' \
        '--timeout[Execution timeout]:seconds:(60 300 600 1800)' \
        '(-p --project)'{-p,--project}'[Project name]:project:' \
        '(-c --config)'{-c,--config}'[Config file]:config file:_files' \
        '--verbose[Verbose output]' \
        --help'[Show help]'
}

_ctxos
