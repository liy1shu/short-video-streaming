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
        self.user_models = []  # Record the user action(Retention class) for the current video, update synchronized with players
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
        while time_len > 0 and play_tm >= min(self.players[0].get_video_len(), self.user_models[0].get_ret_duration()) - 1e-10:  # 如果时间没过完就结束播放
            time_len = play_tm - min(self.players[0].get_video_len(), self.user_models[0].get_ret_duration())
            # After user ended the current video
            # Output: the downloaded time length, the total time length, the watch duration
            print("User stopped watching Video ", self.start_video_id, "( ", self.players[0].get_video_len(), " ms ) :")
            print("User watched for ", self.user_models[0].get_ret_duration(), " ms, you downloaded ", self.players[0].get_chunk_counter()*VIDEO_CHUNCK_LEN, " sec. \n")
            # print("lys test:::: The bandwidth_waste is:")
            self.total_downloaded_len += self.players[0].get_chunk_counter()*VIDEO_CHUNCK_LEN  # sum up the total downloaded time
            wasted_bd += self.players[0].bandwidth_waste(self.user_models[0])  # use watch duration as an arg

            # Forward the queue to the next video
            self.player_op(DEL)
            self.start_video_id += 1
            if self.play_video_id < self.video_num:
                self.player_op(NEW)
                self.end_video_id += 1
                # Start to play the next video
                self.play_video_id += 1
                play_tm, buffer = self.players[0].video_play(time_len)
            else:
                break
            # print(self.start_video_id, time_len, play_tm, buffer)
        return play_tm, buffer, wasted_bd
              
    def buffer_management(self, download_video_id, bitrate, sleep_time):
        buffer = 0
        rebuf = 0
        end_of_video = False
        delay = 0
        video_size = 0
        wasted_bytes = 0

        if sleep_time > 0:
            delay = sleep_time
            play_timeline, buffer, wasted = self.play_videos(sleep_time)
            # Return the end flag for the current playing video
            end_of_video = (self.players[self.play_video_id-self.start_video_id].get_remain_video_num() == 0)
        else:
            video_size = self.players[download_video_id-self.start_video_id].get_video_size(bitrate)
            self.players[download_video_id - self.start_video_id].record_download_bitrate(bitrate)
            delay = self.network.network_simu(video_size)  # ms
            # play_timeline, buffer = self.players[self.play_video_id - self.start_video_id].video_play(delay)
            play_timeline, buffer, wasted = self.play_videos(delay)
            if download_video_id < self.start_video_id:
                # If the video has already been ended, we only accumulate the wastage
                print("Extra chunk downloaded for Video ", download_video_id,
                      " which the user already finished watching.\n")
                wasted += video_size  # Since its already fluently played, the download must be redundant
                self.total_downloaded_len += VIDEO_CHUNCK_LEN  # sum up the total downloaded time
                end_of_video = True
            else:
                end_of_video = self.players[download_video_id-self.start_video_id].video_download(VIDEO_CHUNCK_LEN)

        # Sum up the bandwidth wastage
        wasted_bytes += wasted
        if buffer < 0:
            rebuf = abs(buffer)

        return delay, rebuf, video_size, end_of_video, self.play_video_id, wasted_bytes
