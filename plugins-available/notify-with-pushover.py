#! /usr/bin/python3
import cv2
import numpy as np
import mysql.connector
import requests
from io import BytesIO
from sys import argv
import settings

# Connect to the MySQL database
db_connection = mysql.connector.connect(
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    database=settings.MYSQL_DATABASE
)

# Retrieve image from the database
def retrieve_image_from_database(image_id):
    query = f"SELECT modified_image FROM images WHERE id = {image_id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        image_data = result[0]
        image_np = np.load(BytesIO(image_data))
        return image_np
    return None

# Resize image to ensure it is smaller than the maximum allowed size
def resize_image(image):
    max_size = 2621440  # Maximum allowed image size in bytes
    _, image_encoded = cv2.imencode('.jpg', image)
    if image_encoded.size > max_size:
        scale_factor = np.sqrt(max_size / image_encoded.size)
        resized_image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)
        return resized_image
    return image

# Send image via Pushover API
def send_image_via_pushover(image):
    # Encode image to JPEG
    _, image_encoded = cv2.imencode('.jpg', image)

    # Prepare data for API request
    data = {
        'user':  settings.PUSHOVER_USER_KEY,
        'token': settings.PUSHOVER_API_KEY,
        'message': 'NVR Notification',
    }

    # Send image file via POST request
    files = {
        'attachment': ('image.jpg', image_encoded.tobytes(), 'image/jpeg')
    }

    response = requests.post('https://api.pushover.net/1/messages.json', data=data, files=files)

    # Check response status
    if response.status_code == 200:
        print("Image sent via Pushover successfully.")
    else:
        print("Failed to send image via Pushover.")
        print(response.json())

# Main script
def main():
    # Retrieve the image ID and the desired image ID from the command line or elsewhere
    image_id = argv[1]  # Replace with the desired image ID

    # Retrieve image from the database
    image = retrieve_image_from_database(image_id)
    if image is None:
        print("Image not found in the database.")
        return

    # Resize image if needed
    resized_image = resize_image(image)

    # Send image via Pushover API
    send_image_via_pushover(resized_image)

if __name__ == '__main__':
    main()

