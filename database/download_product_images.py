import os
import sys
from database.generate_real_photos import download_and_generate_photos

if __name__ == "__main__":
    print("Downloading real product photography from the web...")
    download_and_generate_photos()
    print("All category images updated with genuine high-resolution web photos!")
