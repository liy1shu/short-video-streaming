# test code
import short_video_load_trace
import controller as env
import numpy as np
import random
from random import choice

def main():
    sample_user_video_num = 9    # random video nums
    all_cooked_time, all_cooked_bw = short_video_load_trace.load_trace()

    net_env = env.Environment(all_cooked_time=all_cooked_time[0],
                              all_cooked_bw=all_cooked_bw[0])
    
    download_video_id = 0
    bit_rate = 0
    sleep_time = 0
    prop = [0.7, 0.3]
    
    while True:
        sleep_time = np.random.choice([0, 2000], p=prop) 
        if sleep_time == 0:
            download_set = net_env.get_download_permit()
            download_video_id = choice(list(download_set))
            print('download_video_id: %d' % download_video_id)
            
            bit_rate = random.randint(0,5)
            
        print("*****************")
        print('downlad video ID: %2d' % download_video_id)
        print('bitrate download: %2d' % bit_rate)
        print('sleep time: %f' % sleep_time)
        
        delay, buffer_size, rebuf, video_size, end_of_video, \
        video_chunk_remain, play_video_id = net_env.buffer_management(download_video_id, bit_rate, sleep_time)
        
        if end_of_video:
            net_env.remove_download_over_video(download_video_id)
            print("Video %d download over and removed from set" % download_video_id)
        
        if play_video_id > sample_user_video_num or download_video_id > sample_user_video_num:
            break


if __name__ == '__main__':
    main()
    
    