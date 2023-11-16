import os
from datetime import datetime, timedelta, timezone

import requests


def run_query(query, variables, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
    json_data = {"query": query, "variables": variables}

    response = requests.post(url, headers=headers, json=json_data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to execute GraphQL query. Status code: {response.status_code}")
        print(response.text)
        return None


# 替换为你的 GitHub 用户名、仓库名和访问令牌
owner = "naosense"
repo = "naosense.github.io"
token = os.getenv("GH_TOKEN")

# GraphQL 查询
query = """
query GetDiscussions($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    discussions(first: 1, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        id
        title
        body
        category {
          name
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
      }
    }
  }
}
"""

if __name__ == "__main__":
    variables = {"owner": owner, "repo": repo}
    result = run_query(query, variables, token)

    if result:
        discussions = (
            result.get("data", {})
            .get("repository", {})
            .get("discussions", {})
            .get("nodes", [])
        )
        for discussion in discussions:
            title = discussion["title"]
            body = discussion["body"]
            category = discussion["category"]
            labels = discussion.get("labels", {}).get("nodes", [])
            label_names = [label["name"] for label in labels]
            if category["name"] == "Blogs":
                md_path = f"source/_posts/{title}.md"
                if "delete" in label_names:
                    if os.path.exists(md_path):
                        os.remove(md_path)
                        print(f"delete {title}")
                elif "done" in label_names:
                    label_names.remove("done")
                    label_str = f"[{', '.join(label_names)}]" if label_names else ""
                    tz_east_8 = timezone(timedelta(hours=8))
                    now_localized = datetime.now().astimezone(tz_east_8)
                    with open(md_path, "w+") as md:
                        md.write("---\n")
                        md.write(f"title: {title}\n")
                        md.write(f"date: {now_localized:%Y-%m-%d %H:%M:%S}\n")
                        md.write("categories: \n")
                        md.write(f"tags: {label_str}\n")
                        md.write("---\n")
                        md.write(f"{body}\n")
                        print(f"create or update {title}")
                else:
                    print(f"{title} is not ready.")
            else:
                print(f"{title} is not blog.")
    else:
        print("No discussion.")
