#!/usr/bin/env python3
import subprocess
import os
import json
from pathlib import Path
from tqdm import tqdm

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'  # Reset color

#check user input
def check_path_type(user_input):
    """
    Check if the user input is a file, folder, or does not exist.
    """
    if os.path.exists(user_input):
        if os.path.isfile(user_input):
            return "File"
        elif os.path.isdir(user_input):
            return "Folder"
    return "Path does not exist"

#check the file using ffprobe
def ffprobe_check(fcheck):
    """
    Check if a file is using E-AC3 audio codec using ffprobe.
    Return False if it's using any other audio codec.
    """
    ffprobe_command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream=codec_name',
        '-of', 'json',
        fcheck
    ]

    try:
        # Run ffprobe command and capture the output
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)

        # Parse JSON output
        ffprobe_output = json.loads(result.stdout)

        # Check if any stream is using E-AC3 codec
        for stream in ffprobe_output.get('streams', []):
            codec_name = stream.get('codec_name', '').lower()
            if codec_name == 'eac3':
                print(f"{Colors.RED} {fcheck} is already using E-AC3 audio and doesn't need to be connverted for use on roku {Colors.END}")
                return "no_conversion_required"  # E-AC3 codec found

        # E-AC3 codec not found
        print(f"{Colors.GREEN} {fcheck} needs to be converted to E-AC3 audio for use on roku {Colors.END}")
        return "conversion_required"

    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        return "error"

def convert(input_file):
    """
    Convert the input file, keeping the video codec unchanged and changing the audio codec to E-AC3.
    """
    input_path = Path(input_file)
    
    # Ensure the input file exists before proceeding
    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found.")
        return

    #put the file back in the same folder you go it from
    output_file = input_path.with_name(f"{input_path.stem}_EAC3{input_path.suffix}")
    
    ffmpeg_command = [
        'ffmpeg',
        '-i', str(input_path),
        '-c:v', 'copy',  # Copy video codec
        '-c:a', 'eac3',  # Convert audio codec to E-AC3
        str(output_file),
        # '-progress', 'pipe:1'  # Output progress information to stdout
    ]

    try:
        # Start ffmpeg process with subprocess
        process = subprocess.Popen(ffmpeg_command, text=True, universal_newlines=True)

        # Display a progress bar
        print("Converting")
        # with tqdm(total=100, unit="%", dynamic_ncols=True) as pbar:
        #     for line in process.stdout:
        #         if "out_time" in line:
        #             progress_info = line.strip().split('=')
        #             progress_percentage = int(float(progress_info[1]) * 100)
        #             pbar.update(progress_percentage - pbar.n)

        process.wait()  # Wait for the process to finish
        print(f"\nConversion of '{input_path.stem}' successful.")

    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")

def process_files_in_directory(directory):
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']

    for folder_path, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            _, file_extension = os.path.splitext(file_name)

            #before probe check if it's a sample file
            if "sample" in file_name.lower():
                print(f"{Colors.RED} Skipping '{file_name}' as it contains the word 'sample'. {Colors.END}")
                continue
            if file_extension not in video_extensions:
                print(f"{Colors.RED} Skipping '{file_name}' it's not a valid video file {video_extensions} {Colors.END}.")
                continue

            result = ffprobe_check(file_path)
            if result == "conversion_required":
                convert(file_path)

############## Program start ###############
# Get user input
user_input = input("Enter a file or folder path: ")

# Check and print the type of the path
path_type = check_path_type(user_input)

#Depending on file or folder either do once or do in a loop
# if path_type == "File":
#     print(f"The input '{user_input}' is a file.")
#     ffprobe_check(user_input)
# elif path_type == "Folder":
#     print(f"The input '{user_input}' is a folder. Let's check each item in the folder")    
#     process_files_in_directory(user_input)

# else:
#     print(f"The input '{user_input}' does not exist.")

# print("SCRIPT IS NOW COMPLETE")

print(f"{user_input}")
#to scary lets find another way to do this.
# #clean up old files
output_file = f"{user_input}/find_output.txt"
print(f"{output_file}")
# Command to find files and write the output to a file
command1 = f"find '{user_input}' -type f ! -name '*EAC3*' ! -name '*.srt' > '{output_file}'"
command2 = f"find '{user_input}' -type f ! -name '*EAC3*' ! -name '*.srt' ! -name '*.txt' -execdir rm {{}} +"
print(f"{command1}")
print(f"{command2}")
# Execute the command
subprocess.run(command1, shell=True)
subprocess.run(command2, shell=True)

