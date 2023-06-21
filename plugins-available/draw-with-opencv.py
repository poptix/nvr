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

def photoshop_brightness(input_img, brightness=0):
    ''' input_image:  color or grayscale image
        brightness:  -127 (all black) to +127 (all white)

            returns image of same type as input_image but with
            brightness adjusted

    '''
    img = input_img.copy()
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        
        cv2.convertScaleAbs(input_img, img, alpha_b, gamma_b)
        
    return img


# Draw bounding boxes on the image with random pastel colors and labels
def draw_bounding_boxes(image, predictions):
    n_colors = len(predictions)
    palette = sns.color_palette("pastel", n_colors=n_colors).as_hex()

    # Save a copy of the original image
    original_image = image.copy()
    # Reduce the brightness of the working image
    image = photoshop_brightness(image, -100)

    # This loop must happen before we start drawing. 
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

        # Paste this part of the original image back, so that it's full brightness
        cropped = original_image[y_min:y_max, x_min:x_max]
        image[y_min:y_max, x_min:x_max] = cropped

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

        accent = 3

        # Some percentage of the line length
        someperx = int((x_max-x_min)*.20)
        somepery = int((y_max-y_min)*.20)

        # Make the box prettier in the top left corner
        start_point = (x_min-accent, y_min-accent)
        end_point = (x_min, y_min+somepery)
        cv2.rectangle(image, start_point, end_point, color,
                      thickness=-1, lineType=cv2.LINE_AA)

        start_point = (x_min-accent, y_min-accent)
        end_point = (x_min+someperx, y_min)
        cv2.rectangle(image, start_point, end_point, color,
                      thickness=-1, lineType=cv2.LINE_AA)

        # Make the box prettier in the bottom right corner
        start_point = (x_max+accent, y_max+accent)
        end_point = (x_max, y_max-somepery)
        cv2.rectangle(image, start_point, end_point, color,
                      thickness=-1, lineType=cv2.LINE_AA)

        start_point = (x_max+accent, y_max+accent)
        end_point = (x_max-someperx, y_max)
        cv2.rectangle(image, start_point, end_point, color,
                      thickness=-1, lineType=cv2.LINE_AA)

        # Avoid putting labels too close to the edge of the image
        if y_min >= 100:
            # Put the label in the top left
            cv2.putText(image, "%s (%.2f%%)" % (label, confidence), (x_min -
                        (accent*2), y_min-(accent*2)), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
        else:
            # Put the label in the bottom right
            cv2.putText(image, "%s (%.2f%%)" % (label, confidence), (x_max +
                        (accent*2), y_max+(accent*2)), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)



    
    return image


# Function to store an image in the MySQL database
def store_image_in_database(img_array, id):
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

        data_tuple = (image_data, id)

        update_query = 'UPDATE images SET modified_image=%s WHERE id=%s'

        cursor.execute(update_query, data_tuple)
        conn.commit()

    except Error as e:
        print(f'Error storing image in the database: {e}')
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

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

    # Update the database 
    store_image_in_database(image_with_boxes, image_id)

if __name__ == '__main__':
    main()

