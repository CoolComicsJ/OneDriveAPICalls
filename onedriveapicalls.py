import msal
import requests
import json
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Azure AD app credentials
client_id = '31c6a633-ff7c-47ad-b01a-b4c2ff3c02a5'
tenant_id = 'common'
client_secret = 'KJr8Q~IfDr7zBbSFU5yx4D3cVdb.rk02WFmvEble'

# Authority URL and endpoints
AUTHORITY_URL = f"https://login.microsoftonline.com/{tenant_id}"
REDIRECT_URI = 'http://localhost:8000/callback'  # Use the unique redirect URI
SCOPES = ["User.Read", "Files.Read", "Files.ReadWrite", "Files.ReadWrite.All"]
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0/me/drive/root/children"

# Initialize MSAL Client
app = msal.ConfidentialClientApplication(client_id, authority=AUTHORITY_URL, client_credential=client_secret)

# Authentication Handler
class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if 'code' in self.path:
            auth_code = self.path.split('code=')[1].split('&')[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Authentication successful. You can close this window.')
            self.server.auth_code = auth_code

def authenticate():
    authorization_url = app.get_authorization_request_url(SCOPES, redirect_uri=REDIRECT_URI)
    webbrowser.open(authorization_url)

    httpd = HTTPServer(('localhost', 8000), OAuth2CallbackHandler)
    httpd.handle_request()
    auth_code = httpd.auth_code

    result = app.acquire_token_by_authorization_code(auth_code, scopes=SCOPES, redirect_uri=REDIRECT_URI)

    if 'access_token' in result:
        return result['access_token']
    else:
        raise Exception(f"Failed to acquire access token: {result.get('error_description')}")

def list_directories(access_token):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    response = requests.get(GRAPH_ENDPOINT, headers=headers)

    if response.status_code == 200:
        items = response.json().get('value', [])
        directories = [item for item in items if 'folder' in item]
        for directory in directories:
            print(f"Directory Name: {directory['name']}, ID: {directory['id']}")
        return "SUCCESS"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "FAILURE"

def list_files(access_token, parent_directory_id):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_directory_id}/children"
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        items = response.json().get('value', [])
        files = [item for item in items if 'file' in item]
        for file in files:
            file_name = file['name']
            file_size = file['size']
            file_extension = file_name.split('.')[-1] if '.' in file_name else 'No extension'
            file_path = file['parentReference']['path'] + '/' + file_name
            print(f"File Name: {file_name}, Extension: {file_extension}, Size: {file_size} bytes, Path: {file_path}")
        return "SUCCESS"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "FAILURE"

def list_subdirectories(access_token, parent_directory_id):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_directory_id}/children"
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        items = response.json().get('value', [])
        subdirectories = [item for item in items if 'folder' in item]
        for subdirectory in subdirectories:
            print(f"Subdirectory Name: {subdirectory['name']}, ID: {subdirectory['id']}")
        return "SUCCESS"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "FAILURE"

def upload_file(access_token, parent_directory_id, file_path):
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/octet-stream'}
    file_name = file_path.split('/')[-1]
    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_directory_id}:/{file_name}:/content"
    
    # Ensure the file path uses forward slashes
    file_path = file_path.replace('\\', '/')
    
    with open(file_path, 'rb') as file:
        response = requests.put(endpoint, headers=headers, data=file)

    if response.status_code in (200, 201):
        print(f"File '{file_name}' uploaded successfully.")
        return "SUCCESS"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "FAILURE"

def download_file(access_token, file_path, destination_directory):
    headers = {'Authorization': f'Bearer {access_token}'}
    # Ensure the file path uses forward slashes and is correctly formatted
    file_path = file_path.replace('\\', '/').strip('/')
    endpoint = f"https://graph.microsoft.com/v1.0/me/drive/root:/{file_path}:/content"
    
    response = requests.get(endpoint, headers=headers, stream=True)

    if response.status_code == 200:
        # Extract the file name from the file path
        file_name = os.path.basename(file_path)
        destination_path = os.path.join(destination_directory, file_name)
        
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded successfully to {destination_path}.")
        return "SUCCESS"
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "FAILURE"

def main():
    try:
        access_token = authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
        return "FAILURE"

    while True:
        print("\nMenu:")
        print("1. List Directories")
        print("2. List Files with Extensions and Sizes")
        print("3. List Subdirectories in a Directory")
        print("4. Upload a File")
        print("5. Download a File")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            result = list_directories(access_token)
            print(result)
        elif choice == '2':
            parent_directory_id = input("Enter the ID of the directory to list files: ")
            result = list_files(access_token, parent_directory_id)
            print(result)
        elif choice == '3':
            parent_directory_id = input("Enter the ID of the parent directory: ")
            result = list_subdirectories(access_token, parent_directory_id)
            print(result)
        elif choice == '4':
            parent_directory_id = input("Enter the ID of the parent directory: ")
            file_path = input("Enter the path to the file to upload: ").replace('\\', '/')
            result = upload_file(access_token, parent_directory_id, file_path)
            print(result)
        elif choice == '5':
            file_path = input("Enter the path of the file to download (relative to OneDrive root): ").replace('\\', '/')
            destination_directory = input("Enter the destination directory to save the file: ").replace('\\', '/')
            result = download_file(access_token, file_path, destination_directory)
            print(result)
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()