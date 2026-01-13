import xarray as xr
from google.cloud import storage
import os
from google.auth.credentials import AnonymousCredentials

class GLMFileDownloader:
    client = None
    bucket = None

    def __init__(self):
        self.client = storage.Client(credentials=AnonymousCredentials(), project="public-data")



    def download_to_disk(self, bucket_name, prefix, destination_dir):
        bucket = self.client.bucket(bucket_name)
        
        # Make destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)

        # List all blobs under the prefix
        blobs = bucket.list_blobs(prefix=prefix)

        for blob in blobs:
            # Skip "directory" placeholders if any
            if blob.name.endswith("/"):
                continue

            destination_path = os.path.join(
                destination_dir,
                os.path.basename(blob.name)
            )

            blob.download_to_filename(destination_path)
            print(f"Downloaded {blob.name} to {destination_path}")


    def download_to_memory(self, bucket_name, prefix):
        bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)

        data_objects = {}

        for blob in blobs:
            # Skip folder placeholders
            if blob.name.endswith("/"):
                continue

            # Download file contents into memory
            data = blob.download_as_bytes()

            # Store using the blob name as the key
            data_objects[blob.name] = data

            print(f"Loaded {blob.name} into memory ({len(data)} bytes)")

        return data_objects
