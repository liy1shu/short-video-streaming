# Comparison Algorithm: No saving approach
# No saving algorithm downloads videos in recommendation queue one by one.
# It stops when all downloads end.

HIGHEST_BITRATE = 5
TAU = 500.0  # ms
RECOMMEND_QUEUE = 5  

class Algorithm:
    def __init__(self):
        # fill your self params
        pass

    # Intial
    def Initialize(self):
        # Initialize your session or something
        pass

    # Define your algorithm
    def run(self, delay, rebuf, video_size, end_of_video, play_video_id, Players, first_step=False):
        download_video_id = -1
        # check whether videos in RECOMMEND_QUEUE have been downloaded one by one
        for i in range(RECOMMEND_QUEUE):
            if Players[i].get_remain_video_num() != 0:      # downloading hasn't finished yet 
                download_video_id = play_video_id + i
                break

        if download_video_id == -1:  # no need to download, sleep for TAU time
            sleep_time = TAU
            bit_rate = 0
            download_video_id = play_video_id  # the value of bit_rate and download_video_id doesn't matter
        else:
            bit_rate = HIGHEST_BITRATE  # download the video at the highest bitrate
            sleep_time = 0.0

        return download_video_id, bit_rate, sleep_time