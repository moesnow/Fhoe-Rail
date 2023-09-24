# Fhoe-rail食用指南(入门)

本指南仅为小白扫盲使用，不涉及进阶操作

### 键位映射

| 键位       | 映射                                                   |
| ---------- | ------------------------------------------------------ |
| WSAD       | 移动键，后面的数字代表按下的时间长短                   |
| X          | 进入战斗，map映射为fighting=1                          |
| 鼠标左键   | 打障碍物，map映射为fighting=2                          |
| F          | 交互键，后面的数字代表反复按F的时间长短，间隔随机      |
| shutdown   | 关机标志，键值无意义，控制开关在配置文件中             |
| mouse_move | 视角转动，因数值计算复杂（不同设备数值不同），已被弃用 |
| scroll     | 鼠标滚轮滚动的数值，同样较为复杂，未被启用             |
| e          | 只有键值为1时有意义，使用秘技并追加普通攻击            |

### 关于地图录制

禁止用鼠标移动视角，只能使用方向键左右来移动视角（脚本运行后方向键左右会映射鼠标移动）

录制期间能且只能按动键盘上的一个有效按键（也就是不能同时按下多键）

脚本只会录制按键按下时间和移动的视角，不会录制停顿的时间（可以慢慢一个键一个键录制，保证录制准确性）

录制完成后F9停止录制并保存。

（只有WSADF鼠标右键X参与录制，其他键值只能自己修改）

1. 完成后将会生成output(时间).json文件，请把他重命名替换成你要更改的地图json，并且将传送点截图重命名并保存到picture即可使用 （就可以申请到map分支提交，或者交给管理提交）

2. 地图json中的空白填写示例：

   ~~~
   {
       "name": "乌拉乌拉-1",       （地图json名为1-1_1.json）
       "author": "Starry-Wind",   （作者名，第二作者不能覆盖第一作者名称）
       "start": [           （开局传送地图识别图片，并将鼠标移动至图片中间并按下按键）
           {"map": 1},         （按下m键打开地图）
           {"picture\\orientation_1.jpg": 1.5},     （识别到orientation_1.jpg图片后，将鼠标移动至图片中间并按下按键）
           {"picture\\map_1.jpg": 2},               （具体图片自己看，一般为该区域名"乌拉乌拉"的地图文字）
           {"picture\\map_1_point_1.jpg": 1.5},       （第一个传送点的图片）
           {"picture\\transfer.jpg": 1.5}              （"传送"字的图片）
       ]
   }
   ~~~

   ### 关于识别问题

   识图为截取游戏画面，所以不能有任何覆盖



### 关于跑图

成年女性模型（且攻击为远程无位移）跑图最佳，如：娜塔莎、艾丝妲、三月七

幼女模型可能会卡（概率较小），如：青雀、佩拉、符玄

成女有位移，如：驭空

成男有位移，如：饮月丹恒