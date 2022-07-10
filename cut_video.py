import os
import json
import codecs
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed

# json文件目录
json_dir = './benchmarks/slowfast/kinetics/0-170001.json'
# 视频目录
video_dir = './down_videos/dummy_videos'
# 视频剪辑目录
save_dir = './down_videos/cut_videos_170000'

os.makedirs(save_dir, exist_ok=True)


class VideoClip:

    def get_json_files(self):
        """
        获取json文件
        """
        self.json_files = []
        for root, dirs, files in os.walk(json_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.json':
                    self.json_files.append(os.path.join(root, file))

    def get_video_files(self):
        """
        获取视频文件
        """
        self.video_files = {}
        for root, dirs, files in os.walk(video_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.mp4':
                    vid = file.split('.')[0]
                    self.video_files[vid] = os.path.join(root, file)

    def second_to_time(self, second):
        """
        秒转换为时间
        """
        hour = int(second/3600)
        minute = int((second-hour*3600)/60)
        second = int(second-hour*3600-minute*60)
        hour = f'0{hour}' if hour < 10 else hour
        minute = f'0{minute}' if minute < 10 else minute
        second = f'0{second}' if second < 10 else second
        return str(hour)+':'+str(minute)+':'+str(second)

    def calc_time_diff(self, from_second, to_second):
        """
        计算时间差
        """
        return round(to_second-from_second, 2)

    def clip_video(self, video_path, from_second, to_second, save_path):
        """
        剪辑视频
        """
        video_path = video_path.replace('\\', '/')
        save_path = save_path.replace('\\', '/')
        from_time = self.second_to_time(from_second)
        time_diff = self.calc_time_diff(from_second, to_second)
        duration = self.second_to_time(time_diff)
        # 剪辑命令
        cmd = f"""
ffmpeg -y -ss {from_time} -t {duration} -i "{video_path}" -c:v libx264 -preset superfast -c:a copy "{save_path}" -loglevel error
"""
        # 不显示日志

        print(cmd)
        os.system(cmd)

    def check_chardet(self, file_path):
        """
        检查文件编码
        """
        with open(file_path, 'rb') as f:
            data = f.read()
            result = chardet.detect(data)
            encoding = result['encoding']
            return encoding

    def handle_json(self, json_file):
        """
        处理一个json文件
        """
        encoding = self.check_chardet(json_file)
        with codecs.open(json_file, 'r', encoding=encoding) as f:
            data = json.load(f)
            for vid in data:
                clips = data[vid]['annotations']
                total_clips = len(clips)
                # 只有一个片段
                if total_clips == 1:
                    clip = clips[0]
                    fromto = clip['segment']
                    from_second, to_second = fromto
                    save_path = os.path.join(save_dir, vid+'.mp4')
                    video_path = self.video_files.get(vid)
                    if video_path:
                        self.clip_video(video_path, from_second,
                                        to_second, save_path)
                # 多个片段
                else:
                    for idx, clip in enumerate(clips):
                        fromto = clip['segment']
                        from_second, to_second = fromto
                        save_path = os.path.join(
                            save_dir, f'{vid}_{idx+1}.mp4')
                        video_path = self.video_files.get(vid)
                        if video_path:
                            self.clip_video(
                                video_path, from_second, to_second, save_path)

    def main(self):
        """
        主程序
        """
        self.get_json_files()
        self.get_video_files()
        tasks = []
        with ThreadPoolExecutor(max_workers=10) as t:
            for json_file in self.json_files:
                tasks.append(t.submit(self.handle_json, json_file))
            for task in as_completed(tasks):
                pass


if __name__ == '__main__':
    VideoClip().main()
