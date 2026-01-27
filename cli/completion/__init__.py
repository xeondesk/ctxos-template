"""
Autocompletion support for ctxos CLI.

Provides utilities to generate and install shell completions.
"""

import os
import sys
from pathlib import Path


class CompletionInstaller:
    """Install shell completions for ctxos."""
    
    BASH_DIR = "/etc/bash_completion.d"
    ZSH_DIR = "/usr/share/zsh/site-functions"
    FISH_DIR = os.path.expanduser("~/.config/fish/completions")
    
    def __init__(self, cli_dir: str = None):
        """Initialize installer."""
        if cli_dir is None:
            cli_dir = os.path.dirname(__file__)
        self.cli_dir = cli_dir
        self.completion_dir = os.path.join(cli_dir, "completion")
    
    def get_bash_script(self) -> str:
        """Get bash completion script path."""
        return os.path.join(self.completion_dir, "ctxos_completion.bash")
    
    def get_zsh_script(self) -> str:
        """Get zsh completion script path."""
        return os.path.join(self.completion_dir, "ctxos_completion.zsh")
    
    def get_fish_script(self) -> str:
        """Get fish completion script path."""
        return os.path.join(self.completion_dir, "ctxos_completion.fish")
    
    def install_bash(self, verbose: bool = False) -> bool:
        """Install bash completions."""
        if not os.path.exists(self.get_bash_script()):
            print(f"Error: Bash completion script not found at {self.get_bash_script()}")
            return False
        
        if not os.access(self.BASH_DIR, os.W_OK):
            print(f"Warning: Cannot write to {self.BASH_DIR} (permission denied)")
            print(f"Manual installation: cp {self.get_bash_script()} {self.BASH_DIR}/ctxos")
            return False
        
        try:
            with open(self.get_bash_script(), "r") as src:
                content = src.read()
            
            dest = os.path.join(self.BASH_DIR, "ctxos")
            with open(dest, "w") as f:
                f.write(content)
            
            os.chmod(dest, 0o644)
            
            if verbose:
                print(f"✓ Installed bash completion to {dest}")
            
            return True
        except Exception as e:
            print(f"Error installing bash completion: {e}")
            return False
    
    def install_zsh(self, verbose: bool = False) -> bool:
        """Install zsh completions."""
        if not os.path.exists(self.get_zsh_script()):
            print(f"Error: Zsh completion script not found at {self.get_zsh_script()}")
            return False
        
        if not os.path.exists(self.ZSH_DIR):
            print(f"Warning: {self.ZSH_DIR} does not exist")
            print(f"Manual installation: cp {self.get_zsh_script()} {self.ZSH_DIR}/_ctxos")
            return False
        
        if not os.access(self.ZSH_DIR, os.W_OK):
            print(f"Warning: Cannot write to {self.ZSH_DIR} (permission denied)")
            print(f"Manual installation: cp {self.get_zsh_script()} {self.ZSH_DIR}/_ctxos")
            return False
        
        try:
            with open(self.get_zsh_script(), "r") as src:
                content = src.read()
            
            dest = os.path.join(self.ZSH_DIR, "_ctxos")
            with open(dest, "w") as f:
                f.write(content)
            
            os.chmod(dest, 0o644)
            
            if verbose:
                print(f"✓ Installed zsh completion to {dest}")
            
            return True
        except Exception as e:
            print(f"Error installing zsh completion: {e}")
            return False
    
    def install_fish(self, verbose: bool = False) -> bool:
        """Install fish completions."""
        if not os.path.exists(self.get_fish_script()):
            print(f"Error: Fish completion script not found at {self.get_fish_script()}")
            return False
        
        # Create directory if it doesn't exist
        os.makedirs(self.FISH_DIR, exist_ok=True)
        
        try:
            with open(self.get_fish_script(), "r") as src:
                content = src.read()
            
            dest = os.path.join(self.FISH_DIR, "ctxos.fish")
            with open(dest, "w") as f:
                f.write(content)
            
            os.chmod(dest, 0o644)
            
            if verbose:
                print(f"✓ Installed fish completion to {dest}")
            
            return True
        except Exception as e:
            print(f"Error installing fish completion: {e}")
            return False
    
    def install_all(self, verbose: bool = False) -> None:
        """Install all available completions."""
        print("Installing shell completions for ctxos...")
        
        results = {
            "bash": self.install_bash(verbose),
            "zsh": self.install_zsh(verbose),
            "fish": self.install_fish(verbose),
        }
        
        print("\nInstallation summary:")
        for shell, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"  {shell}: {status}")
        
        # Print instructions
        print("\nTo use completions:")
        print("  • Bash: restart your shell or run: source /etc/bash_completion.d/ctxos")
        print("  • Zsh: restart your shell or run: rehash")
        print("  • Fish: completions should work immediately")


def generate_completion_docs() -> str:
    """Generate documentation for completions."""
    return """
# Shell Completions for ctxos

CtxOS provides shell completion scripts for bash, zsh, and fish shells.

## Installation

### Bash
```bash
sudo cp cli/completion/ctxos_completion.bash /etc/bash_completion.d/ctxos
```

Then source in ~/.bashrc:
```bash
source /etc/bash_completion.d/ctxos
```

### Zsh
```bash
sudo cp cli/completion/ctxos_completion.zsh /usr/share/zsh/site-functions/_ctxos
```

### Fish
```bash
cp cli/completion/ctxos_completion.fish ~/.config/fish/completions/ctxos.fish
```

## Usage

After installation, type `ctxos` and press TAB to see available commands and options.

Examples:
```bash
ctxos <TAB>                    # Show available commands
ctxos collect <TAB>            # Show collect options
ctxos graph --format <TAB>     # Show format choices
ctxos risk --engine <TAB>      # Show engine choices
```

## Automated Installation

You can use the Python installer:

```bash
python -c "from cli.completion import CompletionInstaller; CompletionInstaller().install_all(verbose=True)"
```

Or with sudo if writing to system directories:

```bash
sudo python -c "from cli.completion import CompletionInstaller; CompletionInstaller().install_all(verbose=True)"
```
"""
