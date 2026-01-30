from ast import main
from calendar import c
import subprocess
import os
import json
from docarray import DocList, BaseDoc
from jina import Client
import multiprocessing
import shutil

# Global configuration variable
CONFIG = {}

def load_config():
    """Load configuration file"""
    global CONFIG
    config_path = os.path.join(os.path.dirname(__file__), "lip-sync.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        print("Configuration file loaded successfully")
        return True
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"Configuration file format error: {e}")
        return False
    except Exception as e:
        print(f"Error occurred while loading configuration file: {e}")
        return False

def get_config_value(key_path, default=None):
    """Get configuration value, supports nested keys"""
    keys = key_path.split('.')
    value = CONFIG
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

# Initialize configuration
load_config()

# Use paths from configuration file, use default values if loading fails
WORKING_DIRECTORY = get_config_value("paths.working_directory", "/workspace/share/yuntao/LiveTalking")
WORKSPACE = os.path.join(WORKING_DIRECTORY, "burr")
PORT = get_config_value("servers.jina_port", 23002)
LIVEAVADIR = os.path.join(WORKING_DIRECTORY, "data", "avatars")
MUSE_TALK_BASE = get_config_value("paths.muse_talk_base", "/workspace/share/yuntao/MuseTalk")
MUSERESDIR = os.path.join(MUSE_TALK_BASE, "results", "v15", "avatars")
LIVEVIDEODIR = os.path.join(WORKING_DIRECTORY, "data", "video")

# Ensure necessary directories exist
os.makedirs(LIVEVIDEODIR, exist_ok=True)
os.makedirs(LIVEAVADIR, exist_ok=True)
os.makedirs(WORKSPACE, exist_ok=True)

class VideoBGTask(BaseDoc):
    input_video_path: str                  # Required: relative to WORKSPACE
    output_video_path: str   # Result file, relative to WORKSPACE
    blur_background: bool = False          # Choose one of two options
    background_image: str = ""             # Choose one of two options: relative to WORKSPACE
    blur_kernel: int = 101  # Gaussian kernel (odd number)
    resize: int = 192            # PPHumanSeg input size


class Result(BaseDoc):
    result: str  # 'success' / 'error'
    info: str    # Output file path / error message




def convert_video_to_25fps(input_path):
    """
    Convert video to 25fps and modify in place
    
    Args:
        input_path (str): input video file path
    
    Returns:
        bool: whether conversion is successful
    """ 
    temp_path = None
    try:
        # Create temporary file path
        temp_path = os.path.join(LIVEVIDEODIR, "temp.mp4")

        # Use ffmpeg to convert video to 25fps
        cmd = [
            get_config_value("paths.ffmpeg_path", '/usr/bin/ffmpeg'),
            '-i', input_path,
            '-r', "25",  # Set frame rate
            '-b:v', get_config_value("video_processing.bitrate", '3000k'),  # Set video bitrate
            '-c:v', get_config_value("video_processing.codec", 'libx264'),  # Video encoder
            '-y',  # Overwrite output file
            temp_path
        ]

        # Execute command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if successful
        if result.returncode == 0:
            print(f"Video conversion successful, temp file: {temp_path}")
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error converting video: {str(e)}")
        return False
    finally:
        # Do not delete temp file regardless of success or failure, used by subsequent functions
        pass
        

