import sys
import short_video_load_trace
import controller as env

SUMMARY_DIR = './ABM_results'
LOG_FILE = './ABM_results/log_sim_abm'

# QoE参数(？)
alpha = 0.5
beta = 0.5
gamma = 0.5
ALL_VIDEO_NUM = 9
baseline_QoE = 100  # baseline的QoE
TOLERANCE = 0.1  # 容忍的QoE降低率
MIN_QOE = -1e9


def test(user_id):  # 对user_id进行测试
    # 引入选手的决策算法函数 ABM 并初始化
    # sys.path.append(u'/root/mmgc/team/' + user_id + u'/submit/')  # 服务器上的选手代码摆放路径（？）
    # import ABM
    # sys.path.remove(u'/root/mmgc/team/' + user_id + u'/submit/')
    sys.path.append('./baseline/')
    # import no_preload as ABM
    import fix_preload as ABM
    sys.path.remove('./baseline/')
    abm = ABM.Algorithm()
    abm.Initialize()

    all_cooked_time, all_cooked_bw = short_video_load_trace.load_trace()

    # 目前的env是单trace，待修改成多trace，才可以测试
    net_env = env.Environment(all_cooked_time[0], all_cooked_bw[0])

    # log待增加
    log_file = open(LOG_FILE, 'wb')

    # Decision variables
    download_video_id = 0
    bit_rate = 0
    sleep_time = 0.0

    # sum of wasted bytes for a user
    sum_wasted_bytes = 0
    QoE = 0
    last_bitrate = 0  # 维护本视频上一个chunk的bitrate，用于计算QoE

    while True:
        delay, rebuf, video_size, end_of_video, \
        play_video_id, waste_bytes = net_env.buffer_management(download_video_id, bit_rate, sleep_time)

        # 更新带宽浪费
        print(waste_bytes)
        sum_wasted_bytes += waste_bytes  # 累加带宽浪费

        # 更新QoE值
        # qoe = alpha * VIDEO_BIT_RATE[bit_rate] \
        #           - beta * rebuf \
        #           - gamma * np.abs(VIDEO_BIT_RATE[bit_rate] - VIDEO_BIT_RATE[last_bit_rate])
        if last_bitrate == 0:  # 是该视频块的第一块
            smooth = 0
        else:
            smooth = bit_rate - last_bitrate  # 记录质量差
        QoE += alpha * bit_rate - beta * rebuf - gamma * abs(smooth)

        if QoE < MIN_QOE:  # 防止死循环
            print('Your QoE is too low...(Your video seems to have stuck forever) Please check for errors!')
            return

        if end_of_video:  # 如果切换视频，则last_bitrate = 0
            last_bitrate = 0
        else:
            last_bitrate = bit_rate  # 记录当前

        # play over all videos
        if play_video_id >= ALL_VIDEO_NUM:
            print("The user leaves.")
            break

        # 调用选手算法计算下一步的参数
        download_video_id, bit_rate, sleep_time = abm.run(delay, rebuf, video_size, end_of_video, play_video_id, net_env.players)

        print("*****************")
        print('sleep time:')
        print(sleep_time)
        print('downlad video ID')
        print(download_video_id)
        print('bitrate download:')
        print(bit_rate)

    # QoE
    print("Your QoE is: ")
    print(QoE)
    # wasted_bytes
    print("Your sum of wasted bytes is:")
    print(sum_wasted_bytes)
    if QoE >= baseline_QoE * (1-TOLERANCE):  # QoE在可容忍范围内
        print("Your QoE meets the standard.")
    else:  # QoE超出可容忍范围
        print("Your QoE is too low!")


test(1)