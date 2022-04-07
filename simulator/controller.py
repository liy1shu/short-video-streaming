# input: download_video_id, bitrate, sleep_time
# output: info needed by schedule algorithm
# buffer: ms

import numpy as np
import math
from numpy.lib.utils import _split_line
from video_player import Player, VIDEO_CHUNCK_LEN
from user_module import Retention
from network_module import Network

USER_FILE = 'logs/sample_user/user.txt'
user_file = open(USER_FILE, 'wb')
LOG_FILE = 'logs/log.txt'
log_file = open(LOG_FILE, 'a')

NEW = 0
DEL = 1

RECOMMEND_QUEUE = 5

class Environment:
    def __init__(self, all_cooked_time, all_cooked_bw):
        self.players = []
        self.user_models = []  # 和players同步更新，存储该视频的用户行为(Retention类)
        self.video_num = 0
        self.play_video_id = 0
        self.network = Network(all_cooked_time, all_cooked_bw)
        self.timeline = 0.0
        # for ratio
        self.total_watched_len = 0.0
        self.total_downloaded_len = 0.0

        # self.download_permit = set()
        for p in range(RECOMMEND_QUEUE):
            # self.download_permit.add(p)
            self.players.append(Player(p))
            user_time, user_retent_rate = self.players[-1].get_user_model()
            self.user_models.append(Retention(user_time, user_retent_rate))
            self.total_watched_len += self.user_models[-1].get_ret_duration()  # sum the total watch duration
            self.video_num += 1
            user_file.write((str(self.user_models[-1].get_ret_duration()) + '\n').encode())
            user_file.flush()
        
        self.start_video_id = 0
        self.end_video_id = RECOMMEND_QUEUE - 1

    def player_op(self, operation):
        if operation == NEW:
            # print('--------------ADD--------------')
            self.players.append(Player(self.video_num))
            self.total_watched_len += self.user_models[-1].get_ret_duration()  # sum the total watch duration
            user_time, user_retent_rate = self.players[-1].get_user_model()
            self.user_models.append(Retention(user_time, user_retent_rate))
            self.video_num += 1
            # record the user retention rate
            # user_file.write((str(self.players[-1].get_watch_duration()) + '\n').encode())
            user_file.write((str(self.user_models[-1].get_ret_duration()) + '\n').encode())
            user_file.flush()
        else:
            # print('--------------DEL--------------')
            self.players.remove(self.players[0])
            self.user_models.remove(self.user_models[0])
    
    def get_start_video_id(self):
        return self.start_video_id

    def get_wasted_time_ratio(self):
        return self.total_downloaded_len / self.total_watched_len

    def play_videos(self, time_len):  # play for time_len from the start of current players queue
        # print("\n\nPlaying Video ", self.start_video_id)
        wasted_bd = 0
        play_tm, buffer = self.players[0].video_play(time_len)
        # print(self.start_video_id, time_len, play_tm, buffer)
        while time_len > 0 and play_tm >= min(self.players[0].get_video_len(), self.user_models[0].get_ret_duration()):  # 如果时间没过完就结束播放
            time_len = play_tm - min(self.players[0].get_video_len(), self.user_models[0].get_ret_duration())
            # 放完当前视频：输出当前视频下载了多少秒，共多少秒，用户在第几秒离开
            print("User stopped watching Video ", self.start_video_id, "( ", self.players[0].get_video_len(), " ms ) :")
            print("User watched for ", self.user_models[0].get_ret_duration(), " ms, you downloaded ", self.players[0].get_chunk_counter()*VIDEO_CHUNCK_LEN, " sec. \n")
            self.total_downloaded_len += self.players[0].get_chunk_counter()*VIDEO_CHUNCK_LEN  # sum up the total downloaded time
            wasted_bd += self.players[0].bandwidth_waste(self.user_models[0])  # use watch duration as an arg

            # 窗口往前滑动
            self.player_op(DEL)
            self.start_video_id += 1
            self.player_op(NEW)
            self.end_video_id += 1
            # 开始播放下一个视频
            self.play_video_id += 1

            play_tm, buffer = self.players[0].video_play(time_len)
            # print(self.start_video_id, time_len, play_tm, buffer)
        return play_tm, buffer, wasted_bd
              
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
            # play_timeline, buffer = self.players[self.play_video_id - self.start_video_id].video_play(sleep_time)
            play_timeline, buffer, wasted = self.play_videos(sleep_time)
            # print(self.play_video_id, play_timeline, buffer)
            # 设置为返回当前下载视频的长度
            end_of_video = (self.players[self.play_video_id-self.start_video_id].get_remain_video_num() == 0)
        else:
            # print("download...")
            # print('download video id %d' % download_video_id)
            # print('start video id %d' % self.start_video_id)
            video_size = self.players[download_video_id-self.start_video_id].get_video_size(bitrate)
            self.players[download_video_id - self.start_video_id].record_download_bitrate(bitrate)
            delay = self.network.network_simu(video_size)  # ms
            # play_timeline, buffer = self.players[self.play_video_id - self.start_video_id].video_play(delay)
            play_timeline, buffer, wasted = self.play_videos(delay)
            if download_video_id < self.start_video_id:  # 用户已经切掉该视频，因此该视频player已经被摧毁，只需要累计wasted
                print("Extra chunk downloaded for Video ", download_video_id,
                      " which the user already finished watching.\n")
                wasted += video_size  # 因为已经播放完，所以说明下载一定是多余的
                self.total_downloaded_len += VIDEO_CHUNCK_LEN  # sum up the total downloaded time
                end_of_video = True
            else:
                end_of_video = self.players[download_video_id-self.start_video_id].video_download(VIDEO_CHUNCK_LEN)
        
        # print('delay: %f ms' % delay)
        # print('buffer: %f ms' % buffer)
        # 累计带宽浪费
        wasted_bytes += wasted
        if buffer < 0:
            rebuf = abs(buffer)
            # print("You caused rebuf for Video ", self.play_video_id, " of ", rebuf, " ms")

        # while True:
        #     # print('play_video_id: %2d' % self.play_video_id)
        #     watch_duration = np.minimum(self.players[self.play_video_id - self.start_video_id].get_watch_duration(),
        #                                 self.players[self.play_video_id - self.start_video_id].get_video_len())
        #     # print(self.play_video_id - self.start_video_id)
        #     # print('watch duration')
        #     # print(watch_duration)
        #     # print('play timeline')
        #     # print(play_timeline)
        #     # print('diff')
        #     # print(watch_duration-play_timeline)
        #
        #     if play_timeline < watch_duration:
        #         if not math.isclose(play_timeline, watch_duration, abs_tol=1e-8):
        #             # print('play_timeline < watch_duration')
        #             break
        #
        #     # print('play a video over')
        #     # Sum up the wasted bytes. The first video is the video played over.
        #     wasted_bytes += self.players[0].bandwidth_waste()
        #     # print("lys test::::wasted!!!!", wasted_bytes)
        #     self.player_op(DEL)
        #     self.start_video_id += 1
        #     # print(self.start_video_id)
        #     self.player_op(NEW)
        #     self.end_video_id += 1
        #     # print(self.end_video_id)
        #     # print(play_timeline)
        #     # print(watch_duration)
        #     play_timeline -= watch_duration
        #     # print(play_timeline)
        #     self.play_video_id += 1
        #     # print(self.play_video_id)
        

        return delay, rebuf, video_size, end_of_video, self.play_video_id, wasted_bytes
