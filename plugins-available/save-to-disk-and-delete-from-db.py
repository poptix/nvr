#! /usr/bin/python3
import cv2
import numpy as np
import mysql.connector
import seaborn as sns
from sys import argv
import settings
from io import BytesIO

# Connect to the MySQL database
db_connection = mysql.connector.connect(
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    database=settings.MYSQL_DATABASE
)

# Delete image from the images table
def delete_image_from_database(image_id):
    print("delete..")
    query = f"DELETE FROM images WHERE id = {image_id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    query = f"DELETE FROM predictions WHERE id = {image_id}"
    cursor.execute(query)
    db_connection.commit()
    cursor.close()
    return None

# Load image from the images table
def load_image_from_database(image_id):
    query = f"SELECT modified_image FROM images WHERE id = {image_id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    if result is not None and len(result[0]) > 0:
        image_data = BytesIO(result[0])
        image = np.load(image_data, allow_pickle=True)

        return image
    return None


# Function to store an image in the MySQL database
def store_image_on_disk(img_array, filename):
    cv2.imwrite(filename, img_array)

# Main script
def main():
    # Retrieve the image ID and the desired image ID from the command line or elsewhere
    image_id = argv[1]  # Replace with the desired image ID

    # Load image from the database
    image = load_image_from_database(image_id)

    # If nothing was found there won't be a modified image, it's not fatal
    if image is not None:
        store_image_on_disk(image, '/dev/shm/tmp.jpg')

    delete_image_from_database(image_id)

if __name__ == '__main__':
    main()

