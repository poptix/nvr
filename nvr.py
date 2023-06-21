#! /usr/bin/python3

import os
from io import BytesIO
import numpy as np
from PIL import Image
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import settings
import subprocess
import sys



# Schema for the images table in the MySQL database
CREATE_TABLE_QUERY = '''
CREATE TABLE IF NOT EXISTS images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255),
    image LONGBLOB,
    detected_objects LONGBLOB
)
'''

# Function to convert an image file to a NumPy array
def convert_image_to_numpy(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)
    return img_array


# Function to store an image in the MySQL database
def store_image_in_database(filename, img_array):
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE
        )

        cursor = conn.cursor()

        np_bytes = BytesIO()

        np.save(np_bytes, img_array, allow_pickle=True)

        image_data = np_bytes.getvalue()

        data_tuple = (filename, image_data)

        insert_query = 'INSERT INTO images (filename, image) VALUES (%s, %s)'

        cursor.execute(insert_query, data_tuple)
        conn.commit()
        os.unlink(filename)
        id = cursor.lastrowid
        print(f'Successfully stored {filename} in the database with ID {id}.')
        execute_scripts_with_id('plugins-enabled/', id)



    except Error as e:
        print(f'Error storing {filename} in the database: {e}')

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def execute_scripts_with_id(directory, id):
    # Get a sorted list of script filenames in the directory
    script_files = sorted([
        filename for filename in os.listdir(directory)
        #if filename.endswith('.py') and filename.isdigit()
    ])

    # Execute each script and check the exit code
    for script_file in script_files:
        script_path = os.path.join(directory, script_file)
        command = [sys.executable, script_path, str(id)]
        exit_code = subprocess.call(command)
        print(f"Script '{script_file}' executed with exit code: {exit_code}")


# Watchdog event handler to monitor file system events
class ImageUploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = event.src_path
            img_array = convert_image_to_numpy(filename)
            store_image_in_database(filename, img_array)


if __name__ == "__main__":
    # Create the images table in the MySQL database
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE
        )

        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_QUERY)

    except Error as e:
        print(f'Error creating the images table: {e}')

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Start monitoring the directory for image uploads
    event_handler = ImageUploadHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.UPLOADPATH, recursive=True)
    observer.start()

    print('Image upload watcher started. Press Ctrl+C to stop.')

    try:
        while True:
            pass

    except KeyboardInterrupt:
        observer.stop()

    observer.join()

