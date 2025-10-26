import os
import re
import requests
from typing import List, Dict

# GitHub Configuration
GITHUB_USERNAME = "noobhacker02"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TARGET_TAGS = ["rag", "lln", "showcase", "ai"]

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
    """Generate markdown for project cards in responsive layout using HTML tables"""
    if not repos:
        print("⚠️ No projects to display")
        return "\n## 🚀 Featured Projects\n\n_No projects found with the specified tags yet. Tag your repos with `rag`, `lln`, `showcase`, or `ai` to display them here! 🚀_\n\n"
    
    cards_md = "\n## 🚀 Featured Projects\n\n"
    
    # Process repos in pairs for 2-column layout
    for i in range(0, len(repos), 2):
        # Start row
        cards_md += '<table><tr>\n'
        
        # First card
        repo = repos[i]
        cards_md += generate_single_card(repo)
        
        # Second card (if exists)
        if i + 1 < len(repos):
            repo = repos[i + 1]
            cards_md += generate_single_card(repo)
        else:
            # Empty cell if odd number of projects
            cards_md += '<td width="50%"></td>\n'
        
        cards_md += '</tr></table>\n\n'
    
    return cards_md

def generate_single_card(repo: Dict) -> str:
    """Generate a single project card with inline styles"""
    name = repo.get("name", "Unknown")
    desc = repo.get("description") or "No description available."
    url = repo.get("html_url", "#")
    topics = repo.get("topics", [])
    stars = repo.get("stargazers_count", 0)
    language = repo.get("language") or "N/A"
    
    # Get repository image
    img_url = get_repo_image(name)
    
    # Format topics as styled badges (keep ALL target tags including showcase)
    topic_badges = " ".join([
        f'<img src="https://img.shields.io/badge/{topic}-blueviolet?style=for-the-badge" alt="{topic}">'
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
        "Jupyter Notebook": "📓",
    }.get(language, "💻")
    
    # Create card with inline styles
    return f'''<td width="50%" valign="top">
<div align="center" style="padding: 20px; border: 2px solid #30363d; border-radius: 12px; background: linear-gradient(145deg, #0d1117 0%, #161b22 100%); margin: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);">

<h3 style="margin: 0;">
  <a href="{url}" style="color: #58a6ff; text-decoration: none;">
    🔥 {name}
  </a>
</h3>

<a href="{url}">
  <img src="{img_url}" alt="{name}" width="100%" style="border-radius: 8px; margin: 16px 0; border: 1px solid #30363d;">
</a>

<p style="margin: 12px 0;">
  {topic_badges}
</p>

<p style="color: #c9d1d9; font-size: 14px; line-height: 1.6; margin: 16px 0;">
  {desc}
</p>

<p style="margin: 16px 0;">
  <img src="https://img.shields.io/badge/⭐_Stars-{stars}-yellow?style=flat-square" alt="stars">
  <img src="https://img.shields.io/badge/{lang_emoji}_{language.replace(' ', '_')}-informational?style=flat-square" alt="language">
</p>

<a href="{url}" style="display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #1f6feb 0%, #1158c7 100%); color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 8px;">
  View Project →
</a>

</div>
</td>
'''

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