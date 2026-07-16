"""镜像列表排序命令"""

import re
from pathlib import Path

import typer
import yaml


def parse_image_name(name: str) -> tuple[str, str]:
    """解析镜像名称，返回 (repository, tag)"""
    if ":" in name and not name.startswith("ghcr.io/"):  # ghcr.io 可能包含 :port
        parts = name.rsplit(":", 1)
        return parts[0], parts[1]
    return name, ""


def extract_version_parts(tag: str) -> tuple:
    """从 tag 中提取版本号用于排序，返回 (is_valid_version, version_tuple, full_tag)"""
    # 匹配主版本号.次版本号.修订号 格式
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)", tag)
    if match:
        major, minor, patch, suffix = match.groups()
        # 有后缀（如 -ubuntu）的版本排在同版本无后缀之后
        has_suffix = 1 if suffix else 0
        return (0, (int(major), int(minor), int(patch), has_suffix))
    return (1, (999,))  # 非版本格式排在最后


def semantic_sort_key(image: dict) -> tuple[str, tuple]:
    """排序 key：先按 repository，再按 tag 的语义版本"""
    name = image.get("name", "")
    repo, tag = parse_image_name(name)

    # 处理 latest 标签
    if tag == "latest":
        return (repo, (0, (-1,), 0))

    version_tuple = extract_version_parts(tag)
    return (repo, version_tuple)


def register(app: typer.Typer):
    @app.command(name="sort")
    def sort():
        """按 repository 和 tag 语义版本对 images.yaml 排序，并去除重复镜像"""
        yaml_path = Path("images.yaml")
        with open(yaml_path, "r") as f:
            images = yaml.safe_load(f)

        # 检测并记录重复镜像
        seen = set()
        duplicates = []
        unique_images = []
        for image in images:
            name = image.get("name", "")
            if name in seen:
                duplicates.append(name)
            else:
                seen.add(name)
                unique_images.append(image)

        # 输出警告
        for dup in duplicates:
            typer.secho(f"警告: 重复镜像已移除 - {dup}", fg="yellow")

        # 排序：先按 repository，再按 tag 语义版本
        sorted_images = sorted(unique_images, key=semantic_sort_key)

        # 写回文件（标准 YAML 格式）
        with open(yaml_path, "w") as f:
            for image in sorted_images:
                if len(image) == 1 and "name" in image:
                    f.write(f"- name: {image['name']}\n")
                else:
                    f.write(f"- name: {image['name']}\n")
                    for key, value in image.items():
                        if key != "name":
                            f.write(f"  {key}: {value}\n")

        typer.echo(f"已排序 {len(sorted_images)} 条记录（移除 {len(duplicates)} 条重复）")
