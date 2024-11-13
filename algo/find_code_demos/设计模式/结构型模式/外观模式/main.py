'''
Date: 2024-08-27 12:01:22
LastEditors: 牛智超
LastEditTime: 2024-08-27 12:02:01
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\外观模式\main.py
'''
# 子系统类
class AudioPlayer:
    def play(self, audio_file):
        print(f"Playing audio file: {audio_file}")

    def stop(self):
        print("Stopping audio playback.")


class AudioEffects:
    def apply_reverb(self):
        print("Applying reverb effect.")

    def apply_echo(self):
        print("Applying echo effect.")


class PlaylistManager:
    def load_playlist(self, playlist_name):
        print(f"Loading playlist: {playlist_name}")

    def save_playlist(self, playlist_name):
        print(f"Saving playlist: {playlist_name}")
        
# 外观类
class MusicPlayerFacade:
    def __init__(self):
        self.audio_player = AudioPlayer()
        self.audio_effects = AudioEffects()
        self.playlist_manager = PlaylistManager()

    def play_music_with_effects(self, audio_file, playlist_name):
        self.playlist_manager.load_playlist(playlist_name)
        self.audio_player.play(audio_file)
        self.audio_effects.apply_reverb()
        self.audio_effects.apply_echo()
        self.audio_player.stop()
        
# 使用外观模式
def main():
    music_player = MusicPlayerFacade()
    music_player.play_music_with_effects("song.mp3", "My Favorite Songs")

if __name__ == "__main__":
    main()