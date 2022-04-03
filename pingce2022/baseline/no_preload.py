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

class Algorithm:
    def __init__(self):
        # fill your self params
        self.buffer_size = 0
        self.past_bandwidth = []
        self.past_bandwidth_ests = []
        self.past_errors = []
        self.sleep_time = 0

    # Intial
    def Initialize(self):
        # Initialize your session or something
        # past bandwidth record
        self.past_bandwidth = np.zeros(PAST_BW_LEN)

    def estimate_bw(self):
        for _ in range(MPC_FUTURE_CHUNK_COUNT):
            # first get harmonic mean of last 5 bandwidths
            curr_error = 0  # default assumes that this is the first request so error is 0 since we have never predicted bandwidth
            if len(self.past_bandwidth_ests) > 0 and self.past_bandwidth[-1] != 0:
                curr_error  = abs(self.past_bandwidth_ests[-1] - self.past_bandwidth[-1])/float(self.past_bandwidth[-1])
            self.past_errors.append(curr_error)
            while len(self.past_bandwidth) != 0 and self.past_bandwidth[0] == 0.0:
                self.past_bandwidth = self.past_bandwidth[1:]
            # print('in estimate bw')
            # print('past_bandwidth: ', self.past_bandwidth)
            bandwidth_sum = 0
            for past_val in self.past_bandwidth:
                # print('past_bandwidth: ', self.past_bandwidth)
                # print('past_val', past_val)
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
            print("float(video_size):::\n", float(video_size))
            print("float(delay):::\n", float(delay))
            print("past_bandwith::::", self.past_bandwidth)
        
        P = []
        all_future_chunks_size = []
        future_chunks_highest_size = []
        # print("Recommend queue:\n", RECOMMEND_QUEUE)
        download_video_id_relative = -1
        for i in range(RECOMMEND_QUEUE):
            if Players[i].get_remain_video_num() == 0:      # download over
                # print('no remaining chunks to be downloaded')
                P.append(0)
                all_future_chunks_size.append([0])
                future_chunks_highest_size.append([0])
                continue

            if download_video_id_relative == -1:
                download_video_id_relative = i
            P.append(MPC_FUTURE_CHUNK_COUNT)
            # print("Recommend queue:\n", RECOMMEND_QUEUE)
            # print("P[-1] player:::\n", Players[i].get_future_video_size(P[-1]))
            all_future_chunks_size.append(Players[i].get_future_video_size(P[-1]))
            # print("all_future_chunks_size:\n", all_future_chunks_size)
            future_chunks_highest_size.append(all_future_chunks_size[-1][BITRATE_LEVELS-1])
        
        # update past_errors and past_bandwidth_ests
        self.estimate_bw()
        
        # download the playing video if downloading hasn't finished 
        if end_of_video or download_video_id_relative == -1:
            self.sleep_time = TAU
            self.bit_rate = 0
            self.download_video_id = 0
        else:
            self.buffer_size = Players[0].get_buffer_size()  # ms
            self.video_chunk_remain = Players[0].get_remain_video_num()
            self.chunk_sum = Players[0].get_chunk_sum()
            self.download_chunk_bitrate = Players[0].get_downloaded_bitrate()
            self.last_quality = DEFAULT_QUALITY
            if len(self.download_chunk_bitrate) > 0:
                self.last_quality = self.download_chunk_bitrate[-1]
            self.download_video_id = play_video_id + download_video_id_relative
            # print("download_video_seq::::::!!!!", all_future_chunks_size)
            self.bit_rate = mpc_module.mpc(self.past_bandwidth, self.past_bandwidth_ests, self.past_errors, all_future_chunks_size[download_video_id_relative], MPC_FUTURE_CHUNK_COUNT, self.buffer_size, self.chunk_sum, self.video_chunk_remain, self.last_quality)
            self.sleep_time = 0.0
        return self.download_video_id, self.bit_rate, self.sleep_time