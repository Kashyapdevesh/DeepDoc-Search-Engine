import io
import boto3
import paramiko
import logging

from google.cloud import storage

logger=logging.getLogger("ConnectorLogs")
  

class Connectors:
    def __init__(self):
        self.logger=logging.getLogger(self.__class__.__name__)

    def stream_pdf(self,file_content):
        return io.BytesIO(file_content)
    
    def populate_pdfs(self,pdf_files,client,fetch_method):
        print(len(pdf_files))
        for pdf_file in pdf_files:
            self.logger.info(f"Reading {pdf_file} from {self.__class__.__name__}")
            file_content=fetch_method(client,pdf_file)
            pdf_stream=self.stream_pdf(file_content)

class SFTPConnector(Connectors):
    def __init__(self,SFTP_HOST,SFTP_PORT,SFTP_USERNAME,SFTP_PASSWORD,SFTP_DIRECTORY):
        super().__init__()
        self.sftp_host=SFTP_HOST
        self.sftp_port=SFTP_PORT
        self.sftp_username=SFTP_USERNAME
        self.sftp_password=SFTP_PASSWORD
        self.sftp_directory=SFTP_DIRECTORY

    def setup_client(self):
        transport=paramiko.Transport((self.sftp_host,self.sftp_port))
        transport.connect(username=self.sftp_username,password=self.sftp_password)
        sftp_client=paramiko.SFTPClient.from_transport(transport)
        return sftp_client
    
    def fetch_pdf_list(self,sftp_client):
        pdf_files=[f"{self.sftp_directory}/{file}" for file in sftp_client.listdir(self.sftp_directory) if file.endswith(".pdf")]
        return pdf_files
    
    def fetch_file(self,sftp_client,file_path):
        with sftp_client.open(file_path,"rb") as remote_file:
            return remote_file.read()

    def run_connector(self):
        sftp_client=self.setup_client()
        pdf_list=self.fetch_pdf_list(sftp_client)
        self.populate_pdfs(pdf_list, sftp_client, self.fetch_file)

# class ADLSConnector(Connectors):
#     def __init__(self):
#         pass

class AWSConnector(Connectors):
    def __init__(self,aws_bucket,aws_directory):
        super().__init__()
        self.aws_bucket_name=aws_bucket
        self.aws_folder_path=aws_directory

    def setup_client(self):
        return boto3.client("s3")
    
    def fetch_pdf_list(self,aws_client):
        aws_blobs=aws_client.list_objects_v2(Bucket=self.aws_bucket_name,Prefix=self.aws_folder_path)
        pdf_files=[aws_blob["Key"] for aws_blob in aws_blobs.get("Contents",[]) if aws_blob["Key"].endswith(".pdf")]
        return pdf_files
    
    def fetch_file(self,aws_client,file_path):
        s3_object=aws_client.get_object(Bucket=self.aws_bucket_name,Key=file_path)
        return s3_object["Body"].read()
    
    def run_connector(self):
        aws_client=self.setup_client()
        pdf_list=self.fetch_pdf_list(aws_client)
        self.populate_pdfs(pdf_list,aws_client,self.fetch_file)

class GCPConnector(Connectors):
    def __init__(self,gcp_bucket,gcp_directory,gcp_cred_path):
        super().__init__()
        self.gcp_bucket_name=gcp_bucket
        self.gcp_folder_path=gcp_directory
        self.gcp_cred_path=gcp_cred_path

    def setup_client(self):
        return storage.Client.from_service_account_json(self.gcp_cred_path)
    
    def fetch_pdf_list(self,gcp_client):
        gcp_bucket=gcp_client.bucket(self.gcp_bucket_name)
        gcp_blobs=gcp_bucket.list_blobs(prefix=self.gcp_folder_path)
        pdf_files=[gcp_blob.name for gcp_blob in gcp_blobs if gcp_blob.name.endswith(".pdf")]
        return pdf_files
    
    def fetch_file(self,gcp_client,file_path):
        gcp_bucket=gcp_client.bucket(self.gcp_bucket_name)
        return gcp_bucket.blob(file_path).download_as_bytes()

    def run_connector(self):
        gcp_client=self.setup_client()
        pdf_list=self.fetch_pdf_list(gcp_client)
        self.populate_pdfs(pdf_list,gcp_client,self.fetch_file)
    
if __name__=="__main__":
    gcp=GCPConnector(
        gcp_bucket="indgene_hackathon_pdfs",
        gcp_directory="NCBI_PDFS_2024/2024/",
        gcp_cred_path="./Credentials/service-account-key.json"
    )
    gcp.run_connector()