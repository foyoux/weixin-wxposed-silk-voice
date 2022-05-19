"""添加语音"""
from typing import Tuple

from utils import main

# 需要手动设置的参数，超过 3000 按 3000 计算
silk_time: int = 3000  # 3000 指代 60s，300 则是 6s


def get_durations(silk_path: str) -> Tuple:
    """分段，3000 指 60s"""
    global silk_time
    if silk_time > 3000:
        silk_time = 3000
    with open(silk_path, 'rb') as silk:
        # 跳过语音头
        silk.seek(10)
        frame_count = 0
        frame_position = 10
        silk_cursor = frame_position
        while True:
            # 读取 frame 大小
            # noinspection DuplicatedCode
            size = silk.read(2)
            # size == 1 说明 silk 文件异常
            assert size != 1, 'silk 文件异常'
            if len(size) == 0:
                # 说明文件结束，定位到上次结束位置，读取完毕返回
                silk.seek(frame_position)
                yield frame_count * 20, frame_count / 50, silk.read()
                break
            # 一切正常，记录一些值
            frame_count += 1
            size = size[0] + size[1] * 16
            silk_cursor += 2 + size
            if frame_count == silk_time:
                # 达到指定 时间 后，开始返回数据，重新开始
                silk.seek(frame_position)
                yield frame_count * 20, frame_count / 50, silk.read(silk_cursor - frame_position)
                frame_count = 0
                frame_position = silk_cursor
            else:
                silk.seek(silk_cursor)


if __name__ == '__main__':
    main(get_durations)
