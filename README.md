# dotfiles

# Install Latest Neovim
Reference: https://github.com/neovim/neovim/blob/master/INSTALL.md#linux

Download and extract the pre-built archive from the [Releases page](https://github.com/neovim/neovim/releases):
```
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
sudo rm -rf /opt/nvim-linux-x86_64
sudo tar -C /opt -xzf nvim-linux-x86_64.tar.gz
```

Then add this to your shell config (`~/.bashrc`, `~/.zshrc`, ...):
```
export PATH="$PATH:/opt/nvim-linux-x86_64/bin"
```

# Create symlinks
```
ln -s $HOME/repos/dotfiles/.vimrc $HOME/.vimrc
ln -s $HOME/repos/dotfiles/.jcarranz_rc $HOME/.jcarranz_rc
ln -s $HOME/repos/dotfiles/.tmux.conf $HOME/.tmux.conf
```

# Claude Code setup

This repo tracks Claude Code skills and settings under `.claude/`. Only the
specific items below are symlinked — the rest of `~/.claude/` is left alone
because it contains credentials, history, and auto-managed plugin data that
should not be in git.

```
ln -s $HOME/repos/dotfiles/.claude/skills $HOME/.claude/skills
ln -s $HOME/repos/dotfiles/.claude/settings.json $HOME/.claude/settings.json
```

The `skills/` symlink makes all custom skills available globally in every
Claude Code session. Skills added under `.claude/skills/` in this repo are
automatically picked up once the symlink is in place.

# Modify VIMINIT
```
export MYVIMRC=$HOME/.vimrc
export VIMINIT='source $MYVIMRC'
```

# Add below lines in .bashrc file
```
if [ -f ~/.jcarranz_rc ]; then
    . ~/.jcarranz_rc
fi
```

# Download Bundle
```
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
```

Open vim and Run PluginInstall

# Create git aliasesvimrc
```
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
```
# Install Oh my Posh Ubuntu
https://calebschoepp.com/blog/2021/how-to-setup-oh-my-posh-on-ubuntu/
My Font: MesloLGLDZ Nerd Font Mono

# Other helpfull links
https://vi.stackexchange.com/questions/3359/how-do-i-fix-the-status-bar-symbols-in-the-airline-plugin
https://docs.microsoft.com/en-us/windows/terminal/tutorials/custom-prompt-setup#install-a-nerd-font
https://learn.microsoft.com/en-us/windows/terminal/tutorials/custom-prompt-setup#customize-your-wsl-prompt-with-oh-my-posh
https://windowsterminalthemes.dev

# Key remmaping (Ubuntu)
Install input remmapper from https://github.com/sezanzeb/input-remapper

Then do custom remapping

![Screenshot](images/input_remmaper.png)


# Note taking APP
joplin
https://joplinapp.org/help/#desktop-applications

Installation
```
wget -O - https://raw.githubusercontent.com/laurent22/joplin/dev/Joplin_install_and_update.sh | bash
```
