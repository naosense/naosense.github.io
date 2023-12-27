import os
import re
import textwrap
from datetime import datetime, timedelta, timezone

import requests


def run_query(
    query: str, variables: dict[str, any], token: str
) -> dict[str, any] | None:
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


def replace_asset_imgs(markdown_content: str, title: str) -> str:
    """将Markdown文本中的图片URL保存在本地并将url替换为本地路径，
    因为github assets的图片链接常规情况是无法访问的"""
    # 匹配 ![alt](url) 格式的图片
    markdown_img_pattern = (
        r"!\[(.*?)\]\((https://github\.com/naosense/naosense\.github\.io/assets.*?)\)"
    )
    markdown_image_matches = re.findall(markdown_img_pattern, markdown_content)

    # 匹配 <img alt="alt" src="url"> 格式的图片
    html_img_pattern = r'<img[^>]*?(?:\s+alt="(.*?)")?\s+src="(https://github\.com/naosense/naosense\.github\.io/assets[^"]*)"'
    html_image_matches = re.findall(html_img_pattern, markdown_content)

    image_matches = markdown_image_matches + html_image_matches
    print(f"Found img {image_matches}")

    img_dir_for_title = f"source/_posts/{title}"
    if image_matches:
        # 重新创建目录，因为有时候可能会有图片重命名的情况，
        # 如果不重新创建目录，会导致有多份图片
        if os.path.exists(img_dir_for_title):
            rm_dir(img_dir_for_title)
        os.makedirs(img_dir_for_title)

    for alt_text, img_url in image_matches:
        img_name = alt_text if alt_text else img_url.split("/")[-1]
        img_basename = img_name.split(".")[0].replace(" ", "_")
        img_extension = (
            img_name.split(".")[-1] if "." in img_name else "jpeg"
        )  # github assets为jpeg格式
        img_path = f"{img_dir_for_title}/{img_basename}.{img_extension}"

        response = requests.get(img_url)
        if response.status_code == 200:
            with open(img_path, "wb+") as img_file:
                print(f"Save img {img_path}")
                img_file.write(response.content)
        else:
            print(f"Failed to get img {img_url}. Status code: {response.status_code}")

        markdown_content = re.sub(
            re.escape(img_url), f"{img_basename}.{img_extension}", markdown_content
        )
    return markdown_content


def delete_article(title: str) -> None:
    md_file = f"source/_posts/{title}.md"
    if os.path.exists(md_file):
        os.remove(md_file)
        print(f"Delete {md_file}")
    else:
        print(f"{md_file} is not exist")
    img_dir = f"source/_posts/{title}"
    if os.path.exists(img_dir):
        rm_dir(img_dir)
        print(f"Delete {img_dir}")


def rm_dir(dir: str) -> None:
    for file in os.listdir(dir):
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            rm_dir(file_path)
    os.rmdir(dir)


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
            body = body.replace("\r\n", "\n")  # github discussion的换行符是\r\n
            category = discussion["category"]
            if category["name"] == "Blogs":
                if "**!!go away**" in body:
                    delete_article(title)
                else:
                    header_body_pattern = r"---\n(.+?)---\n(.+)"
                    header_extra = ""
                    if res := re.search(header_body_pattern, body, re.DOTALL):
                        header_extra = res.group(1)
                        body = res.group(2)

                    body = replace_asset_imgs(body, title)
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
                        header = textwrap.dedent(
                            f"""\
                            ---
                            title: {title}
                            date: {created_localized:%Y-%m-%d %H:%M:%S}
                            categories:
                            tags: {label_str}
                            """
                        )
                        md.write(header)
                        md.write(header_extra)
                        md.write("---\n")
                        md.write(body)
                        print(f"Create or Update {title}")
            else:
                print(f"{title} is not blog.")
    else:
        print("No discussion.")
