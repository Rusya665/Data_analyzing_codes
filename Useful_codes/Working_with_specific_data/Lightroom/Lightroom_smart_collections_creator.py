import os
import uuid


class SmartCollection:
    """
    A class to create and save Lightroom Smart Collection files.
    """

    def __init__(self, output_path, title, collection_value, filename_value, side=None):
        """
        Initializes the SmartCollection object with the provided criteria.

        :param output_path: The path to the folder where the Smart Collection files will be saved.
        :param title: The title of the Smart Collection.
        :param collection_value: The collection value used in the Smart Collection criteria.
        :param filename_value: The filename value used in the Smart Collection criteria.
        :param side: The optional side flag used in the Smart Collection criteria. (default is None)
        """
        self.output_path = output_path
        self.title = title
        self.collection_value = collection_value
        self.filename_value = filename_value
        self.side = side
        self.template = self.create_smart_collection_template()

    def create_smart_collection_template(self):
        """
        Generates the Smart Collection content based on the provided criteria.

        :return: The generated Smart Collection content.
        """
        unique_id = str(uuid.uuid4()).upper()

        template = f"""s = {{
    id = "{unique_id}",
    internalName = "{self.title}",
    title = "{self.title}",
    type = "LibrarySmartCollection",
    value = {{
        {{
            criteria = "collection",
            operation = "any",
            value = "{self.collection_value}",
            value2 = "",
        }},
        {{
            criteria = "filename",
            operation = "any",
            value = "_{self.filename_value}",
            value2 = "",
        }},"""

        if self.side is not None:
            template += f"""
        {{
            criteria = "filename",
            operation = "any",
            value = "{self.side}",
            value2 = "",
        }},"""

        template += """
        combine = "intersect",
    },
    version = 0,
}
"""
        return template

    def save_smart_collection(self):
        """
        Saves the Smart Collection file to the specified output folder.

        :return: None
        """
        file_name = f"{self.title}.lrsmcol"
        file_path = os.path.join(self.output_path, file_name)

        with open(file_path, "w") as f:
            f.write(self.template)

        print(f"Smart collection saved at: {file_path}")


def main():
    """
    The main function that creates and saves Smart Collections based on the specified criteria.
    """
    output_path = r"C:/Users/runiza.TY2206042/OneDrive - O365 Turun yliopisto/Desktop/Smart collections"

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    collection_value = "2023 Textile"
    filename_values = ['00', '01', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90',
                       '91', '123', '130', '131', '132', '136', '137', '138', '139', '140', '141', '142', '157']

    side_flag = True

    for filename_value in filename_values:
        if side_flag:
            for i in range(0, 2):
                title = f"{filename_value}_{i}"
                side = f"{i}."
                smart_collection = SmartCollection(output_path, title, collection_value, filename_value, side)
                smart_collection.save_smart_collection()
        else:
            title = f"{filename_value}"
            smart_collection = SmartCollection(output_path, title, collection_value, filename_value)
            smart_collection.save_smart_collection()


if __name__ == "__main__":
    """
    Instructions on how to use the script:

    1. Set the 'output_path' variable to the desired folder path where the Smart Collection files will be saved.
    2. Set the 'collection_value' variable to the desired collection value to be used in the Smart Collection criteria.
    3. Set the 'filename_values' list to the desired filename values to be used in the Smart Collection criteria.
    4. Set the 'side_flag' variable to True if you want to create two Smart Collections for each filename value 
    (with ".0" and ".1" appended). Set it to False if you want to create only one Smart Collection for each filename
    value without appending anything.
    """
    main()
