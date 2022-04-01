# Adaptive Buffer Management approach

import short_video_load_trace
import controller as env
import numpy as np
from scipy import optimize
# from test.mpc import DEFAULT_QUALITY
from video_player import VIDEO_CHUNCK_LEN, BITRATE_LEVELS
import mpc_module  

RETENTION_THRESHOLD = 0.85   # P的确定阈值
MAX_P = 5
MIN_P = 1
MPC_FUTURE_CHUNK_COUNT = 5     # MPC 
RECOMMEND_QUEUE = 5
ALL_VIDEO_NUM = 9
PAST_BW_LEN = 5
DEFAULT_QUALITY = 1  # default video quality without agent
TAU = 500.0  # ms  

SUMMARY_DIR = './ABM_results'
LOG_FILE = './ABM_results/log_sim_abm'

past_errors = []
past_bandwidth_ests = []

# 单位 时间单位是ms size的单位是B 

def estimate_bw(past_bandwidths):
    # first get harmonic mean of last 5 bandwidths
    curr_error = 0 # default assumes that this is the first request so error is 0 since we have never predicted bandwidth
    if ( len(past_bandwidth_ests) > 0 ):
        curr_error  = abs(past_bandwidth_ests[-1] - past_bandwidths[-1])/float(past_bandwidths[-1])
    past_errors.append(curr_error)
    while past_bandwidths[0] == 0.0:
        past_bandwidths = past_bandwidths[1:]
    # print('in estimate bw')
    # print(past_bandwidths)
    bandwidth_sum = 0
    for past_val in past_bandwidths:
        bandwidth_sum += (1/float(past_val))
    harmonic_bandwidth = 1.0/(bandwidth_sum/len(past_bandwidths))

    # future bandwidth prediction
    # divide by 1 + max of last 5 (or up to 5) errors
    max_error = 0
    error_pos = -5
    if ( len(past_errors) < 5 ):
        error_pos = -len(past_errors)
    max_error = float(max(past_errors[error_pos:]))
    future_bandwidth = harmonic_bandwidth/(1+max_error)  # robustMPC here
    past_bandwidth_ests.append(harmonic_bandwidth) 
    
    return future_bandwidth

def bwSave(current_b, bandwidth, future_chunks_size, P): 
    # input: current buffer, bandwidth estimation, highest size of future chunks in P
    # output: max waiting time x
    print(current_b)
    # linear programing
    Z = np.array([-1])
    A = np.mat([[1]] * P)
    cons_term = []  # ms
    sum_downloat_t = 0.0  # ms
    
    # print(P)
    # print(future_chunks_size)
    # exit()
    print(cons_term)
    for p in range(P):
        # print('bwSave')
        # print(bandwidth)  # B/ms
        bw_est = estimate_bw(bandwidth)
        print(bw_est)
        sum_downloat_t += float(future_chunks_size[p] / bw_est)  # ms += B / B/ms
        print(sum_downloat_t)
        cons_term.append(current_b + p * VIDEO_CHUNCK_LEN - sum_downloat_t)
        print(current_b + p * VIDEO_CHUNCK_LEN - sum_downloat_t)
        print(cons_term)
        # print(cons_term)
        bandwidth = np.roll(bandwidth, -1)
        bandwidth[-1] = bw_est
    
    print(cons_term)
    B = np.mat(cons_term)
    x_bound = (-1000000, current_b)  # lower bound is 
    
    print(Z)
    print(A)
    print(B)
    
    res = optimize.linprog(Z, A_ub = A, b_ub = B, bounds = (x_bound))
    
    # 为什么应该有解的解不出来？ x_bound加了下限就可以解出来了
    print('x')
    print(res.x)
    return res.x  # negative x represents cannot wait without downloading
    # return np.min(B)
    
    
def Re_bwSave(env, past_bandwidth, future_chunks_size, P):
    # conditions of the playing video
    # current_b = env.players[0].get_buffer_size()
    # x = bwSave(current_b, past_bandwidth, future_chunks_size[0])
    
    # the playing video should be downloaded
    # if x <= 0:
    #     return 0
    # else:
    #     target_buffer = current_b - x
    #     for k in range(1, RECOMMEND_QUEUE):
    #         current_b = env.players[k].get_buffer_size()
    #         # if target_buffer < current_b:
    #         #     continue
    #         # else:
    #         x = bwSave(current_b, past_bandwidth, future_chunks_size[k])
    #         if x <= 0:
    #             return k
    xs = []
    for k in range(RECOMMEND_QUEUE):
        if P[k] == 0:
            xs.append(-1)
            continue
        current_b = env.players[k].get_buffer_size()
        print('current_b')
        print(current_b)
        x = bwSave(current_b, past_bandwidth, future_chunks_size[k], P[k])
        print(x)
        xs.append(float(x))
        print(xs)
        if x <= 0:
            return k, xs
    
    return -1, xs  # all videos current buffer are enough and no video should be downloaded according to current conditions
    

