import os
import re
import requests
from typing import List, Dict

# GitHub Configuration
GITHUB_USERNAME = "noobhacker02"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TARGET_TAGS = ["rag", "lln", "shwcase", "ai"]

def fetch_github_repos() -> List[Dict]:
    """Fetch all repositories for the user"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&sort=updated"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching repos: {e}")
        return []

def has_target_tags(topics: List[str]) -> bool:
    """Check if repo has any of our target tags"""
    if not topics:
        return False
    topics_lower = [t.lower() for t in topics]
    return any(tag.lower() in topics_lower for tag in TARGET_TAGS)

def get_repo_image(repo_name: str) -> str:
    """Get repository social preview image"""
    return f"https://opengraph.githubassets.com/1/{GITHUB_USERNAME}/{repo_name}"

def generate_project_cards(repos: List[Dict]) -> str:
    """Generate markdown for project cards in responsive 2-column layout with dark mode support"""
    if not repos:
        print("⚠️ No projects to display")
        return "\n## 🚀 Featured Projects\n\n_No projects found with the specified tags yet. Tag your repos with `rag`, `lln`, `showcase`, or `ai` to display them here! 🚀_\n\n"
    
    # Add CSS for responsive grid and dark mode
    cards_md = """
## 🚀 Featured Projects

<style>
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin: 20px 0;
}

.project-card {
  background: linear-gradient(145deg, #1a1b27 0%, #1f2937 100%);
  border: 1px solid #374151;
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
}

.project-card:hover {
  transform: translateY(-8px);
  border-color: #3b82f6;
  box-shadow: 0 12px 24px rgba(59, 130, 246, 0.3);
}

.project-card img {
  border-radius: 12px;
  width: 100%;
  height: auto;
  margin: 16px 0;
  border: 1px solid #374151;
}

.project-title {
  color: #f9fafb;
  font-size: 1.5em;
  font-weight: 700;
  margin: 16px 0 12px 0;
  text-decoration: none;
}

.project-title:hover {
  color: #60a5fa;
}

.project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
  justify-content: center;
}

.project-tag {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: #fff;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
  text-transform: lowercase;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.project-desc {
  color: #d1d5db;
  font-size: 1em;
  line-height: 1.6;
  margin: 16px 0;
}

.project-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin: 16px 0;
  color: #9ca3af;
  font-size: 0.9em;
}

.project-stats span {
  background: #111827;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #374151;
}

.project-link {
  display: inline-block;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  margin-top: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.project-link:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.6);
}

