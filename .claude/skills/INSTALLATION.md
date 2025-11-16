# Sharing These Skills Across Repositories

This guide explains how to use these agent-role skills in other projects.

## Quick Install (Copy to Personal Skills)

**Recommended**: Makes skills available to ALL your repos

```bash
# From this repo root
cd /home/user/mini_agent

# Copy to personal skills (available everywhere)
cp -r .claude/skills/research-agent ~/.claude/skills/
cp -r .claude/skills/system-architect ~/.claude/skills/
cp -r .claude/skills/principal-engineer ~/.claude/skills/
cp -r .claude/skills/code-reviewer-advanced ~/.claude/skills/
cp -r .claude/skills/testing-agent ~/.claude/skills/

# Done! Skills now work in any repo
```

## Per-Project Install (Copy to Project Skills)

**Use when**: You want skills only in specific repos

```bash
# In another repo
cd /path/to/other-repo

# Create skills directory if needed
mkdir -p .claude/skills

# Copy skills from mini_agent
cp -r /home/user/mini_agent/.claude/skills/research-agent .claude/skills/
cp -r /home/user/mini_agent/.claude/skills/system-architect .claude/skills/
cp -r /home/user/mini_agent/.claude/skills/principal-engineer .claude/skills/
cp -r /home/user/mini_agent/.claude/skills/code-reviewer-advanced .claude/skills/
cp -r /home/user/mini_agent/.claude/skills/testing-agent .claude/skills/

# Optional: Add to git if you want to version them
git add .claude/skills/
git commit -m "feat: add agent-role skills"
```

## Advanced: Git Submodule (Version Controlled Sharing)

### Create Shared Skills Repo (One Time)

```bash
# Create a new repo for skills
mkdir ~/claude-agent-skills
cd ~/claude-agent-skills
git init

# Copy skills
cp -r /home/user/mini_agent/.claude/skills/research-agent .
cp -r /home/user/mini_agent/.claude/skills/system-architect .
cp -r /home/user/mini_agent/.claude/skills/principal-engineer .
cp -r /home/user/mini_agent/.claude/skills/code-reviewer-advanced .
cp -r /home/user/mini_agent/.claude/skills/testing-agent .
cp /home/user/mini_agent/.claude/skills/README.md .
cp /home/user/mini_agent/.claude/skills/SKILLS_VS_AGENTS.md .

# Commit
git add .
git commit -m "feat: initial agent-role skills collection"

# Push to GitHub (create repo first on GitHub)
git remote add origin https://github.com/YOUR_USERNAME/claude-agent-skills.git
git push -u origin main
```

### Use in Other Repos

```bash
# In any repo
cd /path/to/other-repo

# Remove existing skills if present
rm -rf .claude/skills

# Add as submodule
git submodule add https://github.com/YOUR_USERNAME/claude-agent-skills.git .claude/skills

# Commit
git add .gitmodules .claude/skills
git commit -m "feat: add agent-role skills via submodule"

# Later: Update to latest skills
git submodule update --remote .claude/skills
```

## Hybrid Approach (Recommended)

Use both personal AND project skills:

```
~/.claude/skills/              ← General skills (all repos)
├── research-agent/
├── system-architect/
├── principal-engineer/
├── code-reviewer-advanced/
└── testing-agent/

/your-repo/.claude/skills/     ← Project-specific overrides
├── custom-reviewer/           ← Project-specific skill
└── domain-expert/             ← Another custom skill
```

**Benefits**:
- General skills available everywhere (personal)
- Can override or extend per-project
- Maximum flexibility

## Updating Skills

### Personal Skills
```bash
# Update personal skills
cd /home/user/mini_agent
cp -r .claude/skills/research-agent ~/.claude/skills/
# Repeat for others...
```

### Project Skills
```bash
# Update in specific repo
cd /path/to/other-repo
cp -r /home/user/mini_agent/.claude/skills/research-agent .claude/skills/
git commit -am "chore: update agent skills"
```

### Submodule Skills
```bash
# In shared skills repo
cd ~/claude-agent-skills
# Make changes
git commit -am "feat: improve research-agent"
git push

# In repos using the submodule
cd /path/to/repo
git submodule update --remote .claude/skills
git commit -am "chore: update skills submodule"
```

## Skill Priority

When skills exist in multiple locations, Claude Code uses this priority:

1. **Project skills** (`.claude/skills/`) - Highest priority
2. **Personal skills** (`~/.claude/skills/`) - Fallback

So you can:
- Install general skills in `~/.claude/skills/`
- Override specific skills in project `.claude/skills/`

## Verification

Test that skills are available:

```bash
# List personal skills
ls ~/.claude/skills/

# List project skills
ls .claude/skills/

# In Claude Code, trigger a skill:
"Research the best database options"  # Should trigger research-agent
```

## Distribution to Team

### Option 1: Add to Project Repo
```bash
# Commit skills to project
git add .claude/skills/
git commit -m "feat: add agent-role skills"
git push

# Team members get them automatically
git pull
```

### Option 2: Share Installation Script
```bash
# create install-skills.sh
#!/bin/bash
SKILLS_REPO="https://github.com/YOUR_USERNAME/claude-agent-skills.git"
TEMP_DIR=$(mktemp -d)

git clone $SKILLS_REPO $TEMP_DIR
cp -r $TEMP_DIR/* ~/.claude/skills/
rm -rf $TEMP_DIR

echo "Skills installed to ~/.claude/skills/"
```

### Option 3: NPM Package (Advanced)
Create an NPM package for easy installation across projects.

## Troubleshooting

### Skills not activating?
- Verify files exist: `ls .claude/skills/skill-name/SKILL.md`
- Check YAML frontmatter has `name` and `description`
- Restart Claude Code session

### Submodule issues?
```bash
# Reinitialize submodule
git submodule deinit .claude/skills
git submodule update --init --recursive
```

### Permission issues?
```bash
# Fix permissions
chmod -R u+w ~/.claude/skills/
chmod -R u+w .claude/skills/
```

## Best Practices

1. **Use personal skills for general-purpose roles** (research, architect, engineer)
2. **Use project skills for domain-specific expertise** (mini_agent constitution, framework patterns)
3. **Version control project skills** (commit to repo)
4. **Document customizations** (note when you override personal skills)
5. **Update regularly** (keep skills in sync across machines)

## Examples

### Scenario 1: New Machine Setup
```bash
# Clone mini_agent
git clone https://github.com/YOUR_USERNAME/mini_agent.git
cd mini_agent

# Install skills globally
cp -r .claude/skills/* ~/.claude/skills/

# Now work on any project with these skills
cd ~/other-project
# Skills automatically available!
```

### Scenario 2: Team Project
```bash
# In team repo
git clone https://github.com/team/project.git
cd project

# Add skills as submodule (everyone gets them)
git submodule add https://github.com/YOUR_USERNAME/claude-agent-skills.git .claude/skills
git commit -m "feat: add agent skills"
git push

# Teammates:
git pull
git submodule update --init
# Skills available!
```

### Scenario 3: Mix and Match
```bash
# Personal skills (all repos)
cp -r .claude/skills/{research-agent,system-architect} ~/.claude/skills/

# Project-specific skills (this repo only)
# Keep code-reviewer-advanced in .claude/skills/ (uses mini_agent constitution)
git add .claude/skills/code-reviewer-advanced
git commit -m "feat: add mini_agent-specific code reviewer"
```

---

For questions or issues, refer to:
- `.claude/skills/README.md` - Skills setup guide
- `.claude/skills/SKILLS_VS_AGENTS.md` - Skills vs agents explanation
