# ACM Multimedia 2022 Grand Challenge: Short Video Streaming
This repository contains the simulator code used for ACM Multimedia 2022 Short Video Streaming.  The simulator is a short video streaming simulator with a pluggable client module for participant defined download control algorithms.

# File Structures
#### 0. Data

The data files are placed under `/data`:

- /short_video_size：the video size of each chunk (1000 ms)

  For example, a video of 3 chunks( 3s ) can be described as follows:

  ```
  181801
  155580
  139857
  ```

- /network_traces：the network condition (pesented in (time, bandwidth) groups)

  For example, the following data means the bandwidth from 0.0 to 0.5499999 (s) is 4.03768755221, other rows can be translated likewise.

  ```
  0.0	4.03768755221
  0.549999952316	4.79283060109
  0.879999876022	4.49231799163
  ```

- /user_ret：describes a user retention model of each video

  For example, a video of 4 seconds can take the following form: 

  ```
  0	1
  1	0.929794029
  2	0.832466432
  3	0.729774475
  4 0
  ```

  It means that 92.98% of users are still watching when the clock tick 1 second, 83.24% of users are still watching at 2sec. 

  The leave ratio can be deducted from subtracting one retention rate with its former retention rate. For instance, (92.97 - 83.24) % = 9.73% of users leave within the 1s-2s period.

#### 1. Simulator

The simulator files are placed under `/simulator`:

- controller.py

  `controller.py` contains the main module your algorithm will interact with. It imports the datasets, creates the test environment, and simulates the whole process of your decision step.

- network_module.py

  `network_module` holds a class that can save and operate with network conditions.

- short_video_load_trace.py

  `short_video_load_trace.py` mainly provides an interface for loading datasets.

- user_module.py

  `user_module.py` maintains a class of user model and simulate user actions.

- **video_player.py**

  `video_player.py` is the video player modules which handles most of your actions for each video, including downloading and watching. 

  We strongly recommend you reading this file cause you will be receiving an instance of this class as a feedback from our simulator for each of your decisions.

#### 2. Evaluating program

You can evaluate your program with our simulator by simply running the `run.py` under the root directory.

##### The args:

- `--baseline`, `--user`：choose the algorithm you are evaluating
- `--trace`: (optional) choose the trace_id you are evaluating (currently fixed to zero, will change if we add dataset)

1）Run a baseline algorithm

We have two baseline algorithms, fix_preload and no_preload, which you can refer to the content introduction for details. 

You can run these baselines to get a basic idea of our simulator and how you can interact with it.

```bash
python run.py --baseline fixed_preload
python run.py --baseline no_preload
```

2）Run your own algorithm

You should input your relative code directory path to `run.py` as argument `--user`

```bash
python run.py --user <Your relative code directory path>
```

For example, if you place your file under the `submit` dir under the root directory:

```bash
# Your file structure:
# run.py
# submit
#   |_solution.py
python run.py --user ./submit/
```

##### The outputs:

You will get direct output on the screen apart from the log files. The output will include:

- The user actions:  when they stopped watching a video, we output the watch duration time and the downloaded time length.
- The final results: 
  - QoE
  - Bandwidth wastage
  - Downloaded/watched time ratio

#### 3. Log files

The log files are placed under `/logs`:

- `/logs/sample_user/user.txt`：The generated user watch durations for each video. 

- `/logs/log.txt`：The logs of your algorithm. It will output all steps of your decisions including:

  - *Which* chunk of the *which* video you choose to download?

  - Meanwhile, *which* chunk of video the user is playing? 

  Also, log file will include the influence of QoE from your decision:
  
  - The change of video qualities within a single video
  - The rebuffering time if you have caused a rebuffer
