from calendar import c
import sqlite3
from typing import Tuple


class DB_Controller:
    def __init__(self, db_filename: str) -> None:
        self.db_filename = db_filename

    def _get_image_name(self, image_id: int, connection: sqlite3.Connection) -> str:
        cursor = connection.cursor()
        cursor.execute("SELECT filename FROM images WHERE image_id=?", (image_id,))
        filename: str = cursor.fetchone()[0]
        return filename

    def _get_tag_name(self, tag_id: int, connection: sqlite3.Connection) -> str:
        cursor = connection.cursor()
        cursor.execute("SELECT tag FROM tags WHERE tag_id=?", (tag_id,))
        tag: str = cursor.fetchone()[0]
        return tag

    def _get_image_id(self, image: str, connection: sqlite3.Connection) -> int:
        cursor = connection.cursor()
        cursor.execute("SELECT image_id FROM images WHERE filename=?", (image,))
        image_id: int = cursor.fetchone()[0]

        return image_id

    def _get_tag_id(self, tag: str, connection: sqlite3.Connection) -> int:
        cursor = connection.cursor()
        cursor.execute("SELECT tag_id FROM tags WHERE tag=?", (tag,))
        tag_id: int = cursor.fetchone()[0]
        return tag_id

    def _print_everything(self, connection: sqlite3.Connection):
        cursor = connection.cursor()
        print("------Tables-----")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print(cursor.fetchall())

        print("------Images-----")
        cursor.execute("SELECT * FROM images;")
        print(cursor.fetchall())

        print("------Tags-----")
        cursor.execute("SELECT * FROM tags;")
        print(cursor.fetchall())

        print("------Image_Tags-----")
        cursor.execute("SELECT * FROM image_tags;")
        print(cursor.fetchall())

    def get_image_tags(self, image: str) -> list[str]:
        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()

        print(image)
        image_id = self._get_image_id(image, connection)
        print(image_id)
        cursor.execute("SELECT tag_id FROM image_tags WHERE image_id=?", (image_id,))
        result = cursor.fetchall()
        # print(result)

        tags = []
        for tag in result:
            # print(self._get_tag_name(tag[0]))
            tags.append(self._get_tag_name(tag[0], connection))

        connection.close()
        return tags

    def find_images_with_tags(self, tags: list[str]) -> list[str]:
        images = []

        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()

        tag_ids = [self._get_tag_id(tag, connection) for tag in tags]
        
        image_ids_with_tag: dict[int, list[int]] = {}

        for tag_id in tag_ids:
            cursor.execute("SELECT image_id FROM image_tags WHERE tag_id=?", (tag_id,))
            image_ids = [entry[0] for entry in cursor.fetchall()]
            print(f"tag {tag_id} is assigned to the following images_ids {image_ids}")
            image_ids_with_tag[tag_id] = image_ids
            
        for image_id in list(image_ids_with_tag.values())[0]:
            if all(image_id in x for x in image_ids_with_tag.values()):
                print(f"image_id {image_id} has all tags assigned to it")
                images.append(self._get_image_name(image_id, connection))
            
        connection.close()
        return images
