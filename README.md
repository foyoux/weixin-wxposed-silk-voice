# weixin-wxposed-silk-voice

将任意 媒体文件 以最好音质 转为微信语音文件(支持分段) 推到到手机 ，使用 wxposed 直接发送

## 使用方法

依赖 [adb](https://developer.android.com/studio/command-line/adb)
Windows 平台已自带 其他平台自行安装配置

需要事先 adb 连接 手机，可数据线，可 WIFI

只能连接一个设备，需要多个设备指定的，自行微调代码

```shell
git clone git@github.com:foyoux/weixin-wxposed-silk-voice.git
cd weixin-wxposed-silk-voice
pip install -r requirements.txt
python start.py 音乐.mp3 音乐.flac 视频.mp4 # ... 接任意多媒体文件 
```

在 Windows 平台中，如果正确安装 Python，可双击 *.py 文件运行的，可直接拖拽任意多个媒体文件 到 `start.py` 上


https://user-images.githubusercontent.com/35125624/150513393-a562bcad-3838-4799-8e86-c970bcaf55ec.mp4
