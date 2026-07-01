# poukmaranatha

## Cloning

This repo is owned by the `yosuasimanjuntak` GitHub account. If your machine's
default SSH key (`~/.ssh/id_ed25519`) is registered under a different GitHub
account, cloning with the plain `git@github.com:...` URL will fail with
`Permission denied (publickey)`.

Check `~/.ssh/config` for a host alias tied to the correct key, e.g.:

```
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
```

Then clone using that alias instead of `github.com`:

```bash
git clone git@github-personal:yosuasimanjuntak/poukmaranatha.git
```

To check which account an SSH key authenticates as:

```bash
ssh -i ~/.ssh/id_ed25519_personal -T git@github.com
```