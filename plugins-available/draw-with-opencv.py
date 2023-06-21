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

# Load image from the images table
def load_image_from_database(image_id):
    query = f"SELECT image FROM images WHERE id = {image_id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        image_data = BytesIO(result[0])
        image = np.load(image_data, allow_pickle=True)

        return image
    return None


# Load predictions from the predictions table
def load_predictions_from_database(image_id):
    query = f"SELECT object, confidence, x_min, y_min, x_max, y_max, extra FROM predictions WHERE id = {image_id}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows

# Draw bounding boxes on the image with random pastel colors and labels
def draw_bounding_boxes(image, predictions):
    n_colors = len(predictions)
    palette = sns.color_palette("pastel", n_colors=n_colors).as_hex()
    
    for i, prediction in enumerate(predictions):
        label, confidence, x_min, y_min, x_max, y_max, extra = prediction
        if label == 'make_model':
          continue
        if label == 'year':
          continue
        if label == 'orientation':
          continue
        if label == 'body_type':
          continue
        if label == 'color':
          continue
        if label == 'region':
          continue
        if len(extra): 
          label = extra
        color = tuple(int(palette[i].lstrip("#")[j : j + 2], 16) for j in (0, 2, 4))
        label_text = f"{label} ({confidence:.2f})"
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)
        cv2.putText(image, label_text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    return image

# Main script
def main():
    # Retrieve the image ID and the desired image ID from the command line or elsewhere
    image_id = argv[1]  # Replace with the desired image ID

    # Load image from the database
    image = load_image_from_database(image_id)
    if image is None:
        print("Image not found in the database.")
        return

    # Load predictions from the database
    predictions = load_predictions_from_database(image_id)
    if len(predictions) == 0:
        print("No predictions found in the database.")
        return

    # Draw bounding boxes on the image
    image_with_boxes = draw_bounding_boxes(image, predictions)

    # Display the image with bounding boxes
    cv2.imwrite("/dev/shm/tmp.jpg", image)

if __name__ == '__main__':
    main()

