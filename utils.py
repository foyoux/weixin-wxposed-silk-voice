import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List

import av
import pilk

DEBUG = False


@dataclass
class Sound:
    title: str = None
    filename: str = None
    length: int = None
    status: int = None
    code: int = None
    durations: List[int] = field(default_factory=list)
    segment: int = None


def to_pcm(in_path: str) -> tuple[str, int]:
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


def main(start_durations):
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

    # 3. 整理 sounds, 顺序赋值 code
    for i, sound in enumerate(sounds_db):
        sound.code = i

    # 4. 遍历文件
    for silk_file in sys.argv[1:]:
        # 4.1 获取 silk 文件名，去除后缀，用作语音 title
        name = os.path.basename(silk_file)
        name, ext = os.path.splitext(name)
        if ext != '.silk':
            silk_file = convert_to_silk(silk_file)
        print(silk_file)

        code = len(sounds_db)

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
        os.system('pause')