def burr_video(input_path):
    """
    Function to blur video
    
    Args:
        input_path (str): input video file path
    
    Returns:
        bool: whether blur processing is successful
    """
    try:
        # Copy input video to workspace
        output_path = os.path.join(WORKSPACE, "burr_input.mp4")
        subprocess.run(["cp", input_path, output_path], check=True)
        print(f"Copied video file to workspace: {input_path} -> {output_path}")
        cli = Client(port=PORT)
        req = VideoBGTask(
            input_video_path="burr_input.mp4",
            output_video_path="burr_output.mp4",
            blur_background=True,
        )
        resp = cli.post(
            on="/",
            inputs=DocList[VideoBGTask]([req]),
            return_type=DocList[Result],
        )
        print(resp[0].result, resp[0].info)
        # Check processing result
        if resp[0].result == "success":
            # Overwrite input video with output
            burr_output_path = os.path.join(WORKSPACE, "burr_output.mp4")
            subprocess.run(["cp", burr_output_path, input_path], check=True)
            print(f"Blur processing successful, original file overwritten: {input_path}")
            return True
        else:
            print(f"Blur processing failed: {resp[0].info}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"File operation failed: {e}")
        return False
    except Exception as e:
        print(f"Error occurred during blur processing: {e}")
        return False
    finally:
        # Clean up temporary files in workspace
        temp_input = os.path.join(WORKSPACE, "burr_input.mp4")
        temp_output = os.path.join(WORKSPACE, "burr_output.mp4")
        for temp_file in [temp_input, temp_output]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Deleted temporary file: {temp_file}")
                except Exception as e:
                    print(f"Failed to delete temporary file {temp_file}: {e}")
        

def start_avatar_creation_script(video_path):
    """
    Function to start avatar creation script
    Args:
        video_path (str): input video file path
    
    Returns:
        bool: whether script started successfully
    """
    import subprocess
    # 1. Copy video file to target path
    target_path = os.path.join(MUSE_TALK_BASE, "data", "video", "yongen.mp4")
    try:
        subprocess.run(["cp", video_path, target_path], check=True)
        print(f"Copied video file: {video_path} -> {target_path}")
    except Exception as e:
        print(f"Failed to copy video file: {e}")
        return False
    # Delete existing avator_1 folder
    avatars_dir = os.path.join(MUSE_TALK_BASE, "results", "v15", "avatars", "avator_1")
    if os.path.exists(avatars_dir):
        try:
            shutil.rmtree(avatars_dir)
            print(f"Deleted existing avatar folder: {avatars_dir}")
        except Exception as e:
            print(f"Failed to delete avatar folder: {e}")
            return False
    # 2. Run script using specified conda environment
    conda_init = get_config_value("paths.conda_init", "/home/xinghua/workspace/share/conda/etc/profile.d/conda.sh")
    conda_env = get_config_value("paths.muse_conda_env", "/workspace/share/yuntao/MuseTalk/home/chengxin/workspace/chengxin/conda/envs/MuseTalk")
    script_path = os.path.join(MUSE_TALK_BASE, "inference.sh")
    muse_talk_dir = MUSE_TALK_BASE
    print("Starting script execution...")
    try:
        # Build command to use specified conda environment
        command = [
            "bash", "-c",
            f"source {conda_init} && conda activate {conda_env} && cd {muse_talk_dir} && bash {script_path} v1.5 realtime"
        ]
        # Execute script in specified environment, display output in real time
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        # Print output to console in real time
        for line in process.stdout:
            print(line.rstrip())  # Remove extra newline
        # Wait for process to finish
        process.wait()
        if process.returncode == 0:
            print("Script executed successfully")
            return True
        else:
            print(f"Script execution failed, return code: {process.returncode}")
            return False
    except Exception as e:
        print(f"Error occurred while executing script: {e}")
        return False

def move_avatar_files(source_dir, destination_dir, avatar_name):
    """
    Function to move avatar files
    
    Args:
        source_dir (str): source directory path
        destination_dir (str): destination directory path
        avatar_name (str): avatar name
    
    Returns:
        bool: whether files moved successfully
    """
    
    try:
        # Build source folder path
        source_avatar_dir = os.path.join(source_dir, "avator_1")
        
        # Check if source folder exists
        if not os.path.exists(source_avatar_dir):
            print(f"Source folder does not exist: {source_avatar_dir}")
            return False
        
        # Ensure destination directory exists
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir, exist_ok=True)
            print(f"Created destination directory: {destination_dir}")
        
        # Build target folder path
        target_avatar_dir = os.path.join(destination_dir, avatar_name)
        
        # If target folder exists, delete it first
        if os.path.exists(target_avatar_dir):
            shutil.rmtree(target_avatar_dir)
            print(f"Deleted existing target folder: {target_avatar_dir}")
        
        # Move and rename folder
        shutil.move(source_avatar_dir, target_avatar_dir)
        print(f"Successfully moved folder: {source_avatar_dir} -> {target_avatar_dir}")
        
        # Update avator_info.json with correct avatar_id and video_path
        avator_info_path = os.path.join(target_avatar_dir, "avator_info.json")
        if os.path.exists(avator_info_path):
            try:
                import json
                with open(avator_info_path, 'r') as f:
                    avator_info = json.load(f)
                
                # Update avatar_id and video_path
                avator_info['avatar_id'] = avatar_name
                avator_info['video_path'] = f"data/video/{avatar_name}.mp4"
                
                with open(avator_info_path, 'w') as f:
                    json.dump(avator_info, f)
                
                print(f"Updated avator_info.json: avatar_id={avatar_name}")
            except Exception as e:
                print(f"Warning: Failed to update avator_info.json: {e}")
        
        return True
        
    except Exception as e:
        print(f"Failed to move folder: {e}")
        return False

