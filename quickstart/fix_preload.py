# This example aims at helping you to learn what parameters you need to decide in your algorithm.
# It only gives you basic ideas about the structure of your algorithm, you need to find a better solution to balance QoE and bandwidth waste.
# You can run this example and get results by command: python run.py --quickstart fix_preload

# Description of fixed-preload algorithm
# Fixed-preload algorithm downloads the current playing video first.
# When the current playing video download ends, it preloads the videos in the recommendation queue in order.
# The maximum of preloading size is 800KB for each video.
# It stops when all downloads end.

# We fix bitrate in this example.
FIXED_BITRATE = 1
# If there is no need to download, sleep for TAU time.
TAU = 500.0  # ms
# max length of recommend_queue
RECOMMEND_QUEUE = 5
# maximum of preloading size
PROLOAD_SIZE = 800000.0   # B

class Algorithm:
    def __init__(self):
        # fill the self params
        pass

    def Initialize(self):
        # Initialize the session or something
        pass

    # Define the algorithm here.
    # The args you can get are as follows:
    # 1. delay: the time cost of your last operation
    # 2. rebuf: the length of rebufferment
    # 3. video_size: the size of the last downloaded chunk
    # 4. end_of_video: if the last video was ended
    # 5. play_video_id: the id of the current video
    # 6. Players: the video data of a RECOMMEND QUEUE of 5 (see specific definitions in readme)
    # 7. first_step: is this your first step?
    def run(self, delay, rebuf, video_size, end_of_video, play_video_id, Players, first_step=False):
        download_video_id = -1
        
        # If it is the first step, delay & rebuf & video_size & end_of_video means nothing.
        # So we return specific download_video_id & bit_rate & sleep_time.
        if first_step:
            self.sleep_time = 0
            return 0, 5, self.sleep_time
        
        # decide download video id
        download_video_id = -1
        if Players[0].get_remain_video_num() != 0:  # downloading of the current playing video hasn't finished yet 
            download_video_id = play_video_id
        else:
            # preload videos in RECOMMEND_QUEUE one by one
            for seq in range(1, min(len(Players), RECOMMEND_QUEUE)):
                if Players[seq].get_preload_size() < (PROLOAD_SIZE) and Players[seq].get_remain_video_num() != 0:      # preloading hasn't finished yet 
                    start_chunk = int(Players[seq].get_play_chunk())
                    cond_p = Players[seq].user_ret.conditional_p(start_chunk, interval)
                    if cond_p 
                    download_video_id = play_video_id + seq
                    break

        if download_video_id == -1:  # no need to download, sleep for TAU time
            sleep_time = TAU
            bit_rate = 0
            download_video_id = play_video_id  # the value of bit_rate and download_video_id doesn't matter
        else:

            
            bit_rate = FIXED_BITRATE  # download the video at the highest bitrate
            sleep_time = 0.0

        return download_video_id, bit_rate, sleep_time

