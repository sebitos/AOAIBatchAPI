import streamlit as st
from FileGenerator import FileGenerator
import sys
from io import StringIO
from AzureStorageHandler import StorageHandler
from Utilities import Utils
import json
import os
APP_CONFIG = os.environ.get('APP_CONFIG', r"/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/config/app_config.json")
def main():
    st.set_page_config(page_title="Batch Processing UI", layout="wide")
    app_config_data = Utils.read_json_data(APP_CONFIG)
    storage_config_data = Utils.read_json_data(app_config_data["storage_config"])
    upload_interface,download_interface = st.tabs(["Upload","Download"])
    with upload_interface:
        handle_file_upload(storage_config_data)
    with download_interface:
        handle_file_download(storage_config_data)

def handle_file_download(storage_config_data):
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    processed_filesystem_system_name = storage_config_data["processed_filesystem_system_name"]
    processed_storage_handler = StorageHandler(storage_account_name, storage_account_key, processed_filesystem_system_name)
    output_directory = storage_config_data["output_directory"]
    files = processed_storage_handler.get_file_list(output_directory)
    files = [file for file in files if "output" in file]
    file_to_download = st.selectbox("Select a file to download",files,index=None,placeholder="Select a file to download...")
    if file_to_download is not None:
        file_wo_directory = Utils.strip_directory_name(file_to_download)
        directory_only = Utils.get_directory_name_only(file_to_download)
        filename_only = Utils.get_file_name_only(file_wo_directory)
        output_csv_filename = filename_only + ".csv"
        processed_directroy_client = processed_storage_handler.get_directory_client(directory_only)
        batch_response_data = processed_storage_handler.get_file_data(file_wo_directory,processed_directroy_client)
        batch_response_data_string = str(batch_response_data,'utf-8')
        st.write("File downloaded successfully!")
        output_csv = Utils.parse_batch_output_file(batch_response_data_string,"|")
        st.write("Generated CSV file successfully!")
        local_output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/download/"
        with open(local_output_path+output_csv_filename,"w",encoding="utf-8") as output_file:
            output_file.write(output_csv)
def handle_file_upload(storage_config_data):
    output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/batch_files/"
    csv_output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/data/"
    header = st.checkbox("Header row is present in the CSV file")
    uploaded_file = st.file_uploader("Choose a file to upload", type=['csv'])
    st.write("CSV Header in CSV file: ",header)
    if uploaded_file is not None:
        with st.spinner('Generating batch file...'):
            filename = uploaded_file.name
            #This is stupid, but this ensures that the file is processed from a known location...
            #TODO: Write better code when you're not tired...
            filename_with_path = csv_output_path+ "raw_csv/" + filename
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            with open(filename_with_path, "w") as file:
                file.write(string_data)
            batch_template_file = r"/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/templates/batch_template.json"
            fg = FileGenerator("CSV",batch_template_file,"gpt-4o-batch")
            csv = fg.read_and_parse_CSV(filename_with_path,header,",")
            batch_file = fg.generate_batch_file(csv)
            st.write("Files generated successfully!")
            batch_output = ""
            i = 0
            for i in range(0,len(batch_file)):
                batch_output += json.dumps(batch_file[i])
                if i < len(batch_file)-1:
                    batch_output += "\n"
            file_name_only = Utils.get_file_name_only(filename)
            output_filename = Utils.append_postfix(file_name_only) + "_batch_file.jsonl"
            output_file_path = output_path + output_filename
            write_content_to_storage(batch_output,output_filename,storage_config_data)
            st.write("File written to Azure Storage successfully!")
            #Write locally as well
            with open(output_file_path,"w") as file:
                file.write(batch_output)
            st.write("File written to local storage successfully!")
def write_content_to_storage(batch_output,batch_output_filename,storage_config_data):
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    input_filesystem_system_name =  storage_config_data["input_filesystem_system_name"]
    input_storage_handler = StorageHandler(storage_account_name, storage_account_key, input_filesystem_system_name)
    target_directory = storage_config_data["input_directory"]
    input_storage_handler.write_content_to_directory(batch_output,target_directory,batch_output_filename)
if __name__ == "__main__":
    main()