def main():
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
    # ID of the playing video
    # play_video_id = 0
    # pre_video_id = play_video_id
    
    DEFAULT_QUALITY = 0
    
    # past bandwidth record
    past_bandwidth = np.zeros(PAST_BW_LEN)
    
    while True:
        delay, rebuf, video_size, end_of_video, \
        play_video_id, waste_bytes = net_env.buffer_management(download_video_id, bit_rate, sleep_time)
        print('Video %d is playing.' % play_video_id)
        
        sum_wasted_bytes += waste_bytes
        
        # play over all videos
        if play_video_id >= ALL_VIDEO_NUM: 
            print("The user leaves.")  
            break
        
        # download a chunk, record the bitrate and update the network 
        if sleep_time == 0:
            net_env.players[download_video_id-net_env.get_start_video_id()].record_download_bitrate(bit_rate)
            past_bandwidth = np.roll(past_bandwidth, -1)
            past_bandwidth[-1] = float(video_size)/float(delay)  # B / ms
            
        # P的确定，条件概率大于RETENTION_THRESHOLD，不同视频的P不同. 范围[MIN_P, MAX_P]，比如[1,5]
        # 如果此视频块下载完成，P为0
        P = []
        all_future_chunks_size = []
        future_chunks_highest_size = []
        for i in range(RECOMMEND_QUEUE):
            if net_env.players[i].get_remain_video_num() == 0:      # download over
                print('no remaining chunks to be downloaded')
                P.append(0)
                all_future_chunks_size.append([0])
                future_chunks_highest_size.append([0])
                continue
            
            interval = 1
            sum = 0
            start_chunk = int(net_env.players[i].get_play_chunk())
            if net_env.players[i].get_play_chunk() % 1 == 0:
                interval = 0
            while start_chunk + interval <= net_env.players[i].get_chunk_sum() - 1:
                cond_p = net_env.players[i].user_ret.conditional_p(start_chunk, interval)
                print('cond_p %f' % cond_p)
                if cond_p >= RETENTION_THRESHOLD:
                    sum += 1
                    interval += 1
                else:
                    break
            print('sum %d' % sum)    
            P.append(np.maximum(MIN_P, np.minimum(sum, MAX_P)))
            all_future_chunks_size.append(net_env.players[i].get_future_video_size(P[-1]))
            future_chunks_highest_size.append(all_future_chunks_size[-1][BITRATE_LEVELS-1])
                        
        # 根据P，确定下载视频id
        download_video_seq, xs = Re_bwSave(net_env, past_bandwidth, future_chunks_highest_size, P)  # 序号 [0, RECOMMEND_QUEUE]
        
        print('-------------')
        print(P)
        print(xs)
        
        # 如果有需要被下载的视频，调用MPC，确定bit_rate and download_video_id
        if download_video_seq >= 0:
            print('if')
            buffer_size = net_env.players[download_video_seq].get_buffer_size()  # ms
            video_chunk_remain = net_env.players[download_video_seq].get_remain_video_num()
            chunk_sum = net_env.players[download_video_seq].get_chunk_sum()
            download_chunk_bitrate = net_env.players[download_video_seq].get_downloaded_bitrate()
            last_quality = DEFAULT_QUALITY
            if len(download_chunk_bitrate) > 0:
                last_quality = download_chunk_bitrate[-1]
            
            bit_rate = mpc_module.mpc(past_bandwidth, past_bandwidth_ests, past_errors, all_future_chunks_size[download_video_seq], P[download_video_seq], buffer_size, chunk_sum, video_chunk_remain, last_quality)
        
            download_video_id = download_video_seq + net_env.get_start_video_id()
            sleep_time = 0.0
        else:  
            print('else')  
            # 没有需要被下载的视频
            if xs[0] >= 0:  # 正在播放的视频target buffer>0并且还有块可以被下载
                sleep_time = xs[0]
                print(xs[0])
            else:  # 正在播放的视频已经全部下完了，等tau时间再看情况
                sleep_time = TAU
            
            bit_rate = 0
            download_video_id = 0
            
        print("*****************")
        print('sleep time:')
        print(sleep_time) 
        print('downlad video ID')
        print(download_video_id)
        print('bitrate download:')
        print(bit_rate)
    
    # statistics
    print("sum_wasted_bytes")
    print(sum_wasted_bytes)  

if __name__ == '__main__':
    main()