#!/bin/bash

# 指定包含.md文件的目录
directory="source/_posts"

# 循环遍历目录下的所有.md文件
for file in "$directory"/*.md; do
    # 检查文件是否存在
    if [ -e "$file" ]; then
        # 使用awk来提取类目值
        category=$(awk -F': ' '/categories:/ {if ($2 != "") print $2}' "$file")

        # 如果类目值不为空，则替换为"categories:"，否则跳过
        if [ -n "$category" ]; then
            echo "$file: $category"
            sed -i '' 's/^categories:.*$/categories:/' "$file"
        fi
    fi
done
