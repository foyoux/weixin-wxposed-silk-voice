# foyou-wilk
将任意 媒体文件 以最好音质 转为微信语音文件(支持分段) 推到手机 ，使用 wxposed 直接发送

推荐配合 [foyou-king 酷狗铃声搜索和下载](https://github.com/foyoux/foyou-king) 使用

## 快速入门

[![python version](https://img.shields.io/pypi/pyversions/foyou-wilk)](https://pypi.org/project/foyou-wilk)  [![Downloads](https://static.pepy.tech/personalized-badge/foyou-wilk?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/foyou-wilk)

安装

```shell
pip install -U foyou-wilk
```

> 这是一个偏个人化的包，为了尽可能不占用公共资源，所以包名比较啰嗦。以后我发布的类似小工具包都会添加一个 **foyou-** 前缀

安装后，会有一个 `wilk` 的命令

> 请先配置 `adb` 并连接好手机，不明表看 [这里](https://github.com/foyoux/weixin-wxposed-silk-voice/tree/old)
> 
推送媒体文件到手机（不明白说啥，请看 [旧版](https://github.com/foyoux/weixin-wxposed-silk-voice/tree/old)）

```shell
wilk <媒体文件1> <媒体文件2> ...
```

## 其他

```shell
# 获取帮助
wilk 
wilk -h/--help 打印帮助

wilk -v/version 打印版本

wilk [--debug] [-t/--time <time>] <media1> <media2> ...

--debug silk 文件调试,开发使用,大家无需理会

--time silk 分割的时间,默认是 3000,代表 60s

wilk <media1> <media2> ... [--debug] [-t/--time <time>]
```
