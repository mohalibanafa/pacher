import lzma
import bz2
import struct
import os
import io

def bspatch(old_data, patch_data):
    """
    Pure Python implementation of bspatch.
    Based on the algorithm by Colin Percival.
    """
    if len(patch_data) < 32:
        raise ValueError("Patch file too short")
        
    header = patch_data[:32]
    if header[:8] != b'BSDIFF40':
        raise ValueError("Invalid patch header")
        
    ctrl_len = struct.unpack('<Q', header[8:16])[0]
    diff_len = struct.unpack('<Q', header[16:24])[0]
    new_size = struct.unpack('<Q', header[24:32])[0]
    
    ctrl_block = bz2.decompress(patch_data[32 : 32 + ctrl_len])
    diff_block = bz2.decompress(patch_data[32 + ctrl_len : 32 + ctrl_len + diff_len])
    extra_block = bz2.decompress(patch_data[32 + ctrl_len + diff_len :])
    
    new_data = bytearray(new_size)
    old_pos = 0
    new_pos = 0
    diff_pos = 0
    extra_pos = 0
    
    for i in range(0, len(ctrl_block), 24):
        add_len = struct.unpack('<Q', ctrl_block[i : i+8])[0]
        copy_len = struct.unpack('<Q', ctrl_block[i+8 : i+16])[0]
        seek_len = struct.unpack('<q', ctrl_block[i+16 : i+24])[0]
        
        # Add section
        if new_pos + add_len > new_size:
            raise ValueError("Corrupt patch (add)")
            
        for j in range(add_len):
            val = diff_block[diff_pos + j]
            if 0 <= old_pos + j < len(old_data):
                val = (val + old_data[old_pos + j]) % 256
            new_data[new_pos + j] = val
            
        new_pos += add_len
        old_pos += add_len
        diff_pos += add_len
        
        # Copy section
        if new_pos + copy_len > new_size:
            raise ValueError("Corrupt patch (copy)")
            
        new_data[new_pos : new_pos + copy_len] = extra_block[extra_pos : extra_pos + copy_len]
        
        new_pos += copy_len
        extra_pos += copy_len
        old_pos += seek_len
        
    return bytes(new_data)

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
    
    # 1. Read original file
    with open(original_path, 'rb') as f:
        old_data = f.read()
        
    # 2. Decompress .xz patch file to get the bsdiff patch
    with lzma.open(patch_path, "rb") as f:
        patch_data = f.read()
        
    # 3. Apply bspatch
    new_data = bspatch(old_data, patch_data)
    
    # 4. Save result
    with open(output_file, 'wb') as f:
        f.write(new_data)
        
    return output_file
