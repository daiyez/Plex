#!/usr/bin/env python3
import imageio
import subprocess
import os
import json

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
                print(f"{fcheck} is already using E-AC3 audio and doesn't need to be connverted for use on roku ")
                return conversion_required  # E-AC3 codec found

        # E-AC3 codec not found
        print(f"{fcheck} needs to be converted to E-AC3 audio for use on roku")
        return no_conversion_required

    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        return False

def convert(input_file):
    """
    Convert the input file, keeping the video codec unchanged and changing the audio codec to E-AC3.
    """
    output_file = f"{input_file.stem}_EAC3{input_file.suffix}"

    ffmpeg_command = [
        'ffmpeg',
        '-i', str(input_file),
        '-c:v', 'copy',  # Copy video codec
        '-c:a', 'eac3',  # Convert audio codec to E-AC3
        str(output_file)
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Conversion successful. Output file: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")

def find_bottom(root_folder, target_extension):
    """
    Search for a file with the specified extension within the specified root folder and its subdirectories.
    Return the full path if found, otherwise return None.
    """
    for folder, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(target_extension.lower()):
                return os.path.join(folder, file)
    return None


# Get user input
user_input = input("Enter a file or folder path: ")

# Check and print the type of the path
path_type = check_path_type(user_input)

#Depending on file or folder either do once or do in a loop
if path_type == "File":
    print(f"The input '{user_input}' is a file.")
    ffprobe_check(user_input)
elif path_type == "Folder":
    print(f"The input '{user_input}' is a folder. Let's check each item in the folder")
    
    files_in_folder = [f for f in os.listdir(user_input) if os.path.isfile(os.path.join(user_input, f))]
    for file_name in files_in_folder:
	    file_path = os.path.join(user_input, file_name)
	    result = ffprobe_check(file_path)
	    if result == "conversion_required":
	    	convert(file_path)

else:
    print(f"The input '{user_input}' does not exist.")

