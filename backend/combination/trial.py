import moviepy as mp
# assets\Campaign_Mock_01A\3875283-hd_1920_1080_25fps.mp4
clip = mp.VideoFileClip("assets/Campaign_Mock_01A/3875283-hd_1920_1080_25fps.mp4")
clip_resized = clip.resized(height=360) # make the height 360px ( According to moviePy documenation The width is then computed so that the width/height ratio is conserved.)
clip_resized.write_videofile("movie_resized.mp4")