@media (max-width: 768px) {
  .projects-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-color-scheme: light) {
  .project-card {
    background: linear-gradient(145deg, #ffffff 0%, #f9fafb 100%);
    border-color: #e5e7eb;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .project-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 12px 24px rgba(59, 130, 246, 0.2);
  }
  
  .project-title {
    color: #111827;
  }
  
  .project-desc {
    color: #4b5563;
  }
  
  .project-stats {
    color: #6b7280;
  }
  
  .project-stats span {
    background: #f3f4f6;
    border-color: #e5e7eb;
  }
  
  .project-card img {
    border-color: #e5e7eb;
  }
}
</style>

<div class="projects-grid">
"""
    
    # Generate individual cards
    for repo in repos:
        cards_md += generate_single_card(repo)
    
    cards_md += "\n</div>\n\n"
    
    return cards_md

def generate_single_card(repo: Dict) -> str:
    """Generate a single project card with modern styling"""
    name = repo.get("name", "Unknown")
    desc = repo.get("description") or "No description available."
    url = repo.get("html_url", "#")
    topics = repo.get("topics", [])
    stars = repo.get("stargazers_count", 0)
    language = repo.get("language") or "N/A"
    
    # Get repository image
    img_url = get_repo_image(name)
    
    # Format topics as badges (keep ALL topics including showcase)
    topic_badges = "".join([
        f'<span class="project-tag">{topic}</span>' 
        for topic in topics 
        if topic.lower() in [t.lower() for t in TARGET_TAGS]
    ])
    
    # Add emoji based on language
    lang_emoji = {
        "Python": "🐍",
        "JavaScript": "⚡",
        "TypeScript": "💙",
        "Java": "☕",
        "Go": "🔷",
        "Rust": "🦀",
        "C++": "⚙️",
        "HTML": "🌐",
    }.get(language, "💻")
    
    # Create card
    return f"""
<div class="project-card">
  <div align="center">
    <a href="{url}" class="project-title">🔥 {name}</a>
    <img src="{img_url}" alt="{name} preview">
    <div class="project-tags">
      {topic_badges}
    </div>
    <p class="project-desc">{desc}</p>
    <div class="project-stats">
      <span>⭐ {stars}</span>
      <span>{lang_emoji} {language}</span>
    </div>
    <a href="{url}" class="project-link">View Project →</a>
  </div>
</div>
"""

def update_readme(projects_md: str):
    """Update README.md with new projects section"""
    readme_path = "README.md"
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"📄 Original README length: {len(content)} characters")
        
        # Check if markers exist
        if "<!--START_PROJECTS_LIST-->" not in content or "<!--END_PROJECTS_LIST-->" not in content:
            print("❌ ERROR: Project markers not found in README.md")
            print("Make sure your README contains:")
            print("<!--START_PROJECTS_LIST-->")
            print("<!--END_PROJECTS_LIST-->")
            return
        
        # Pattern to find the projects section
        pattern = r"(<!--START_PROJECTS_LIST-->)(.*?)(<!--END_PROJECTS_LIST-->)"
        
        # Replace the content between markers
        new_content = re.sub(
            pattern,
            f"\\1{projects_md}\\3",
            content,
            flags=re.DOTALL
        )
        
        print(f"📝 New README length: {len(new_content)} characters")
        print(f"📊 Added {len(new_content) - len(content)} characters")
        
        # Write back
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("✅ README.md updated successfully!")
        
        # Verify the update
        with open(readme_path, "r", encoding="utf-8") as f:
            verify_content = f.read()
            if "## 🚀 Featured Projects" in verify_content:
                print("✅ Verified: Projects section was written!")
            else:
                print("⚠️ Warning: Projects section may not have been written")
        
    except FileNotFoundError:
        print("❌ README.md not found!")
    except Exception as e:
        print(f"❌ Error updating README: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    print("🔍 Fetching GitHub repositories...")
    all_repos = fetch_github_repos()
    
    print(f"📦 Found {len(all_repos)} total repositories")
    
    # Debug: Show all repo names and topics
    print("\n📋 Repository Topics:")
    for repo in all_repos:
        topics = repo.get("topics", [])
        print(f"  - {repo.get('name')}: {topics if topics else 'No topics'}")
    
    # Filter repos with target tags
    filtered_repos = [
        repo for repo in all_repos 
        if has_target_tags(repo.get("topics", []))
    ]
    
    print(f"\n🎯 Found {len(filtered_repos)} projects with target tags: {', '.join(TARGET_TAGS)}")
    
    if filtered_repos:
        print("\n✨ Filtered projects:")
        for repo in filtered_repos:
            print(f"  - {repo.get('name')} (topics: {repo.get('topics', [])})")
    
    # Sort by stars and update date
    filtered_repos.sort(key=lambda x: (x.get("stargazers_count", 0), x.get("updated_at", "")), reverse=True)
    
    # Generate markdown
    print("\n🎨 Generating project cards...")
    projects_md = generate_project_cards(filtered_repos)
    
    print(f"📏 Generated markdown length: {len(projects_md)} characters")
    print("\n" + "="*50)
    print("GENERATED MARKDOWN PREVIEW:")
    print("="*50)
    print(projects_md[:500] + "..." if len(projects_md) > 500 else projects_md)
    print("="*50 + "\n")
    
    # Update README
    print("📝 Updating README.md...")
    update_readme(projects_md)
    
    print("\n🎉 Process completed!")

if __name__ == "__main__":
    main()