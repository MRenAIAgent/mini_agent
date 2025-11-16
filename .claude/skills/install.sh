#!/bin/bash
# Installation script for Claude Agent Role Skills
# Usage: ./install.sh [personal|project|submodule] [target-directory]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS=(
    "research-agent"
    "system-architect"
    "principal-engineer"
    "code-reviewer-advanced"
    "testing-agent"
)

DOCS=(
    "README.md"
    "SKILLS_VS_AGENTS.md"
    "INSTALLATION.md"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

show_usage() {
    cat << EOF
Claude Agent Role Skills - Installation Script

Usage:
    ./install.sh personal           # Install to ~/.claude/skills (all repos)
    ./install.sh project [DIR]      # Install to DIR/.claude/skills (default: current dir)
    ./install.sh list               # List available skills

Examples:
    ./install.sh personal                    # Install globally
    ./install.sh project                     # Install to current repo
    ./install.sh project /path/to/repo       # Install to specific repo

Skills included:
    - research-agent: Technology research and evaluation
    - system-architect: System design and architecture
    - principal-engineer: Implementation and technical leadership
    - code-reviewer-advanced: Code review and quality analysis
    - testing-agent: Testing strategy and execution

EOF
}

install_personal() {
    print_info "Installing skills to personal directory: ~/.claude/skills/"

    # Create directory if needed
    mkdir -p ~/.claude/skills

    # Copy skills
    for skill in "${SKILLS[@]}"; do
        if [ -d "$SCRIPT_DIR/$skill" ]; then
            cp -r "$SCRIPT_DIR/$skill" ~/.claude/skills/
            print_success "Installed: $skill"
        else
            print_error "Skill not found: $skill"
        fi
    done

    # Copy docs
    for doc in "${DOCS[@]}"; do
        if [ -f "$SCRIPT_DIR/$doc" ]; then
            cp "$SCRIPT_DIR/$doc" ~/.claude/skills/
            print_success "Installed: $doc"
        fi
    done

    print_success "Installation complete!"
    print_info "Skills are now available in ALL your repositories"
    echo ""
    echo "Test by asking Claude:"
    echo "  \"Research the best database options\""
    echo "  \"Design a scalable API system\""
    echo "  \"Implement user authentication\""
}

install_project() {
    local target_dir="${1:-.}"
    target_dir="$(cd "$target_dir" 2>/dev/null && pwd || echo "$target_dir")"

    print_info "Installing skills to project: $target_dir/.claude/skills/"

    # Create directory if needed
    mkdir -p "$target_dir/.claude/skills"

    # Copy skills
    for skill in "${SKILLS[@]}"; do
        if [ -d "$SCRIPT_DIR/$skill" ]; then
            cp -r "$SCRIPT_DIR/$skill" "$target_dir/.claude/skills/"
            print_success "Installed: $skill"
        else
            print_error "Skill not found: $skill"
        fi
    done

    # Copy docs
    for doc in "${DOCS[@]}"; do
        if [ -f "$SCRIPT_DIR/$doc" ]; then
            cp "$SCRIPT_DIR/$doc" "$target_dir/.claude/skills/"
            print_success "Installed: $doc"
        fi
    done

    print_success "Installation complete!"
    print_info "Skills are available in: $target_dir"
    echo ""
    print_info "To version control these skills:"
    echo "  cd $target_dir"
    echo "  git add .claude/skills/"
    echo "  git commit -m 'feat: add agent-role skills'"
}

list_skills() {
    echo "Available Skills:"
    echo ""
    for skill in "${SKILLS[@]}"; do
        if [ -f "$SCRIPT_DIR/$skill/SKILL.md" ]; then
            # Extract description from SKILL.md
            local desc=$(grep "^description:" "$SCRIPT_DIR/$skill/SKILL.md" | sed 's/description: //')
            echo -e "${GREEN}$skill${NC}"
            echo "  $desc"
            echo ""
        fi
    done

    echo "Documentation:"
    for doc in "${DOCS[@]}"; do
        echo "  - $doc"
    done
}

# Main script
case "${1:-}" in
    personal)
        install_personal
        ;;
    project)
        install_project "${2:-.}"
        ;;
    list)
        list_skills
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        print_error "No installation type specified"
        echo ""
        show_usage
        exit 1
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
