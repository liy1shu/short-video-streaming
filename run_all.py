from cmath import inf
import os
import numpy as np
from re import S
import sys
import itertools
from simulator.network_module import Network
sys.path.append('./simulator/')
from simulator import controller as env, short_video_load_trace
VIDEO_SIZE_FILE = 'data/short_video_size/'
NETWORK_TRACE_FILE = 'data/network_traces/'
BEHAVIOR_FILE = 'data/user_behavior/'
VIDEO_BIT_RATE = [750,1200,1850]  # Kbps


# QoE arguments
alpha = 1
beta = 1.85
gamma = 1
theta = 0.5
ALL_VIDEO_NUM = 7
baseline_QoE = 600  # baseline's QoE
TOLERANCE = 0.1  # The tolerance of the QoE decrease
MIN_QOE = -1e9

RANDOM_SEED = 42  # the random seed for user retention
np.random.seed(RANDOM_SEED)
user_sample_cnt = 50
seeds = np.random.randint(100, size=(user_sample_cnt))  # seeds for generating the user_ret sample seed

def test(trace_name, trace_id, behavior_id, video_list, seed):
    min_score = +inf
    max_score = -inf
    score = []
    
    filepath = []
    filepath.append('./baseline/')
    filepath.append('./quickstart/')

    for path in filepath:
        sys.path.append(path)
        if path == './baseline/':
            import no_save as Solution
        else:
            import fix_preload as Solution
        sys.path.remove(path)

    # else:  # Testing participant's algorithm
    #     sys.path.append(user_id)
    #     import Solution
    #     sys.path.remove(user_id)
    #     LOG_FILE = 'logs/log.txt'
        solution = Solution.Algorithm()
        solution.Initialize()

        all_cooked_time, all_cooked_bw = short_video_load_trace.load_trace(trace_name)
        net_env = env.Environment(all_cooked_time[trace_id], all_cooked_bw[trace_id], ALL_VIDEO_NUM, behavior_id, video_list, seed)

        # Decision variables
        download_video_id, bit_rate, sleep_time = solution.run(0, 0, 0, False, 0, net_env.players, True)  # take the first step

        # sum of wasted bytes for a user
        sum_wasted_bytes = 0
        QoE = 0
        bandwidth_usage = 0  # record total bandwidth usage

        while True:
            delay, rebuf, video_size, end_of_video, \
            play_video_id, waste_bytes, smooth = net_env.buffer_management(download_video_id, bit_rate, sleep_time)
            # print(delay, rebuf, video_size, end_of_video, play_video_id, waste_bytes)

            # Update bandwidth usage
            bandwidth_usage += video_size

            # Update bandwidth wastage
            sum_wasted_bytes += waste_bytes  # Sum up the bandwidth wastage

            # print log info of the last operation
            if play_video_id < ALL_VIDEO_NUM:
                # the operation results
                current_chunk = net_env.players[0].get_play_chunk()
                current_bitrate = net_env.players[0].get_video_quality(max(int(current_chunk - 1e-10), 0))

            # Update QoE:
            QoE += alpha * VIDEO_BIT_RATE[bit_rate] / 1000. - beta * rebuf / 1000. - gamma * abs(smooth) / 1000.

            if QoE < MIN_QOE:  # Prevent dead loops
                # print('Your QoE is too low...(Your video seems to have stuck forever) Please check for errors!')
                return

            # play over all videos
            if play_video_id >= ALL_VIDEO_NUM:
                # print("The user leaves.")
                break

            # Apply the participant's algorithm to decide the args for the next step
            download_video_id, bit_rate, sleep_time = solution.run(delay, rebuf, video_size, end_of_video, play_video_id, net_env.players, False)

        # Score
        S = QoE - theta * bandwidth_usage * 8 / 1000000.
        if S > max_score:
            max_score = S
        if S < min_score:
            min_score = S
        score.append(S)

        # # QoE
        # print("Your QoE is: ")
        # print(QoE)
        # # wasted_bytes
        # print("Your sum of wasted bytes is:")
        # print(sum_wasted_bytes)
        # print("Your download/watch ratio (downloaded time / total watch time) is:")
        # print(net_env.get_wasted_time_ratio())
    print("------------------------------")
    print(trace_name, trace_id, behavior_id, video_list)
    print("baseline_S: " , score[0])
    print("quickstart_S ", score[1])
    print("------------------------------")
    r_score = [(s - min_score) / (max_score - min_score) for s in score]
    # print(r_score)
    return r_score

def get_scenario():
    # create scenaios: permutation of trace_name, trace_id, behavior_id, video_list
    scenarios = []
    
    # get video sequence 
    video_sequence = []
    video_folder = os.listdir(VIDEO_SIZE_FILE)
    # for i in itertools.permutations(vio, len(video)):
    #     video_sequence.append(i)
    seq1 = video_folder
    video_sequence.append(seq1)
    seq2 = [video_folder[len(video_folder) - i - 1] for i in range(len(video_folder))]
    video_sequence.append(seq2)
    # print(video_sequence)

    # get behavior
    # behavior = os.listdir(BEHAVIOR_FILE)
    # print(behavior)

    # get network traces
    network_type = os.listdir(NETWORK_TRACE_FILE)
    for level in network_type:
        scenario = {'trace_name': level}
        network_file = os.listdir(os.path.join(NETWORK_TRACE_FILE + level))
        for i in range(len(network_file)):
            scenario['trace_id'] = i
            for seq in video_sequence:
                scenario['video_list'] = seq
                # for b in behavior:
                #     scenario['behavior_id'] = b
                #     scenarios.append(scenario.copy())
                for sample_id in range(user_sample_cnt):
                    np.random.seed(seeds[sample_id])
                    seed = np.random.randint(10000, size=(7,2)) # 7 * 2 means 7 videos each with 2 sample seed
                    scenario['seed'] = seed
                    scenarios.append(scenario.copy())

    return scenarios

def score():
    scenarios = get_scenario()
    score = [0, 0]
    for scenario in scenarios:
        # res = test(scenario['trace_name'], scenario['trace_id'], scenario['behavior_id'], scenario['video_list'])
        res = test(scenario['trace_name'], scenario['trace_id'], 'random', scenario['video_list'], scenario['seed'])
        for i in range(len(res)):
            score[i] += res[i]
    print("baseline_T: " , score[0])
    print("quickstart_T ", score[1])

if __name__ == '__main__':
    score()