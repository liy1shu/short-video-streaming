# Comparison algorithm: No preloading approach
import numpy as np
from video_player import VIDEO_CHUNCK_LEN, BITRATE_LEVELS
from pensieve.test.ABM import estimate_bw
from .. import mpc_module

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
        self.last_download_video_seq = 0

    # Intial
    def Initialize(self):
        # Initialize your session or something
        # past bandwidth record
        self.past_bandwidth = np.zeros(PAST_BW_LEN)

    def estimate_bw(self, P):
        for _ in range(P):
            # first get harmonic mean of last 5 bandwidths
            curr_error = 0 # default assumes that this is the first request so error is 0 since we have never predicted bandwidth
            if (len(self.past_bandwidth_ests) > 0):
                curr_error  = abs(self.past_bandwidth_ests[-1] - self.past_bandwidth[-1])/float(self.past_bandwidth[-1])
            self.past_errors.append(curr_error)
            while self.past_bandwidth[0] == 0.0:
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
                print('no remaining chunks to be downloaded')
                P.append(0)
                all_future_chunks_size.append([0])
                future_chunks_highest_size.append([0])
                continue
            
            P.append(MPC_FUTURE_CHUNK_COUNT)
            all_future_chunks_size.append(Players[i].get_future_video_size(P[-1]))
            future_chunks_highest_size.append(all_future_chunks_size[-1][BITRATE_LEVELS-1])
        
        # update past_errors and past_bandwidth_ests
        estimate_bw(P)
        
        # download the playing video if downloading hasn't finished     
        # otherwise preloads the videos on the recommendation queue in order
        download_video_id = -1
        if self.last_download_video_seq == 0: # the downloading video is the playing video
            if end_of_video:
                download_video_id = play_video_id + 1
            else:
                download_video_id = play_video_id
        else:
            for seq in range(1, RECOMMEND_QUEUE):
                if Players[seq].get_preload_size > MAX_PROLOAD_SIZE:
                    continue
                else:
                    download_video_id = play_video_id + seq
                    break
        if download_video_id == -1: # no need to download
            sleep_time = TAU
            bit_rate = 0
            download_video_id = 0
        else:
            download_video_seq = download_video_id - play_video_id
            buffer_size = Players[download_video_seq].get_buffer_size()  # ms
            video_chunk_remain = Players[download_video_seq].get_remain_video_num()
            chunk_sum = Players[download_video_seq].get_chunk_sum()
            download_chunk_bitrate = Players[download_video_seq].get_downloaded_bitrate()
            last_quality = DEFAULT_QUALITY
            if len(download_chunk_bitrate) > 0:
                last_quality = download_chunk_bitrate[-1]
            download_video_id = play_video_id
            bit_rate = mpc_module.mpc(self.past_bandwidth, self.past_bandwidth_ests, self.past_errors, self.all_future_chunks_size[download_video_seq], P, buffer_size, chunk_sum, video_chunk_remain, last_quality)
            sleep_time = 0.0
        self.last_download_seq = download_video_id - play_video_id
        return download_video_id, bit_rate, sleep_time