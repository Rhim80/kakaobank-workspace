"""WikiLink 해석 공용 함수. 워크스페이스의 꼬리·별칭·상대경로 규칙."""
from pathlib import Path


def link_index(files, directories=()):
    names: set[str] = set()
    suffixes: set[str] = set()
    for f in files:
        base = f.rsplit("/", 1)[-1]
        names.add(base)
        if base.endswith(".md"):
            names.add(base[:-3])
        parts = f.split("/")
        for i in range(len(parts)):
            tail = "/".join(parts[i:])
            suffixes.add(tail)
            if tail.endswith(".md"):
                suffixes.add(tail[:-3])
            for j in range(len(parts) - 1, i, -1):   # 폴더 꼬리도 산 것으로
                suffixes.add("/".join(parts[i:j]))

    for directory in directories:
        parts = directory.strip("/").split("/")
        for i in range(len(parts)):
            suffixes.add("/".join(parts[i:]))

    return names, suffixes


def link_target(raw):
    return raw.replace("\\|", "|").split("|")[0].split("#")[0].strip()


def link_alive(target, source, root, names, suffixes):
    if not target:
        return True
    if "/" in target:
        if target.startswith("."):
            resolved = (root / source).parent / target
            return resolved.exists() or resolved.with_name(resolved.name + ".md").exists()
        return target.strip("/") in suffixes
    return target in names or target + ".md" in names
