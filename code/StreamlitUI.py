import streamlit as st
from FileGenerator import FileGenerator
import sys
from io import StringIO
from AzureStorageHandler import StorageHandler
from Utilities import Utils
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from datetime import datetime
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx



# From original code
# APP_CONFIG = os.environ.get('APP_CONFIG', r"/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/config/app_config.json")

# Get the directory of the script (current file's directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the config folder and app_config.json file
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "config", "app_config.json")

# Check if the config file exists at the resolved path
if not os.path.exists(DEFAULT_CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found at: {DEFAULT_CONFIG_PATH}")

# Get the APP_CONFIG environment variable or use the default path
APP_CONFIG = os.environ.get('APP_CONFIG', DEFAULT_CONFIG_PATH)

# Path to the runBatch.py script
RUNBATCH_PATH = os.path.join(SCRIPT_DIR, "..", "code", "runBatch.py")

# Initialize session state
if "batch_output" not in st.session_state:
    st.session_state["batch_output"] = ""
if "thread_running" not in st.session_state:
    st.session_state["thread_running"] = False
if "thread_result" not in st.session_state:
    st.session_state["thread_result"] = None

def main():
    st.set_page_config(page_title="Batch Processing UI", layout="wide")

    app_config_data = Utils.read_json_data(APP_CONFIG)
    storage_config_data = Utils.read_json_data(app_config_data["storage_config"])
    
    upload_interface, download_interface, batch_interface = st.tabs(["Upload", "Download", "Batch Processing"])
    
    with upload_interface:
        handle_file_upload(storage_config_data)
    
    with download_interface:
        handle_file_download(storage_config_data)
    
    with batch_interface:
        st.header("Batch Process Running Every Minute")
        run_batch_script()

        # Create a container for dynamic output updates
        output_container = st.empty()

        # Continuously display output from the batch process
        while st.session_state["thread_running"]:
            if st.session_state["thread_result"]:
                # Add timestamp to the output
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_output = f"[{timestamp}] {st.session_state['thread_result']}"

                # Append the new line to the existing batch output in session state
                st.session_state["batch_output"] += formatted_output + "\n"

                # Update the output container with the complete content
                output_container.markdown(
                    f"""
                    <div style="background-color:black;color:lime;padding:10px;font-family:monospace;height:400px;overflow:auto;">
                    <pre>{st.session_state["batch_output"]}</pre>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.session_state["thread_result"] = None  # Reset result to avoid duplicates

            time.sleep(2)  # Poll every 2 seconds for updates

        # Once thread is finished, show the final output
        output_container.markdown(
            f"""
            <div style="background-color:black;color:lime;padding:10px;font-family:monospace;height:400px;overflow:auto;">
            <pre>{st.session_state["batch_output"]}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Optionally, also display the batch output in a text area as a backup
        st.text_area("Batch Output", st.session_state["batch_output"], height=400)

def run_batch_script():
    if not st.session_state["thread_running"]:
        def target(ctx):
            add_script_run_ctx(threading.current_thread())

            try:
                process = subprocess.Popen(
                    ["python", RUNBATCH_PATH],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line buffering
                )

                # Stream the output line by line
                for line in iter(process.stdout.readline, ''):
                    # Add timestamp to the output
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state["thread_result"] = f"[{timestamp}] {line}"
                    st.session_state["thread_running"] = True

                process.stdout.close()
                _, stderr = process.communicate()

                if process.returncode != 0:
                    st.error(f"Batch process failed: {stderr}")
                else:
                    st.success("Batch process completed successfully.")

            except Exception as e:
                st.error(f"Error running batch process: {str(e)}")

            st.session_state["thread_running"] = False

        ctx = get_script_run_ctx()
        thread = threading.Thread(target=lambda: target(ctx), daemon=True)
        add_script_run_ctx(thread)
        thread.start()
        st.session_state["thread_running"] = True

# ORIGINAL CODE
#================================================================================

# def handle_file_download(storage_config_data):
#     storage_account_name = storage_config_data["storage_account_name"]
#     storage_account_key = storage_config_data["storage_account_key"]
#     processed_filesystem_system_name = storage_config_data["processed_filesystem_system_name"]
#     processed_storage_handler = StorageHandler(storage_account_name, storage_account_key, processed_filesystem_system_name)
#     output_directory = storage_config_data["output_directory"]
#     files = processed_storage_handler.get_file_list(output_directory)
#     files = [file for file in files if "output" in file]
#     file_to_download = st.selectbox("Select a file to download",files,index=None,placeholder="Select a file to download...")
#     if file_to_download is not None:
#         file_wo_directory = Utils.strip_directory_name(file_to_download)
#         directory_only = Utils.get_directory_name_only(file_to_download)
#         filename_only = Utils.get_file_name_only(file_wo_directory)
#         output_csv_filename = filename_only + ".csv"
#         processed_directroy_client = processed_storage_handler.get_directory_client(directory_only)
#         batch_response_data = processed_storage_handler.get_file_data(file_wo_directory,processed_directroy_client)
#         batch_response_data_string = str(batch_response_data,'utf-8')
#         st.write("File downloaded successfully!")
#         output_csv = Utils.parse_batch_output_file(batch_response_data_string,"|")
#         st.write("Generated CSV file successfully!")
#         local_output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/download/"
#         with open(local_output_path+output_csv_filename,"w",encoding="utf-8") as output_file:
#             output_file.write(output_csv)
# def handle_file_upload(storage_config_data):
#     output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/batch_files/"
#     csv_output_path = "/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/data/"
#     header = st.checkbox("Header row is present in the CSV file")
#     uploaded_file = st.file_uploader("Choose a file to upload", type=['csv'])
#     st.write("CSV Header in CSV file: ",header)
#     if uploaded_file is not None:
#         with st.spinner('Generating batch file...'):
#             filename = uploaded_file.name
#             #This is stupid, but this ensures that the file is processed from a known location...
#             #TODO: Write better code when you're not tired...
#             filename_with_path = csv_output_path+ "raw_csv/" + filename
#             stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
#             string_data = stringio.read()
#             with open(filename_with_path, "w") as file:
#                 file.write(string_data)
#             batch_template_file = r"/Users/nezeral/Desktop/CDT-Batch/AOAIBatchAPI/templates/batch_template.json"
#             fg = FileGenerator("CSV",batch_template_file,"gpt-4o-batch")
#             csv = fg.read_and_parse_CSV(filename_with_path,header,",")
#             batch_file = fg.generate_batch_file(csv)
#             st.write("Files generated successfully!")
#             batch_output = ""
#             i = 0
#             for i in range(0,len(batch_file)):
#                 batch_output += json.dumps(batch_file[i])
#                 if i < len(batch_file)-1:
#                     batch_output += "\n"
#             file_name_only = Utils.get_file_name_only(filename)
#             output_filename = Utils.append_postfix(file_name_only) + "_batch_file.jsonl"
#             output_file_path = output_path + output_filename
#             write_content_to_storage(batch_output,output_filename,storage_config_data)
#             st.write("File written to Azure Storage successfully!")
#             #Write locally as well
#             with open(output_file_path,"w") as file:
#                 file.write(batch_output)
#             st.write("File written to local storage successfully!")




def handle_file_download(storage_config_data):
    # Get the user's Downloads folder dynamically
    downloads_folder = Path.home() / "Downloads/CDT-Batch/download"
    downloads_folder.mkdir(parents=True, exist_ok=True)
    
    # Extract storage configuration
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    processed_filesystem_system_name = storage_config_data["processed_filesystem_system_name"]

    # Initialize StorageHandler
    processed_storage_handler = StorageHandler(storage_account_name, storage_account_key, processed_filesystem_system_name)
    
    # Get list of files from storage
    output_directory = storage_config_data["output_directory"]
    files = processed_storage_handler.get_file_list(output_directory)
    files = [file for file in files if "output" in file]

    # File selection UI
    file_to_download = st.selectbox("Select a file to download", files, index=None, placeholder="Select a file to download...")
    
    if file_to_download is not None:
        # Extract file information
        file_wo_directory = Utils.strip_directory_name(file_to_download)
        directory_only = Utils.get_directory_name_only(file_to_download)
        filename_only = Utils.get_file_name_only(file_wo_directory)
        output_csv_filename = filename_only + ".csv"
        
        # Download the file from storage
        processed_directory_client = processed_storage_handler.get_directory_client(directory_only)
        batch_response_data = processed_storage_handler.get_file_data(file_wo_directory, processed_directory_client)
        batch_response_data_string = str(batch_response_data, 'utf-8')
        
        st.write("File downloaded successfully!")
        
        # Parse the batch response to CSV
        output_csv = Utils.parse_batch_output_file(batch_response_data_string, "|")
        st.write("Generated CSV file successfully!")

        # Save the CSV to the Downloads folder
        local_output_path = downloads_folder / output_csv_filename
        with open(local_output_path, "w", encoding="utf-8") as output_file:
            output_file.write(output_csv)
        
        st.write(f"File saved to local storage successfully at: {local_output_path}")


def handle_file_upload(storage_config_data):
    # Get the user's Downloads folder dynamically
    downloads_folder = Path.home() / "Downloads"
    output_path = downloads_folder / "CDT-Batch/batch_files"
    csv_output_path = downloads_folder / "CDT-Batch/data/raw_csv"
    
    # Ensure directories exist
    output_path.mkdir(parents=True, exist_ok=True)
    csv_output_path.mkdir(parents=True, exist_ok=True)

    # Get the directory of the current script (points to the app's config folder)
    script_dir = Path(__file__).resolve().parent
    batch_template_file = script_dir.parent / "config/batch_template.json"

    # UI Interaction
    header = st.checkbox("Header row is present in the CSV file")
    uploaded_file = st.file_uploader("Choose a file to upload", type=['csv'])
    st.write("CSV Header in CSV file: ", header)
    
    if uploaded_file is not None:
        with st.spinner('Generating batch file...'):
            filename = uploaded_file.name
            filename_with_path = csv_output_path / filename
            
            # Read and write uploaded file locally
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()
            with open(filename_with_path, "w") as file:
                file.write(string_data)
            
            # Initialize the FileGenerator
            fg = FileGenerator("CSV", str(batch_template_file), "gpt-4o-batch")
            csv = fg.read_and_parse_CSV(str(filename_with_path), header, ",")
            batch_file = fg.generate_batch_file(csv)
            
            st.write("Files generated successfully!")
            
            # Generate the batch output content
            batch_output = "\n".join(json.dumps(item) for item in batch_file)
            
            # Generate output filename
            file_name_only = Utils.get_file_name_only(filename)
            output_filename = Utils.append_postfix(file_name_only) + "_batch_file.jsonl"
            output_file_path = output_path / output_filename
            
            # Write content to Azure Storage
            write_content_to_storage(batch_output, output_filename, storage_config_data)
            st.write("File written to Azure Storage successfully!")
            
            # Write to local Downloads folder
            with open(output_file_path, "w") as file:
                file.write(batch_output)
            st.write(f"File written to local storage successfully at: {output_file_path}")



def write_content_to_storage(batch_output,batch_output_filename,storage_config_data):
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    input_filesystem_system_name =  storage_config_data["input_filesystem_system_name"]
    input_storage_handler = StorageHandler(storage_account_name, storage_account_key, input_filesystem_system_name)
    target_directory = storage_config_data["input_directory"]
    input_storage_handler.write_content_to_directory(batch_output,target_directory,batch_output_filename)


if __name__ == "__main__":
    main()
