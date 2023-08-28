#!/bin/bash

# 创建一个空数组来存储所有的标签
tags=()

# 遍历post文件夹下的所有md文件
for file in source/_posts/*.md; do
    # 使用sed命令提取标签行，然后使用awk将标签提取出来
    tag_line=$(sed -n '/^tags:/p' "$file")
    tags+=( $(echo "$tag_line" | awk -F 'tags: ' '{print $2}' | tr -d '[],' | tr ' ' '\n') )
done

# 使用sort命令对标签进行排序并去重
sorted_tags=($(echo "${tags[@]}" | tr ' ' '\n' | sort -u))

# 打印排好序的标签
for tag in "${sorted_tags[@]}"; do
    echo "$tag"
done
