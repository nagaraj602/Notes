# Github & Git Commands Cheat Sheet

> Essential Git source control and GitHub CLI commands for branching, rebase, merge conflicts, tags, and repo management.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `git clone --depth 1 --branch main https://github.com/org/repo.git` | Performs shallow clone with history truncated to 1 commit, saving massive network bandwidth and accelerating CI/CD container checkout. | Clone, CI/CD Performance |
| `git rebase -i HEAD~5` | Initiates interactive rebase over the last 5 commits to squash, edit, reorder, or drop commits before opening a clean Pull Request. | Branching, History Cleanup |
| `git rebase --onto main feat-base feature-branch` | Re-roots a feature branch onto main while dropping commits from upstream ancestor branch feat-base. Vital for multi-tier branch workflows. | Advanced Rebase |
| `git cherry-pick <commit-hash>` | Applies the exact changes introduced by a specific commit from another branch onto current HEAD without merging the entire branch. | Cherry-pick, Hotfix |
| `git cherry-pick --abort` | Aborts an in-progress cherry-pick conflict resolution and returns working tree cleanly to original state before cherry-pick was invoked. | Troubleshooting |
| `git stash push -u -m "WIP: auth refactor"` | Stashes all uncommitted tracked and untracked changes (-u) with a custom description message, leaving a pristine working directory. | Stashing |
| `git stash list && git stash pop stash@{0}` | Inspects all stashed work items and reapplies the latest stash while removing it from the stash stack. | Stashing |
| `git reset --soft HEAD~1` | Undoes the last commit while preserving all modified files in the staging area (index), allowing message fixes or re-committing with added files. | Commits, Undo |
| `git reset --hard HEAD~1` | Destructively discards the last commit and all associated working directory changes. Use with extreme caution. | Commits, Reset |
| `git reflog` | Chronological log of where HEAD and branch references have pointed. Lifesaver for locating and restoring orphaned commits or accidentally deleted branches. | Recovery, Reflog |
| `git branch -D <branch-name>` | Forcefully deletes a local branch even if its commits have not yet been merged into upstream or current branch. | Branching |
| `git push origin --delete <remote-branch>` | Deletes a remote branch on GitHub directly from CLI without logging into the web interface. | Remote, Branching |
| `git tag -a v1.2.0 -m "Release version 1.2.0" && git push origin v1.2.0` | Creates an annotated, signed release tag with message metadata and pushes it to GitHub, often triggering automated release pipelines. | Releases, Tags |
| `git log --graph --oneline --decorate --all -n 20` | Renders a visual ASCII graph showing branch divergences, merges, and tags across all local and remote branches. | Inspection, Log |
| `git diff --stat origin/main...HEAD` | Shows file change statistics and line addition/deletion counts between current feature branch and latest origin/main upstream. | Pull Request Review |
| `git clean -fd` | Forcefully removes all untracked files (-f) and directories (-d) from working tree. Useful for clearing rogue build artifacts before testing. | Clean-up |
| `git remote prune origin` | Cleans up obsolete remote-tracking branch references (e.g. origin/feature-xyz) whose corresponding branches have already been deleted on GitHub. | Maintenance |
| `gh pr create --title "feat: AWS EKS migration" --body "Resolves JIRA-840" --base main` | GitHub CLI: creates a Pull Request directly from current branch with title, description, and target branch. | GitHub CLI, Automation |
| `gh pr merge <PR-NUMBER> --squash --auto --delete-branch` | GitHub CLI: enables auto-merge to squash and merge PR upon passing all required status checks and delete the feature branch automatically. | GitHub CLI, Automation |
| `gh workflow run deploy.yml -f environment=staging` | GitHub CLI: triggers a GitHub Actions workflow dispatch event with custom input parameters directly from the terminal. | Actions, CI/CD |
