"""添加语音"""
import json
import os
import sys
from typing import Tuple

import av
import pilk

# 需要手动设置的参数，超过 3000 按 3000 计算
silk_time: int = 3000  # 3000 指代 60s，300 则是 6s


def to_pcm(in_path: str) -> tuple[str, int]:
    """任意媒体文件转pcm"""
    out_path = os.path.splitext(in_path)[0] + '.pcm'
    with av.open(in_path) as in_container:
        in_stream = in_container.streams.audio[0]
        sample_rate = in_stream.codec_context.sample_rate
        if sample_rate > 48000:
            sample_rate = 48000
        with av.open(out_path, 'w', 's16le') as out_container:
            out_stream = out_container.add_stream(
                'pcm_s16le',
                rate=sample_rate,
                layout='mono'
            )
            for frame in in_container.decode(in_stream):
                frame.pts = None
                for packet in out_stream.encode(frame):
                    out_container.mux(packet)
    return out_path, sample_rate


def convert_to_silk(media_path: str) -> str:
    """任意媒体文件转为 silk, 返回silk路径"""
    pcm_path, sample_rate = to_pcm(media_path)
    silk_path = os.path.splitext(pcm_path)[0] + '.silk'
    pilk.encode(pcm_path, silk_path, pcm_rate=sample_rate, tencent=True)
    os.remove(pcm_path)
    return silk_path


def get_duration(silk_path: str) -> int:
    """获取 silk 文件持续时间"""
    with open(silk_path, 'rb') as silk:
        silk.seek(10)
        i = 0
        while True:
            size = silk.read(2)
            if len(size) != 2:
                break
            i += 1
            size = size[0] + size[1] * 16
            silk.seek(silk.tell() + size)
        return i * 20


def get_durations(silk_path: str) -> Tuple[int, int, bytes]:
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


def get_code(code_list, _code=0) -> int:
    """从 code 开始遍历 code_list，遇到缺失则返回，末尾则 +1 返回"""
    for i in range(_code, len(code_list)):
        _code = code_list[i]['code']
        if i != _code:
            # 缺失，返回 i，供在此位置插入数据
            return i
    # 数据完整，从最后一个位置插入
    return _code + 1


if __name__ == '__main__':
    '''添加silk文件'''
    folder = os.path.dirname(sys.argv[0])

    # 0. 连接 adb
    # connect_result = os.popen('adb connect 192.168.1.2:5555')
    # connect_result = connect_result.buffer.read().decode('utf8')
    # print(connect_result)
    # if not connect_result.__contains__('connected'):
    #     print(connect_result)
    #     raise connect_result

    # 1. 拉取 sounds_db 文件
    sounds_db_path = os.path.join(folder, 'sounds_db')
    os.system(f'adb pull /sdcard/WechatXposed/sounds/sounds_db "{sounds_db_path}"')

    # 2. 打开 sounds_db -> json
    with open(sounds_db_path, encoding='utf8') as f:
        sounds_db: list = json.load(f)

    # 3. 初始化 code，意指从 0 开始解析
    code = 0

    # 4. 遍历文件
    for silk_file in sys.argv[1:]:
        # 4.0 获取 silk 文件名，去除后缀，用作语音 title
        name = os.path.basename(silk_file)
        name, ext = os.path.splitext(name)
        if ext != '.silk':
            silk_file = convert_to_silk(silk_file)
        print(silk_file)
        # 4.1 解析 code
        code = get_code(sounds_db, code)

        # 4.2 获取分段数据及信息
        duration = 0
        lens = []
        sf_index = 0
        for item in get_durations(silk_file):
            duration += item[0]
            lens.append(item[1])
            sf_file = f'sf_{code}_p{sf_index}_amr'
            with open(sf_file, 'wb') as f:
                f.write(b'\x02#!SILK_V3')
                f.write(item[2])
            os.system(f'adb push "{os.path.abspath(sf_file)}" /sdcard/WechatXposed/sounds/sf_{code}_p{sf_index}_amr')
            os.remove(sf_file)
            sf_index += 1

        sounds_db.insert(code, {
            # "title": f'{name} ??',
            "title": f'{name}',
            "filename": f'sf_{code}',
            "length": duration,
            "status": 1,
            "code": code,
            "durations": lens,
            "segment": 60
        })
        os.remove(silk_file)

    # 5. 保存 sounds_db
    with open(os.path.join(folder, 'sounds_db'), 'w') as f:
        json.dump(sounds_db, f, ensure_ascii=False)

    # 6. 推送 sounds_db
    os.system(f'adb push "{sounds_db_path}" /sdcard/WechatXposed/sounds/sounds_db')
    os.remove(sounds_db_path)
    os.system('pause')
