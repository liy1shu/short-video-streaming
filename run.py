import sys
sys.path.append('./simulator/')
import argparse
from simulator import controller as env, short_video_load_trace

parser = argparse.ArgumentParser()

parser.add_argument('--baseline', type=str, default='', help='Is testing baseline')
parser.add_argument('--user', type=str, default='./', help='The relative path of your file dir, default is current dir')
parser.add_argument('--trace', type=int, default=0, help='The network trace you are testing')
args = parser.parse_args()


SUMMARY_DIR = 'logs'
LOG_FILE = 'logs/log.txt'

# QoE arguments
alpha = 1
beta = 4.3
gamma = 1
ALL_VIDEO_NUM = 9
baseline_QoE = 600  # baseline的QoE
TOLERANCE = 0.1  # The tolerance of the QoE decrease
MIN_QOE = -1e9


def test(isBaseline, user_id, trace_id):
    if isBaseline:  # Testing baseline algorithm
        sys.path.append('./baseline/')
        if user_id == 'fixed_preload':
            import fix_preload as ABM
            LOG_FILE = 'logs/log_fixpreload.txt'
        else:
            import no_preload as ABM
            LOG_FILE = 'logs/log_nopreload.txt'
        sys.path.remove('./baseline/')
    else:  # Testing participant's algorithm
        sys.path.append(user_id)
        import ABM
        sys.path.remove(user_id)
        LOG_FILE = 'logs/log.txt'
    abm = ABM.Algorithm()
    abm.Initialize()

    all_cooked_time, all_cooked_bw = short_video_load_trace.load_trace()
    net_env = env.Environment(all_cooked_time[trace_id], all_cooked_bw[trace_id])

    # log file
    log_file = open(LOG_FILE, 'w')

    # Decision variables
    download_video_id, bit_rate, sleep_time = abm.run(0, 0, 0, False, 0, net_env.players, True)  # take the first step
    # output the first step
    if sleep_time != 0:
        print("You choose to sleep for ", sleep_time, " ms", file=log_file)
    else:
        print("Download Video ", download_video_id, " chunk (",
              net_env.players[download_video_id].get_chunk_counter() + 1, " / ",
              net_env.players[download_video_id].get_chunk_sum(), ") with bitrate ", bit_rate,
              file=log_file)

    # sum of wasted bytes for a user
    sum_wasted_bytes = 0
    QoE = 0
    last_played_chunk = -1  # record the last played chunk

    while True:
        delay, rebuf, video_size, end_of_video, \
        play_video_id, waste_bytes = net_env.buffer_management(download_video_id, bit_rate, sleep_time)

        # Update bandwidth wastage
        sum_wasted_bytes += waste_bytes  # Sum up the bandwidth wastage

        # print log info of the last operation
        # the operation results
        current_chunk = net_env.players[0].get_play_chunk()
        # print(current_chunk)
        current_bitrate = net_env.players[0].get_video_quality(max(int(current_chunk - 1e-10), 0))
        print("Playing Video ", play_video_id, " chunk (", current_chunk, " / ", net_env.players[0].get_chunk_sum(),
              ") with bitrate ", current_bitrate, file=log_file)
        if rebuf != 0:
            print("You caused rebuf for Video ", play_video_id, " of ", rebuf, " ms", file=log_file)
        if max(int(current_chunk - 1e-10), 0) == 0 or last_played_chunk == max(int(current_chunk - 1e-10), 0):  # is the first chunk or the same chunk as last time(already calculated) of the current video
            smooth = 0
        else:  # needs to calc smooth
            last_bitrate = net_env.players[0].get_video_quality(int(current_chunk - 1e-10) - 1)
            smooth = current_bitrate - last_bitrate
            if smooth == 0:
                print("Your bitrate is stable and smooth. ", file=log_file)
            else:
                print("Your bitrate changes from ", last_bitrate, " to ", current_bitrate, ".", file=log_file)
        print("*****************", file=log_file)
        last_played_chunk = max(int(current_chunk - 1e-10), 0)

        # Update QoE:
        # qoe = alpha * VIDEO_BIT_RATE[bit_rate] \
        #           - beta * rebuf \
        #           - gamma * np.abs(VIDEO_BIT_RATE[bit_rate] - VIDEO_BIT_RATE[last_bit_rate])
        QoE += alpha * bit_rate - beta * rebuf - gamma * abs(smooth)

        if QoE < MIN_QOE:  # Prevent dead loops
            print('Your QoE is too low...(Your video seems to have stuck forever) Please check for errors!')
            return

        # play over all videos
        if play_video_id >= ALL_VIDEO_NUM:
            print("The user leaves.", file=log_file)
            print("The user leaves.")
            break

        # Apply the participant's algorithm to decide the args for the next step
        download_video_id, bit_rate, sleep_time = abm.run(delay, rebuf, video_size, end_of_video, play_video_id, net_env.players, False)

        # print log info of the last operation
        print("\n\n*****************", file=log_file)
        # the operation detail
        if sleep_time != 0:
            print("You choose to sleep for ", sleep_time, " ms", file=log_file)
        else:
            print("Download Video ", download_video_id, " chunk (", net_env.players[download_video_id - play_video_id].get_chunk_counter() + 1, " / ",
                  net_env.players[download_video_id - play_video_id].get_chunk_sum(), ") with bitrate ", bit_rate, file=log_file)

    # QoE
    print("Your QoE is: ")
    print(QoE)
    # wasted_bytes
    print("Your sum of wasted bytes is:")
    print(sum_wasted_bytes)
    print("Your download/watch ratio (downloaded time / total watch time) is:")
    print(net_env.get_wasted_time_ratio())
    if QoE >= baseline_QoE * (1-TOLERANCE):  # if your QoE is in a tolerated range
        print("Your QoE meets the standard.")
    else:  # if your QoE is out of tolerance
        print("Your QoE is too low!")


if __name__ == '__main__':
    if args.baseline == '':
        test(False, args.user, args.trace)
    else:
        test(True, args.baseline, args.trace)
