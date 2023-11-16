import os

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
        labels(first: 5) {
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
            title = {discussion["title"]}
            body = {discussion["body"]}
            labels = discussion.get("labels", {}).get("nodes", [])
            label_names = [label["name"] for label in labels]
            label_str = ", ".join(label_names)
            print(f"Labels: {label_str}")
            if "blog" in label_names:
                md_path = f"source/_post/{title}.md"
                if "delete" in label_names:
                    if os.path.exists(md_path):
                        os.remove(md_path)
                elif "done" in label_names:
                    with open(md_path, "w+") as md:
                        md.write("---\n")
                        md.write(f"title: {title}\n")
                        md.write(f"date: {title}\n")
                        md.write("categories: \n")
                        md.write(f"tags: [{label_str}]\n")
                        md.write("---\n")
                        md.write(f"{body}\n")
                else:
                    print("Discussion is not ready.")
                    exit(-1)
            else:
                print("Discussion is not blog.")
                exit(-1)
    else:
        print("No discussion.")
        exit(-1)
