import os
import re
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


def save_assets_img_substitute_url(markdown_content, title):
    print("Going to save assets img")
    # 匹配 ![alt](url) 格式的图片
    markdown_img_pattern = (
        r"!\[(.*?)\]\((https://github\.com/naosense/naosense\.github\.io/assets.*?)\)"
    )
    markdown_image_matches = re.findall(markdown_img_pattern, markdown_content)

    # 匹配 <img src="url"> 格式的图片
    html_img_pattern = r'<img(?: alt="(.*?)")? src="(https://github\.com/naosense/naosense\.github\.io/assets[^"]*)"'
    html_image_matches = re.findall(html_img_pattern, markdown_content)

    # 合并两种格式的图片匹配结果
    image_matches = markdown_image_matches + html_image_matches
    print(f"Found img {image_matches}")

    img_dir_for_title = f"source/_posts/{title}"
    if image_matches and not os.path.exists(img_dir_for_title):
        os.makedirs(img_dir_for_title)

    # 保存图片并替换Markdown文本中的URL为本地路径
    for alt_text, img_url in image_matches:
        img_name = alt_text if alt_text else img_url.split("/")[-1]
        img_basename = img_name.split(".")[0].replace(" ", "_")
        img_extension = (
            img_name.split(".")[-1] if "." in img_name else "jpeg"
        )  # 提取图片后缀
        img_path = f"{img_dir_for_title}/{img_basename}.{img_extension}"

        # 下载图片
        response = requests.get(img_url)
        if response.status_code == 200:
            with open(img_path, "wb+") as img_file:
                print(f"Save img {img_path}")
                img_file.write(response.content)
        else:
            print(f"Failed to get img {img_url}. Status code: {response.status_code}")

        # 替换Markdown中的URL为本地路径
        markdown_content = re.sub(
            re.escape(img_url), f"{img_basename}.{img_extension}", markdown_content
        )
    return markdown_content


def delete_files_and_imgs_about_title(title):
    md_file = f"source/_posts/{title}.md"
    if os.path.exists(md_file):
        os.remove(md_file)
        print(f"Delete {md_file}")
    else:
        print(f"{md_file} is not exist")
    img_dir = f"source/_posts/{title}"
    if os.path.exists(img_dir):
        for img_file in os.listdir(img_dir):
            os.remove(f"{img_dir}/{img_file}")
        os.rmdir(img_dir)
        print(f"Delete {img_dir}")


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
        createdAt
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
            if category["name"] == "Blogs":
                if f"!go away, {title}" in body:
                    delete_files_and_imgs_about_title(title)
                else:
                    body = save_assets_img_substitute_url(body, title)
                    labels = discussion.get("labels", {}).get("nodes", [])
                    label_names = [label["name"] for label in labels]
                    label_str = f"[{', '.join(label_names)}]" if label_names else ""
                    tz_east_8 = timezone(timedelta(hours=8))
                    created_at = datetime.strptime(
                        discussion["createdAt"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    created_localized = created_at.astimezone(tz_east_8)
                    md_file = f"source/_posts/{title}.md"
                    with open(md_file, "w+") as md:
                        md.write("---\n")
                        md.write(f"title: {title}\n")
                        md.write(f"date: {created_localized:%Y-%m-%d %H:%M:%S}\n")
                        md.write("categories: \n")
                        md.write(f"tags: {label_str}\n")
                        md.write("---\n")
                        md.write(f"{body}\n")
                        print(f"Create or Update {title}")
            else:
                print(f"{title} is not blog.")
    else:
        print("No discussion.")
