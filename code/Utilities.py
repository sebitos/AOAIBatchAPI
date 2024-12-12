import json
import tiktoken
import os
from token_count import TokenCount
from  datetime import datetime
from bs4 import BeautifulSoup
class Utils:
    #Add utility to count output tokens and estimate price.
    def __init__(self):
        pass
    @staticmethod
    def strip_directory_name(file_name):
        file_name_split = file_name.split("/")
        return file_name_split[len(file_name_split)-1]
    @staticmethod
    def get_file_name_only(file_name):
        file_name_with_extension = Utils.strip_directory_name(file_name)
        file_name_with_extension_split = file_name_with_extension.split(".")
        file_name_only = file_name_with_extension_split[0]
        return file_name_only
    @staticmethod
    def parse_batch_output_file(file_data,delimiter):
        file_split = file_data.split("\n")
        headers = []
        output_string = ""
        for content in file_split:
            if len(content) == 0:
                continue
            json_data = json.loads(content)
            aoai_content = json_data["response"]["body"]["choices"][0]["message"]["content"]
            aoai_content_formatted = aoai_content.replace("\n","").replace("json","").replace("'","").replace("`","")
            aoai_content_json = json.loads(aoai_content_formatted)
            keys = list(aoai_content_json.keys())
            if len(headers) == 0:
                output_string += f"custom_id{delimiter}"
                headers = keys
                output_string += delimiter.join(headers)
                output_string += "\n"
            output_string += json_data["custom_id"] + delimiter
            for key in keys:
                output_string += str(aoai_content_json[key])+delimiter
            #Trim the last comma
            output_string = output_string[:-1]
            output_string += "\n"
        return output_string.lstrip().rstrip()
    @staticmethod
    def get_directory_name_only(filename_with_path):
        file_name_split = filename_with_path.split("/")
        directory_name = ""
        for i in range(0,len(file_name_split)-1):
            directory_name += file_name_split[i] + "/"
        return directory_name
    @staticmethod
    def read_json_data(file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)
        return data
    def get_file_list(self,directory):
        file_list = []
        for file in os.listdir(directory):
            file_list.append(file)
        return file_list
    @staticmethod
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    @staticmethod
    def get_tokens_in_file(file, model_family):
        tc = TokenCount(model_name=model_family)
        tokens = tc.num_tokens_from_file(file)
        return tokens
    @staticmethod
    def append_postfix(file):
        datetime_string = datetime.today().strftime('%Y-%m-%d_%H_%M_%S')
        return f"{file}_{datetime_string}"
    @staticmethod
    def clean_binary_string(data):
        return data[2:-1].replace('\\n', '').replace('\\"', '"').replace('\\\\', '\\')
    @staticmethod
    def convert_to_json_from_binary_string(data):
        # Remove the leading "b'" and trailing "'"
        data_str = data[2:-1]

        # Replace escape sequences
        data_str_clean = data_str.replace('\\n', '').replace('\\"', '"').replace('\\\\', '\\')

        # Convert the JSON string to a dictionary
        data_dict = json.loads(data_str_clean)
        return data_dict
    @staticmethod
    def get_file_extension(file_name):
        file_name_split = file_name.split(".")
        #No extension
        extension = file_name
        if len(file_name_split) > 1:
            extension = file_name_split[len(file_name_split)-1]
        return extension
    @staticmethod
    def get_body_from_html(html_string):
        # Parse the HTML string
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the body of the page
        text_content = soup.get_text()
        content = ""
        for element in text_content:
            content+=element
       # content = ""
       # for element in text_content:
       #     content+=element.get_text()
        content = content.replace('\\u200b','')
        content = content.replace('\u200b','')
        content = content.replace('\u2009','')
        return content
        