def get_avatar_image(avatar_name):
    """
    Read image file of specified avatar
    
    Args:
        avatar_name (str): avatar name
    
    Returns:
        bytes or None: image file bytes data, returns None if file does not exist
    """
    import os
    
    try:
        # Build image file path
        image_path = os.path.join(LIVEAVADIR, avatar_name, "full_imgs", "00000000.png")
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Image file does not exist: {image_path}")
            return None
    
        
        print(f"Successfully read image file path: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"Failed to read image file: {e}")
        return None
        

def create_avatar(video_path, avatar_name, burr=False):
    """
    Main function to create avatar
    
    Args:
        video_path (str): input video file path
        avatar_name (str): avatar name
        burr (bool): whether to apply blur processing
    
    Returns:
        str or False: image file path if successful, False if failed
    """
    # Check and create data/video folder
    video_dir = LIVEVIDEODIR
    if not os.path.exists(video_dir):
        try:
            os.makedirs(video_dir, exist_ok=True)
            print(f"Created video directory: {video_dir}")
        except Exception as e:
            print(f"Failed to create video directory: {e}")
            return False
    
    temp_video_path = os.path.join(video_dir, "temp.mp4")
    
    try:
        # 1. Convert video frame rate to 25fps
        print("Starting video frame rate conversion...")
        if not convert_video_to_25fps(video_path):
            print("Video frame rate conversion failed")
            return False
        print("Video frame rate conversion successful")
        
        # Use temporary file from here
        current_video_path = temp_video_path
        
        # 2. Optional blur processing
        if burr == True:
            print("Starting blur processing...")
            burr_result = burr_video(current_video_path)
            if not burr_result:
                print("Blur processing failed")
                return False
            print("Blur processing successful")
        
        # 3. Start avatar creation script
        print("Starting avatar creation...")
        if not start_avatar_creation_script(current_video_path):
            print("Avatar creation script execution failed")
            return False
        print("Avatar creation script execution successful")
        
        # 4. Move avatar files
        print("Starting avatar file movement...")
        if not move_avatar_files(MUSERESDIR, LIVEAVADIR, avatar_name):
            print("Avatar file movement failed")
            return False
        print("Avatar file movement successful")
        
        # 5. Get avatar image
        print("Starting avatar image retrieval...")
        image_path = get_avatar_image(avatar_name)
        if image_path is None:
            print("Failed to retrieve avatar image")
            return False
        
        print(f"Avatar creation completed, image path: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"Error occurred during avatar creation: {e}")
        return False
    finally:
        # Delete temporary file
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                print(f"Deleted temporary file: {temp_video_path}")
            except Exception as e:
                print(f"Failed to delete temporary file: {e}")



if __name__ == "__main__":
    # Use paths from configuration file for testing
    video_dir = LIVEVIDEODIR
    
    #convert_video_to_25fps(os.path.join(video_dir, "fps_30.mp4"))
    #burr_video(os.path.join(video_dir, "burr_test.mp4"))
    #start_avatar_creation_script(os.path.join(video_dir, "burr_test.mp4"))
    #move_avatar_files(MUSERESDIR, LIVEAVADIR, "avatar_3")
    create_avatar(os.path.join(video_dir, "burr_test.mp4"), "avatar_3", burr=True)
    pass
