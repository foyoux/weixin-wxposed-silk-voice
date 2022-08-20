__version__ = '0.0.1'

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Tuple

import av
import pilk

DEBUG = False

# 需要手动设置的参数，超过 3000 按 3000 计算
silk_time: int = 3000  # 3000 指代 60s，300 则是 6s


@dataclass
class Sound:
    title: str = None
    filename: str = None
    length: int = None
    status: int = None
    code: int = None
    durations: List[int] = field(default_factory=list)
    segment: int = None


# noinspection PyUnresolvedReferences
def to_pcm(in_path: str) -> Tuple[str, int]:
    """任意媒体文件转pcm"""
    out_path = os.path.splitext(in_path)[0] + '.pcm'
    with av.open(in_path) as in_container:
        in_stream = in_container.streams.audio[0]
        sample_rate = in_stream.codec_context.sample_rate
        if sample_rate not in [8000, 12000, 16000, 24000, 32000, 44100, 48000]:
            sample_rate = 24000
        with av.open(out_path, 'w', 's16le') as out_container:
            out_stream = out_container.add_stream(
                'pcm_s16le',
                rate=sample_rate,
                layout='mono'
            )
            try:
                for frame in in_container.decode(in_stream):
                    frame.pts = None
                    for packet in out_stream.encode(frame):
                        out_container.mux(packet)
            except:
                pass
    return out_path, sample_rate


def convert_to_silk(media_path: str) -> str:
    """任意媒体文件转为 silk, 返回silk路径"""
    pcm_path, sample_rate = to_pcm(media_path)
    silk_path = os.path.splitext(pcm_path)[0] + '.silk'
    pilk.encode(pcm_path, silk_path, pcm_rate=sample_rate, tencent=True)
    if not DEBUG:
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


def adjust_duration(duration):
    if duration < 1:
        return 1
    if duration > 60:
        return 60
    return duration


def start(start_durations, files):
    """添加silk文件"""
    folder = os.path.dirname(sys.argv[0])

    # 1. 拉取 sounds_db 文件
    sounds_db_path = os.path.join(folder, 'sounds_db')
    if not DEBUG:
        os.system(f'adb pull /sdcard/WechatXposed/sounds/sounds_db "{sounds_db_path}"')

    # 2. 打开 sounds_db -> json
    sounds_db: List[Sound] = []  # type: ignore
    if os.path.exists(sounds_db_path):
        with open(sounds_db_path, encoding='utf8') as f:
            sounds_db = [Sound(**sound) for sound in json.load(f)]

    # 4. 遍历文件
    for silk_file in files:
        # 4.1 获取 silk 文件名，去除后缀，用作语音 title
        name = os.path.basename(silk_file)
        name, ext = os.path.splitext(name)
        if ext != '.silk':
            silk_file = convert_to_silk(silk_file)
        print(silk_file)

        code = sounds_db[-1].code + 1 if sounds_db else 0

        # 4.2 获取分段数据及信息
        duration = 0
        lens = []
        sf_index = 0
        for item in start_durations(silk_file):
            duration += item[0]
            lens.append(adjust_duration(item[1]))
            sf_file = f'sf_{code}_p{sf_index}_amr'
            with open(sf_file, 'wb') as f:
                f.write(b'\x02#!SILK_V3')
                f.write(item[2])
            if not DEBUG:
                os.system(
                    f'adb push "{os.path.abspath(sf_file)}" /sdcard/WechatXposed/sounds/sf_{code}_p{sf_index}_amr')
                os.remove(sf_file)
            sf_index += 1

        sounds_db.append(Sound(
            title=name, filename=f'sf_{code}', length=duration, status=1, code=code, durations=lens, segment=60
        ))

        if not DEBUG:
            os.remove(silk_file)

    # 5. 保存 sounds_db
    with open(os.path.join(folder, 'sounds_db'), 'w', encoding='utf8') as f:
        json.dump([asdict(obj) for obj in sounds_db], f, ensure_ascii=False)

    # 6. 推送 sounds_db
    if not DEBUG:
        os.system(f'adb push "{sounds_db_path}" /sdcard/WechatXposed/sounds/sounds_db')
        os.remove(sounds_db_path)


def get_durations(silk_path: str) -> Tuple[int, int, bytes]:
    """分段，3000 指 60s"""
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


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='将媒体文件转为文件推到手机供微(x)信发送',
        epilog=f'wilk({__version__}) by foyou(https://github.com/foyoux)'
    )
    parser.add_argument('files', nargs='*', help='音视频文件，可任意多个')
    parser.add_argument('-t', '--time', dest='time', type=int, default=3000, help='set silk duration')
    parser.add_argument('--debug', dest='debug', help='debug mode', action="store_true")
    parser.add_argument('-v', '--version', dest='version', help='show wilk version', action="store_true")
    args = parser.parse_args()

    if args.version:
        print('wilk version', __version__)
        return

    if len(args.files) == 0:
        parser.print_usage()
        return

    global DEBUG, silk_time
    DEBUG = args.debug
    silk_time = args.time

    start(get_durations, [os.path.abspath(file) for file in args.files])
