import sys
import argparse
import short_video_load_trace
import controller as env

parser = argparse.ArgumentParser()

parser.add_argument('--baseline', type=str, default='',
	help='Is testing baseline')
parser.add_argument('--user', type=str, default='./',
	help='The relative path of your file dir, default is current dir')
args = parser.parse_args()


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


def test(isBaseline, user_id, trace_id):  # 对user_id进行测试
    # 引入选手的决策算法函数 ABM 并初始化
    # sys.path.append(u'/root/mmgc/team/' + user_id + u'/submit/')  # 服务器上的选手代码摆放路径（？）
    # import ABM
    # sys.path.remove(u'/root/mmgc/team/' + user_id + u'/submit/')
    if isBaseline:  # 测试baseline
        sys.path.append('./baseline/')
        if user_id == 'fixed_preload':
            import fix_preload as ABM
        else:
            import no_preload as ABM
        sys.path.remove('./baseline/')
    else:  # 测试选手自身代码
        sys.path.append(user_id)
        import ABM
        sys.path.remove(user_id)
    abm = ABM.Algorithm()
    abm.Initialize()

    all_cooked_time, all_cooked_bw = short_video_load_trace.load_trace()

    # 目前的env是单trace，待修改成多trace，才可以测试
    net_env = env.Environment(all_cooked_time[trace_id], all_cooked_bw[trace_id])

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
        print("waste_bytes:::::!", waste_bytes)
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


if __name__ == '__main__':
    if args.baseline == '':
        test(False, args.user, 0)
    else:
        test(True, args.baseline, 0)