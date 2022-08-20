import os
import re


def get_latest_tag():
    return max(
        {tag.name: tag.stat().st_mtime_ns for tag in os.scandir('.git/refs/tags')}.items(),
        key=lambda item: item[1]
    )[0]


if __name__ == '__main__':
    latest_tag = get_latest_tag()
    init_py = 'src/wilk/__init__.py'

    with open(init_py, encoding='utf8') as f:
        txt = f.read()

    txt = re.sub(r"__version__ = '\d+.\d+.\d+'", f"__version__ = '{latest_tag[1:]}'", txt)

    with open(init_py, 'w', encoding='utf8') as f:
        f.write(txt)
