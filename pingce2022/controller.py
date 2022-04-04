# input: download_video_id, bitrate, sleep_time
# output: info needed by schedule algorithm
# buffer: ms

import numpy as np
import math
from numpy.lib.utils import _split_line
from video_player import Player, VIDEO_CHUNCK_LEN
from network_module import Network

USER_FILE = './sample_user/user.txt'
log_file = open(USER_FILE, 'wb')

NEW = 0
DEL = 1

RECOMMEND_QUEUE = 5

class Environment:
    def __init__(self, all_cooked_time, all_cooked_bw):
        self.players = []   
        self.video_num = 0
        self.play_video_id = 0
        self.network = Network(all_cooked_time, all_cooked_bw)
        self.timeline = 0.0
        
        # self.download_permit = set()
        for p in range(RECOMMEND_QUEUE):
            # self.download_permit.add(p)
            self.players.append(Player(p))
            self.video_num += 1
            log_file.write((str(self.players[-1].get_watch_duration()) + '\n').encode())
            log_file.flush()
        
        self.start_video_id = 0
        self.end_video_id = RECOMMEND_QUEUE - 1

    def player_op(self, operation):
        if operation == NEW:
            # print('--------------ADD--------------')
            self.players.append(Player(self.video_num))
            self.video_num += 1
            # record the user retention rate
            log_file.write((str(self.players[-1].get_watch_duration()) + '\n').encode())
            log_file.flush()
        else:
            # print('--------------DEL--------------')
            self.players.remove(self.players[0])
    
    def get_start_video_id(self):
        return self.start_video_id
              
    def buffer_management(self, download_video_id, bitrate, sleep_time):
        buffer = 0
        rebuf = 0
        end_of_video = False
        delay = 0
        video_size = 0
        wasted_bytes = 0
        
        # 待优化：如果当前正在播放的视频卡了，立刻切回来这个视频的下载
        if sleep_time > 0:
            # print("sleep for a while...")
            delay = sleep_time
            # print('sleep_time')
            # print(sleep_time)
            play_timeline, buffer = self.players[self.play_video_id - self.start_video_id].video_play(sleep_time)
            end_of_video = self.players[download_video_id-self.start_video_id].video_download(VIDEO_CHUNCK_LEN)  
        else:
            # print("download...")
            # print('download video id %d' % download_video_id)
            # print('start video id %d' % self.start_video_id)
            video_size = self.players[download_video_id-self.start_video_id].get_video_size(bitrate)
            delay = self.network.network_simu(video_size)  # ms
            play_timeline, buffer = self.players[self.play_video_id - self.start_video_id].video_play(delay)
            end_of_video = self.players[download_video_id-self.start_video_id].video_download(VIDEO_CHUNCK_LEN)
        
        # print('delay: %f ms' % delay)
        # print('buffer: %f ms' % buffer)
        if buffer < 0:
            rebuf = abs(buffer)

        while True:
            # print('play_video_id: %2d' % self.play_video_id)
            watch_duration = np.minimum(self.players[self.play_video_id - self.start_video_id].get_watch_duration(), self.players[self.play_video_id - self.start_video_id].get_video_len())
            # print(self.play_video_id - self.start_video_id)
            # print('watch duration')
            # print(watch_duration)
            # print('play timeline')
            # print(play_timeline)
            # print('diff')
            # print(watch_duration-play_timeline)
            
            if play_timeline < watch_duration:
                if not math.isclose(play_timeline, watch_duration, abs_tol=1e-8):
                    # print('play_timeline < watch_duration')
                    break
            
            # print('play a video over')
            # Sum up the wasted bytes. The first video is the video played over.
            wasted_bytes += self.players[0].bandwidth_waste() 
            self.player_op(DEL)
            self.start_video_id += 1
            # print(self.start_video_id)
            self.player_op(NEW)
            self.end_video_id += 1
            # print(self.end_video_id)
            # print(play_timeline)
            # print(watch_duration)
            play_timeline -= watch_duration
            # print(play_timeline)
            self.play_video_id += 1
            # print(self.play_video_id)
        

        return delay, rebuf, video_size, end_of_video, self.play_video_id, wasted_bytes
