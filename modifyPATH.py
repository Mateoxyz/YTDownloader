import os, sys

def TemporalPath():
    """
    Temporarily changes the system PATH to include the ffmpeg directory.
    Returns the original PATH value for later restoration.
    """
    
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))

    
    tempDir = os.path.join(current_dir, "ffmpeg", "bin")
    
    
    original_path = os.environ.get("PATH", "")
    
    
    os.environ["PATH"] = f"{tempDir}{os.pathsep}{original_path}"
    return original_path


def RestorePath(original_path):
    """
    Restore the PATH
    """
    if original_path:
        os.environ["PATH"] = original_path