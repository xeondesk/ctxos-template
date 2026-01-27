#!/bin/bash
# bash completion script for ctxos CLI
# Installation: cp ctxos_completion.bash /etc/bash_completion.d/ctxos
# Or source it in ~/.bashrc: source /path/to/ctxos_completion.bash

_ctxos_completion() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    commands="collect graph risk agent"
    
    # Global options
    opts="--project --config --verbose --debug --version --help"
    
    # If we're completing the command itself
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands} ${opts}" -- ${cur}) )
        return 0
    fi
    
    # Collect command completions
    if [[ "${COMP_WORDS[1]}" == "collect" ]]; then
        case "${prev}" in
            -s|--source)
                COMPREPLY=( $(compgen -W "all dns osint recon cloud vuln" -- ${cur}) )
                return 0
                ;;
            -o|--output)
                COMPREPLY=( $(compgen -f -- ${cur}) )
                return 0
                ;;
            *)
                COMPREPLY=( $(compgen -W "--source --output --parallel --project --config --verbose --debug --help" -- ${cur}) )
                return 0
                ;;
        esac
    fi
    
    # Graph command completions
    if [[ "${COMP_WORDS[1]}" == "graph" ]]; then
        case "${prev}" in
            -f|--format)
                COMPREPLY=( $(compgen -W "json graphml dot png" -- ${cur}) )
                return 0
                ;;
            -i|--input|-o|--output)
                COMPREPLY=( $(compgen -f -- ${cur}) )
                return 0
                ;;
            *)
                if [[ "${cur}" != -* ]]; then
                    COMPREPLY=( $(compgen -W "build analyze export visualize" -- ${cur}) )
                else
                    COMPREPLY=( $(compgen -W "--input --output --format --project --config --verbose --debug --help" -- ${cur}) )
                fi
                return 0
                ;;
        esac
    fi
    
    # Risk command completions
    if [[ "${COMP_WORDS[1]}" == "risk" ]]; then
        case "${prev}" in
            --engine)
                COMPREPLY=( $(compgen -W "risk exposure drift all" -- ${cur}) )
                return 0
                ;;
            -i|--input|-o|--output)
                COMPREPLY=( $(compgen -f -- ${cur}) )
                return 0
                ;;
            *)
                COMPREPLY=( $(compgen -W "--input --output --engine --threshold --project --config --verbose --debug --help" -- ${cur}) )
                return 0
                ;;
        esac
    fi
    
    # Agent command completions
    if [[ "${COMP_WORDS[1]}" == "agent" ]]; then
        case "${prev}" in
            -i|--input|-o|--output)
                COMPREPLY=( $(compgen -f -- ${cur}) )
                return 0
                ;;
            *)
                if [[ "${cur}" != -* ]]; then
                    COMPREPLY=( $(compgen -W "summarize gap-detect hypothesis explain all" -- ${cur}) )
                else
                    COMPREPLY=( $(compgen -W "--input --output --timeout --project --config --verbose --debug --help" -- ${cur}) )
                fi
                return 0
                ;;
        esac
    fi
    
    # Default completions
    COMPREPLY=( $(compgen -W "${opts} ${commands}" -- ${cur}) )
}

complete -o bashdefault -o default -o nospace -F _ctxos_completion ctxos
