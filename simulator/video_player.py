# multi-video play
import numpy as np
import math

BITRATE_LEVELS = 6
VIDEO_BIT_RATE = [300,750,1200,1850,2850,4300]  # Kbps
VIDEO_CHUNCK_LEN = 1000.0
MILLISECONDS_IN_SECOND = 1000.0
VIDEO_SIZE_FILE = 'data/short_video_size/video_size_'
VIDEO_SIZE_SCALE = 4.0  # 4s->1s chunk size
USER_RET = './data/user_ret/user_ret_'

DISTINCT_VIDEO_NUM = 9

class Player:
    # initialize each new video and player buffer
    def __init__(self, video_num):  
        # initialize each new video
        self.video_size = {}  # in bytes
        for bitrate in range(BITRATE_LEVELS):
            self.video_size[bitrate] = []
            file_name = VIDEO_SIZE_FILE + str(video_num%DISTINCT_VIDEO_NUM) + '_' + str(bitrate)
            with open(file_name) as f:
                for line in f:
                    self.video_size[bitrate].append(int(line.split()[0])/VIDEO_SIZE_SCALE)
        
        # num and len of the video, all chunks are counted instead of -1 chunk
        self.chunk_num = len(self.video_size[0])
        self.video_len = self.chunk_num * VIDEO_CHUNCK_LEN  # ms
        
        # download chunk counter
        self.video_chunk_counter = 0
        self.video_chunk_remain = self.chunk_num - self.video_chunk_counter
        
        self.download_chunk_bitrate = []
        
        # play chunk counter
        self.video_play_counter = 0
        
        # play timeline of this video
        self.play_timeline = 0.0
        
        # initialize the buffer
        self.buffer_size = 0  # ms
        
        # initialize preload size
        self.preload_size = 0 # B

        # initialize corresponding user watch time
        self.user_time = []  # user_model which players have access to!!
        self.user_retent_rate = []
        with open(USER_RET + str(video_num % DISTINCT_VIDEO_NUM)) as file:
            for line in file:
                self.user_time.append(float(line.split()[0]) * MILLISECONDS_IN_SECOND)
                self.user_retent_rate.append(line.split()[1])

    def get_user_model(self):
        return self.user_time, self.user_retent_rate
    
    def get_video_len(self):
        return self.video_len

    def get_video_size(self, quality):
        video_chunk_size = self.video_size[quality][self.video_chunk_counter]
        self.preload_size += video_chunk_size
        return video_chunk_size

    # get size of all preloaded chunks
    def get_preload_size(self):
        return self.preload_size
    
    def get_future_video_size(self, P):
        interval = 1
        chunk_playing = self.get_play_chunk()
        if chunk_playing % 1 == 0:        # Check whether it is an integer
                interval = 0
                
        future_videosize = []
        for i in range(BITRATE_LEVELS):
            size_in_level = []
            for k in range(P):
                size_in_level.append(self.video_size[i][int(chunk_playing+interval+k)])
            future_videosize.append(size_in_level)
        return future_videosize

    def get_play_chunk(self):
        return self.play_timeline / VIDEO_CHUNCK_LEN
    
    def get_remain_video_num(self):
        self.video_chunk_remain = self.chunk_num - self.video_chunk_counter
        return self.video_chunk_remain
    
    def get_chunk_sum(self):
        return self.chunk_num

    def get_chunk_counter(self):
        return self.video_chunk_counter

    def get_buffer_size(self):
        return self.buffer_size
    
    def record_download_bitrate(self, bit_rate):
        self.download_chunk_bitrate.append(bit_rate)
    
    def get_downloaded_bitrate(self):
        return self.download_chunk_bitrate
    
    def bandwidth_waste(self, user_ret):
        download_len = len(self.download_chunk_bitrate)
        waste_start_chunk = math.ceil(user_ret.get_ret_duration() / VIDEO_CHUNCK_LEN)
        sum_waste_each_video = 0
        for i in range(waste_start_chunk, download_len):
            download_bitrate = self.download_chunk_bitrate[i]
            download_size = self.video_size[download_bitrate][i]
            print("lys test:::: chunk ", i, "of bitrate[", download_bitrate, "] costs ", download_size)
            sum_waste_each_video += download_size
        return sum_waste_each_video
            
    # download the video, buffer increase.
    def video_download(self, download_len):  # ms
        self.buffer_size += download_len
        self.video_chunk_counter += 1
        end_of_video = False
        if self.video_chunk_counter >= self.chunk_num:
            end_of_video = True
        return end_of_video

    # play the video, buffer decrease. Return the remaining buffer, negative number means rebuf
    def video_play(self, play_time):  # ms
        buffer = self.buffer_size - play_time
        self.play_timeline += np.minimum(self.buffer_size, play_time)   # rebuffering time is not included in timeline
        self.buffer_size = np.maximum(self.buffer_size - play_time, 0.0)
        return self.play_timeline, buffer



