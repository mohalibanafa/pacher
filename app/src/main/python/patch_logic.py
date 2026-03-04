import bsdiff4
import lzma
import tempfile
import shutil
import os

def apply_patch(original_path, patch_path, output_dir):
    """
    Applies an LZMA-compressed bsdiff patch to an original file.
    Args:
        original_path (str): Path to the original file.
        patch_path (str): Path to the compressed patch (.xz).
        output_dir (str): Directory where the patched file will be saved.
    Returns:
        str: Path to the newly patched file.
    """
    output_file = os.path.join(output_dir, "patched_file_final.bin")
    
    # Extract patch temporarily
    fd, temp_patch_path = tempfile.mkstemp()
    try:
        # Decompress .xz patch file
        with lzma.open(patch_path, "rb") as f_in, os.fdopen(fd, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
            
        # Apply patch
        bsdiff4.file_patch(original_path, output_file, temp_patch_path)
    finally:
        # Cleanup temp file
        if os.path.exists(temp_patch_path):
            os.remove(temp_patch_path)
            
    return output_file
