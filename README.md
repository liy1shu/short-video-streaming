# short-video-streaming
2022 网络创新实验 MMGC 小组

# 目录结构
#### 0. 数据

- /short_video_size：视频大小
- /network_traces：网络模型
- /user_ret：用户留存率的模型

#### 1. 仿真器

- controller.py
- network_module.py
- short_video_load_trace.py
- user_module.py
- video_player.py

#### 2. 评测程序（run.py）

评测方法：

1）跑baseline代码

```bash
python run.py --baseline fixed_preload
python run.py --baseline no_preload
```

2）评测自己的代码

```bash
python run.py --user <Your relative code directory path>
```

#### 3. 生成的日志

- /sample_user/user.txt：生成的用户行为，每个视频播放的时间
- /ABM_results/log.txt：评测的日志，每一步选择下载哪个视频的第几块，同时正在播放视频的哪一块。同时也会输出影响QoE的因素，视频质量的变化、造成重缓冲等

#### 4. 提供的参数含义：

- delay
- rebuf
- ...
- players：详情可见video_player.py
