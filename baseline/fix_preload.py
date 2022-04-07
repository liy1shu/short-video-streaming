# Comparison algorithm: No preloading approach
import numpy as np
import sys
sys.path.append("..")
from video_player import VIDEO_CHUNCK_LEN, BITRATE_LEVELS
import mpc_module

MPC_FUTURE_CHUNK_COUNT = 5     # MPC 
PAST_BW_LEN = 5
TAU = 500.0  # ms
RECOMMEND_QUEUE = 5  
MAX_PROLOAD_SIZE = 8000000.0   # B

class Algorithm:
    def __init__(self):
        # fill your self params
        self.buffer_size = 0
        self.past_bandwidth = []
        self.past_bandwidth_ests = []
        self.past_errors = []
        self.sleep_time = 0
        self.last_download_video_id = 0

    # Intial
    def Initialize(self):
        # Initialize your session or something
        # past bandwidth record
        self.past_bandwidth = np.zeros(PAST_BW_LEN)

    def estimate_bw(self, P):
        for _ in range(P):
            # first get harmonic mean of last 5 bandwidths
            curr_error = 0  # default assumes that this is the first request so error is 0 since we have never predicted bandwidth
            if (len(self.past_bandwidth_ests) > 0) and self.past_bandwidth[-1] != 0:
                curr_error = abs(self.past_bandwidth_ests[-1] - self.past_bandwidth[-1])/float(self.past_bandwidth[-1])
            self.past_errors.append(curr_error)
            while self.past_bandwidth[0] == 0.0 and self.past_bandwidth[0] == 0.0:
                self.past_bandwidth = self.past_bandwidth[1:]
            # print('in estimate bw')
            # print(past_bandwidths)
            bandwidth_sum = 0
            for past_val in self.past_bandwidth:
                bandwidth_sum += (1/float(past_val))
            harmonic_bandwidth = 1.0/(bandwidth_sum/len(self.past_bandwidth))

            # future bandwidth prediction
            # divide by 1 + max of last 5 (or up to 5) errors
            max_error = 0
            error_pos = -5
            if ( len(self.past_errors) < 5 ):
                error_pos = -len(self.past_errors)
            max_error = float(max(self.past_errors[error_pos:]))
            future_bandwidth = harmonic_bandwidth/(1+max_error)  # robustMPC here
            self.past_bandwidth_ests.append(harmonic_bandwidth) 
            self.past_bandwidth = np.roll(self.past_bandwidth, -1)
            self.past_bandwidth[-1] = future_bandwidth

    # Define your algorithm
    def run(self, delay, rebuf, video_size, end_of_video, play_video_id, Players):
        DEFAULT_QUALITY = 0
        # download a chunk, record the bitrate and update the network 
        if self.sleep_time == 0:
            self.past_bandwidth = np.roll(self.past_bandwidth, -1)
            self.past_bandwidth[-1] = float(video_size)/float(delay)  # B / ms
        
        P = []
        all_future_chunks_size = []
        future_chunks_highest_size = []
        for i in range(RECOMMEND_QUEUE):
            if Players[i].get_remain_video_num() == 0:      # download over
                # print('no remaining chunks to be downloaded for Player: ', i+play_video_id)
                P.append(0)
                all_future_chunks_size.append([0])
                future_chunks_highest_size.append([0])
                continue
            
            P.append(min(MPC_FUTURE_CHUNK_COUNT, Players[i].get_remain_video_num()))
            # P.append(Players[i].get_remain_video_num())
            all_future_chunks_size.append(Players[i].get_future_video_size(P[-1]))
            future_chunks_highest_size.append(all_future_chunks_size[-1][BITRATE_LEVELS-1])

        download_video_id = -1
        if rebuf > 0 and Players[0].get_remain_video_num() != 0:  # 如果正在播放的视频需要预缓冲，则必须下载当前视频
            # print("needs rebuf of ", play_video_id)
            # print("download ", play_video_id, " because of rebuf")
            download_video_id = play_video_id
        else:
            # download the playing video if downloading hasn't finished
            # otherwise preloads the videos on the recommendation queue in order
            if self.last_download_video_id == play_video_id and not end_of_video:  # the downloading video is the playing video & its not fully downloaded
                # print("last_download_video_id == play_video_id!!!!!")
                # print("download ", play_video_id, " because of unfinished")
                download_video_id = play_video_id
            else:
                for seq in range(RECOMMEND_QUEUE):
                    if Players[seq].get_preload_size() > MAX_PROLOAD_SIZE or Players[seq].get_remain_video_num() <= 0:
                        continue
                    else:
                        download_video_id = play_video_id + seq
                        # print("download ", download_video_id, " because of fixed_preload: preload_size ",  Players[seq].get_preload_size(), " <= ",  MAX_PROLOAD_SIZE)
                        break
            # self.last_download_video_id = download_video_id

        if download_video_id == -1:  # no need to download
            self.sleep_time = TAU
            bit_rate = 0
            download_video_id = play_video_id
        else:
            download_video_seq = download_video_id - play_video_id
            # update past_errors and past_bandwidth_ests
            # for k in range(download_video_seq + 1):
            #     self.estimate_bw(P[k])
            self.estimate_bw(P[download_video_seq])
            # print("download_video_seq", download_video_seq)
            buffer_size = Players[download_video_seq].get_buffer_size()  # ms
            video_chunk_remain = Players[download_video_seq].get_remain_video_num()
            # print("video_chunk_remain", video_chunk_remain)
            chunk_sum = Players[download_video_seq].get_chunk_sum()
            download_chunk_bitrate = Players[download_video_seq].get_downloaded_bitrate()
            last_quality = DEFAULT_QUALITY
            if len(download_chunk_bitrate) > 0:
                last_quality = download_chunk_bitrate[-1]
            # print("download: ", download_video_id, "last_download: ", self.last_download_video_id, "play: ", play_video_id, "P:", P)
            bit_rate = mpc_module.mpc(self.past_bandwidth, self.past_bandwidth_ests, self.past_errors, all_future_chunks_size[download_video_seq], P[download_video_seq], buffer_size, chunk_sum, video_chunk_remain, last_quality)
            self.sleep_time = 0.0
        self.last_download_video_id = download_video_id

        # print("download: ", download_video_id, "play: ",play_video_id)
        return download_video_id, bit_rate, self.sleep_time