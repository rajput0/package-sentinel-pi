import vlc

alarm = vlc.MediaPlayer()
media = vlc.Media("alarm-sound.mp3")
alarm.set_media(media)
alarm.audio_set_volume(0)
alarm.play()
alarm.set_pause(1)

while True:
      
    print("Press 'p' to pause, 'r' to resume")
    print("Press 'e' to exit the program")
    query = input("  ")
      
    if query == 'p':
        print("Start Playing")
        # Pausing the music
        alarm.audio_set_volume(200)
        alarm.play()    
    