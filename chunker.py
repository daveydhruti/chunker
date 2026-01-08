#!/usr/bin/env python3
"""
File Chunker - Split large files into chunks and rebuild them
Usage:
    python chunker.py split <file> [chunk_size_mb]
    python chunker.py join <folder_name>
"""
# Script enhanced using claude AI

import os
import sys
import hashlib


def get_file_hash(filepath):
    """Calculate SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def split_file(filepath, chunk_size_mb=50):
    """Split a file into chunks"""
    chunk_size = chunk_size_mb * 1024 * 1024  # Convert MB to bytes
    
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found")
        return
    
    file_size = os.path.getsize(filepath)
    base_name = os.path.basename(filepath)
    
    # Create folder named after the file
    folder_name = base_name + "_chunks"
    os.makedirs(folder_name, exist_ok=True)
    
    print(f"Splitting '{filepath}' ({file_size / (1024*1024):.2f} MB)")
    print(f"Chunk size: {chunk_size_mb} MB")
    print(f"Output folder: {folder_name}/")
    
    # Calculate original file hash
    print("Calculating file hash...")
    original_hash = get_file_hash(filepath)
    
    chunk_num = 0
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            chunk_filename = os.path.join(folder_name, f"{base_name}.part{chunk_num:03d}")
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            
            print(f"Created: {chunk_filename} ({len(chunk) / (1024*1024):.2f} MB)")
            chunk_num += 1
    
    # Create metadata file in the folder
    meta_filename = os.path.join(folder_name, f"{base_name}.meta")
    with open(meta_filename, 'w') as meta:
        meta.write(f"original_name={base_name}\n")
        meta.write(f"num_chunks={chunk_num}\n")
        meta.write(f"original_size={file_size}\n")
        meta.write(f"chunk_size={chunk_size}\n")
        meta.write(f"sha256={original_hash}\n")
    
    print(f"\nSplit complete! Created {chunk_num} chunks")
    print(f"All files saved in: {folder_name}/")
    print(f"Original hash: {original_hash}")


def join_files(folder_name):
    """Join chunks back into original file"""
    
    if not os.path.isdir(folder_name):
        print(f"Error: Folder '{folder_name}' not found")
        return
    
    # Find the metadata file
    meta_files = [f for f in os.listdir(folder_name) if f.endswith('.meta')]
    
    if not meta_files:
        print(f"Error: No metadata file found in '{folder_name}'")
        return
    
    meta_filename = os.path.join(folder_name, meta_files[0])
    
    # Read metadata
    metadata = {}
    with open(meta_filename, 'r') as meta:
        for line in meta:
            key, value = line.strip().split('=', 1)
            metadata[key] = value
    
    original_name = metadata['original_name']
    num_chunks = int(metadata['num_chunks'])
    original_size = int(metadata['original_size'])
    original_hash = metadata['sha256']
    
    print(f"Rebuilding '{original_name}' from {num_chunks} chunks")
    print(f"Source folder: {folder_name}/")
    
    # Check all chunks exist
    missing = []
    for i in range(num_chunks):
        chunk_filename = os.path.join(folder_name, f"{original_name}.part{i:03d}")
        if not os.path.exists(chunk_filename):
            missing.append(chunk_filename)
    
    if missing:
        print("Error: Missing chunk files:")
        for m in missing:
            print(f"  - {m}")
        return
    
    # Rebuild file (save in current directory)
    output_name = original_name
    if os.path.exists(output_name):
        output_name = f"rebuilt_{output_name}"
        print(f"Warning: Output file exists, using '{output_name}'")
    
    with open(output_name, 'wb') as outfile:
        for i in range(num_chunks):
            chunk_filename = os.path.join(folder_name, f"{original_name}.part{i:03d}")
            with open(chunk_filename, 'rb') as chunk_file:
                outfile.write(chunk_file.read())
            print(f"Merged: {os.path.basename(chunk_filename)}")
    
    # Verify file
    rebuilt_size = os.path.getsize(output_name)
    print(f"\nRebuilding complete!")
    print(f"Original size: {original_size:,} bytes")
    print(f"Rebuilt size:  {rebuilt_size:,} bytes")
    
    if rebuilt_size == original_size:
        print("✓ Size matches!")
        print("Verifying hash...")
        rebuilt_hash = get_file_hash(output_name)
        
        if rebuilt_hash == original_hash:
            print("✓ Hash matches! File integrity verified")
            print(f"Output: {output_name}")
        else:
            print("✗ Hash mismatch! File may be corrupted")
            print(f"Expected: {original_hash}")
            print(f"Got:      {rebuilt_hash}")
    else:
        print("✗ Size mismatch! File may be corrupted")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Split: python chunker.py split <file> [chunk_size_mb]")
        print("  Join:  python chunker.py join <folder_name>")
        print("\nExample:")
        print("  python chunker.py split large_file.zip 50")
        print("  python chunker.py join large_file.zip_chunks")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'split':
        filepath = sys.argv[2]
        chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        split_file(filepath, chunk_size)
    
    elif command == 'join':
        folder_name = sys.argv[2]
        join_files(folder_name)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'split' or 'join'")
        sys.exit(1)


if __name__ == '__main__':
    main()