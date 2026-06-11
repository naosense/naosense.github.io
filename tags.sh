#!/bin/bash

# 创建一个空数组来存储所有的标签
tags=()

# 遍历post文件夹下的所有md文件
for file in source/_posts/*.md; do
    # 使用sed命令提取标签行，然后使用awk将标签提取出来
    tag_line=$(sed -n '/^tags:/p' "$file")
    tags+=( $(echo "$tag_line" | awk -F 'tags: ' '{print $2}' | tr -d '[] ' | tr ',' '\n') )
done

# 统计每个标签的出现次数，按数量降序排列，名称左对齐数量右对齐
echo "${tags[@]}" | tr ' ' '\n' | sort | uniq -c | sort -rn | {
    # 收集数据并计算最大显示宽度
    lines=()
    max_w=0
    while read count tag; do
        byte_len=$(echo -n "$tag" | wc -c | tr -d ' ')
        char_len=${#tag}
        cjk_count=$(( (byte_len - char_len) / 2 ))
        vis_width=$(( char_len + cjk_count ))
        lines+=("$vis_width|$tag|$count")
        (( vis_width > max_w )) && max_w=$vis_width
    done
    for line in "${lines[@]}"; do
        IFS='|' read -r w t c <<< "$line"
        pad=$(( max_w - w ))
        printf "%s%*s%3d\n" "$t" "$pad" "" "$c"
    done
}
