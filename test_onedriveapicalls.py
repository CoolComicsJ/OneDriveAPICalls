import unittest
from unittest.mock import patch, Mock, mock_open
import onedriveapicalls  
import os

class TestOneDriveAPICalls(unittest.TestCase):

    @patch('onedriveapicalls.requests.get')
    def test_list_directories(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'name': 'Documents', 'id': '123', 'folder': {}},
                {'name': 'Photos', 'id': '456', 'folder': {}}
            ]
        }
        mock_get.return_value = mock_response

        result = onedriveapicalls.list_directories('fake_access_token')
        self.assertEqual(result, "SUCCESS")

    @patch('onedriveapicalls.requests.get')
    def test_list_files(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'name': 'file1.txt', 'size': 100, 'file': {}, 'parentReference': {'path': '/drive/root:/Documents'}},
                {'name': 'file2.jpg', 'size': 200, 'file': {}, 'parentReference': {'path': '/drive/root:/Photos'}}
            ]
        }
        mock_get.return_value = mock_response

        result = onedriveapicalls.list_files('fake_access_token', 'fake_parent_directory_id')
        self.assertEqual(result, "SUCCESS")

    @patch('onedriveapicalls.requests.get')
    def test_list_subdirectories(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'name': 'Subfolder1', 'id': '789', 'folder': {}},
                {'name': 'Subfolder2', 'id': '101112', 'folder': {}}
            ]
        }
        mock_get.return_value = mock_response

        result = onedriveapicalls.list_subdirectories('fake_access_token', 'fake_parent_directory_id')
        self.assertEqual(result, "SUCCESS")

    @patch('onedriveapicalls.requests.put')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_file(self, mock_open, mock_put):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response

        result = onedriveapicalls.upload_file('fake_access_token', 'fake_parent_directory_id', 'fake_file_path')
        self.assertEqual(result, "SUCCESS")

    @patch('onedriveapicalls.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file(self, mock_open, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b'testdata']
        mock_get.return_value = mock_response

        result = onedriveapicalls.download_file('fake_access_token', 'fake_file_path', 'fake_destination_directory')
        self.assertEqual(result, "SUCCESS")

        # Normalize the expected path format for comparison
        expected_path = os.path.join('fake_destination_directory', 'fake_file_path')
        mock_open.assert_called_once_with(expected_path, 'wb')

if __name__ == '__main__':
    unittest.main()