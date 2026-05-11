import os
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'my_playlist.txt')

def write_liked_songs_to_file(liked_songs, file_name):
    file = open('my_playlist.txt', 'w')
    file.write("Liked Songs:\n")
    for k,v in liked_songs.items():
        file.writelines(f'{k} by {v}\n')

liked_songs = {
    'Bad Habits': 'Ed Sheeran',
    "I'm Just Ken": "Ryan Gosling",
    'Mastermind': 'Taylor Swift',
    'Uptown Funk': 'Mark Ronson ft. Bruno Mars',
    'Ghost': 'Justin Bieber'
}

write_liked_songs_to_file(liked_songs, file_path)

