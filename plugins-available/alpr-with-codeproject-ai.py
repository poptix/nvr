#! /usr/bin/python3 
import cv2
import numpy as np
import mysql.connector
import requests
import json
import settings
from io import BytesIO
from sys import argv



# Connect to the database
db_connection = mysql.connector.connect(
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    database=settings.MYSQL_DATABASE
)

# Load the image from the database
def load_image_from_database(id):
    query = f"SELECT image FROM images WHERE id = {id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        image_data = BytesIO(result[0])
        image = np.load(image_data, allow_pickle=True)
        return image
    return None

# Save the detected objects to the database
def save_detected_objects_to_database(id, object, x_min, x_max, y_min, y_max, confidence, extra):
    query = f"INSERT INTO predictions VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_connection.cursor()
    data_tuple = (id, object, x_min, x_max, y_min, y_max, (confidence*100), extra)
    print(data_tuple)
    cursor.execute(query,data_tuple)
    db_connection.commit()
    cursor.close()

# Perform object detection using CodeProject AI
def perform_object_detection(image, id):
    url = f"{settings.CODEPROJECT_HOST}/v1/image/alpr"
    headers = {'api-key': settings.CODEPROJECT_API_KEY}
    _, img_encoded = cv2.imencode('.jpg', image)
    files = {'image': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        response_data = response.json()
        for obj in response_data['predictions']:
            label = 'plate' 
            extra = obj['label'].lstrip("Plate: ") 
            # Save detected objects to the database
            save_detected_objects_to_database(id, label, obj['x_min'], obj['x_max'], obj['y_min'], obj['y_max'], obj['confidence'], extra)
        return 1 
    else:
        print("Error performing object detection:", response.text)
    return 0

# Main script
def main(id):
    # Load image from the database
    image = load_image_from_database(id)
    if image is None:
        print("Image not found in the database.")
        return

    # Perform object detection
    detected_objects = perform_object_detection(image, id)
    if detected_objects == 0:
        print("No objects detected.")
        return

    print("Detected objects saved to the database.")

if __name__ == '__main__':
    id = argv[1] 
    main(id)


