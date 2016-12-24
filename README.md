## 简介

豆芽保姆。一个用来检测宠物生活环境温度、视频监控，并能控制空调等家电影响环境的程序。此程序通过sina weibo做为远程接口，实现温度查询，视频截图上传，空调控制等功能。

## 使用指南

### 硬件设备

-跑Ubuntu的ARM开发板一块，或者PC一台。运行环境为Ubuntu 11.04+Python 2.7。
-USB temper1温度传感器一个(http://item.taobao.com/item.htm?id=9576081279) 。USB转串口的通用dongle，可以直接模拟串口读取温度值。
-USB 红外遥控器一个(http://item.taobao.com/item.htm?id=17522720980) 。USB转串口的dongle，通过发送 'learn n', 'send n'来学习和发送一个按键。
-普通USB摄像头一个（UVC）

### 安装工具

首先要下载安装Weibo Python SDK(下载地址：https://github.com/michaelliao/sinaweibopy/zipball/master) 
``` bash
$ cd sinaweibopy
$ python setup.py install
```

安装UVC camera工具：
``` bash
$ sudo apt-get install fswebcam
```

安装libusb开发包：
``` bash
$ sudo apt-get install libusb-dev
```

有可能您会缺少一些Python的module，如httplib, urllib2之类，请自行安装。

### 编译

温度传感器程序和空调红外控制程序需要编译：
``` bash
$ cd dog-nanny
$ cd temper1
$ make
$ cd ../ac-controller
$ make
```

会生成 temper1/temper,ac-controller/ac-ctrl,ac-controller/ac-learn三个可执行文件。 分别用于从USB DONGLE获取温度，发送红外遥控，学习红外遥控。

### 学习空调指令

``` bash
$ ac-learn 1 # 对着USB DONGLE按总开关，开启空调
$ ac-learn 2 # 对着USB DONGLE按总开关，关闭空调
```

### 写配置文件

建立配置文件 ~/dognanny.rc
``` html
<app key>  #创建weibo app后，既有app key/secret
<app secret>
<nanny weibo account> # 总要申请个微博帐号给保姆吧:)
<nanny weibo passwd>
<nanny app callback url> # e.g. http://www.baidu.com. 在你的weibo APP管理页面里可以设置
<admin weibo nickname> # 管理员微博名称。保姆通过他判断用户是否有权限做高级操作。
```

### 运行保姆
``` bash
$ python main.py
```
此主程序会以daemon的形式运行。

### 远程控制

远程接口，都是通过发微薄@保姆来实现，具体定义：

**通用接口，任何互粉的用户都可以使用：**
查询保姆是否在工作：“@保姆 ping” 查询当前温度、拍摄照片：“@保姆 豆芽呢”

**管理员接口，只有定义在配置文件里的管理员发送才有效：**
退出保姆程序：“@保姆 下班咯” 开空调：“@保姆 开空调” 关空调：“@保姆 关空调”

## 进阶

豆芽保姆实际上是个简单的程序，利用了各种传感器、控制器作为环境检测和空调遥控的设备，利用新浪微博作为远程通讯的接口。可以说他是智能家庭的一个缩影，可以扩展的应用非常的多：只要有想法。
程序本身比较容易读懂，可以配置的地方除了~/dognanny.rc，有些hard code在main.py里：
``` python
TEMPER1 = WORKDIR + '/temper1/temper' # USB temper1 读取程序路径
AC_CONTROL = WORKDIR + '/ac-controller/ac-ctrl' # 空调遥控程序路径
CONFIG_FILE = os.environ['HOME'] + '/dognanny.rc' # 配置文件路径
INTERVAL = 30 # 保姆默认工作时间间隔，微博API采用POLLING方式，所以保姆也只能睡眠、唤醒、工作然后再睡眠
RESOLUTION = '1280x720' # 摄像头拍照默认分辨率
```

命令接口的修改：所有命令都定义在cmds_desc的dict结构里。 * pattern 是命令匹配字符串 * desc 是用来DEBUG的说明 * handler 自然是处理函数 

``` python

cmds_desc = { 'poll' : { 'pattern': u'豆芽呢', 'desc': u'poll the status', 'handler': cmd_poll }, 'acon' : { 'pattern': u'开空调', 'desc': u'turn on ac', 'handler': cmd_acon }, 'acoff': { 'pattern': u'关空调', 'desc': u'turn off ac', 'handler': cmd_acoff }, 'kill' : { 'pattern': u'下班了', 'desc': u'kill myself', 'handler': cmd_kill }, 'ping' : { 'pattern': u'ping', 'desc': u'debug ping', 'handler': cmd_ping }, } ```
```

