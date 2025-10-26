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
    return any(tag.lower() in [t.lower() for t in topics] for tag in TARGET_TAGS)

def get_repo_image(repo_name: str, default_img: str) -> str:
    """Get repository social preview image or default"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Try to get social preview image
            if data.get("owner", {}).get("avatar_url"):
                return f"https://opengraph.githubassets.com/1/{GITHUB_USERNAME}/{repo_name}"
    except:
        pass
    
    return default_img

def generate_project_cards(repos: List[Dict]) -> str:
    """Generate markdown for project cards"""
    if not repos:
        return "_No projects found with the specified tags yet. Check back soon! 🚀_\n"
    
    cards_md = ""
    default_image = "https://via.placeholder.com/600x300/1a1b27/58a6ff?text=Project+Preview"
    
    for repo in repos:
        name = repo.get("name", "Unknown")
        desc = repo.get("description", "No description available.")
        url = repo.get("html_url", "#")
        topics = repo.get("topics", [])
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language", "N/A")
        
        # Get repository image
        img_url = get_repo_image(name, default_image)
        
        # Format topics as badges
        topic_badges = " ".join([f"`{topic}`" for topic in topics if topic in [t.lower() for t in TARGET_TAGS]])
        
        # Create card
        card = f"""
<div align="center">

### 🔥 [{name}]({url})

<img src="{img_url}" alt="{name}" width="600" style="border-radius: 10px; margin: 20px 0;">

{topic_badges}

**{desc}**

⭐ Stars: `{stars}` | 💻 Language: `{language}`

[View Project →]({url})

---

</div>
"""
        cards_md += card
    
    return cards_md

def update_readme(projects_md: str):
    """Update README.md with new projects section"""
    readme_path = "README.md"
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Pattern to find the projects section
        pattern = r"(<!--START_PROJECTS_LIST-->)(.*?)(<!--END_PROJECTS_LIST-->)"
        
        # Replace the content between markers
        new_content = re.sub(
            pattern,
            f"\\1\n\n## 🚀 Featured Projects\n\n{projects_md}\n\\3",
            content,
            flags=re.DOTALL
        )
        
        # Write back
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("✅ README.md updated successfully!")
        
    except FileNotFoundError:
        print("❌ README.md not found!")
    except Exception as e:
        print(f"❌ Error updating README: {e}")

def main():
    """Main execution"""
    print("🔍 Fetching GitHub repositories...")
    all_repos = fetch_github_repos()
    
    print(f"📦 Found {len(all_repos)} total repositories")
    
    # Filter repos with target tags
    filtered_repos = [
        repo for repo in all_repos 
        if has_target_tags(repo.get("topics", []))
    ]
    
    print(f"🎯 Found {len(filtered_repos)} projects with target tags: {', '.join(TARGET_TAGS)}")
    
    # Sort by stars and update date
    filtered_repos.sort(key=lambda x: (x.get("stargazers_count", 0), x.get("updated_at", "")), reverse=True)
    
    # Generate markdown
    projects_md = generate_project_cards(filtered_repos)
    
    # Update README
    update_readme(projects_md)
    
    print("🎉 Process completed!")

if __name__ == "__main__":
    main()