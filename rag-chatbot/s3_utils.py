import boto3
import os
import json
import logging
import numpy as np
import concurrent.futures

logger = logging.getLogger(__name__)

# TBD, add deduplication function

def split_logs_into_chunks_by_words(logs, words_per_chunk=200):
    """Splits logs into chunks based on a fixed number of words."""
    chunks = []
    current_chunk = []
    current_word_count = 0

    for log in logs:
        words = log.split()
        if current_word_count + len(words) > words_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_word_count = 0
        current_chunk.extend(words)
        current_word_count += len(words)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def download_all_logs_to_single_file(bucket_name, prefix, output_file_path, logger=logger, words_per_chunk=50, max_workers=10):
    try:
        output_dir = os.path.dirname(output_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created directory: {output_dir}")

        s3_client = boto3.client('s3')
        objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        all_logs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for obj in objects.get('Contents', []):
                file_key = obj['Key']
                futures.append(executor.submit(download_file, s3_client, bucket_name, file_key, logger))

            for future in concurrent.futures.as_completed(futures):
                try:
                    logs = future.result()
                    all_logs.extend(logs)
                except Exception as e:
                    logger.error(f"Error downloading file: {e}")

        logger.info("Finished downloading all logs from S3.")
        unique_logs = all_logs
        # Split logs into smaller chunks by words
        chunks = split_logs_into_chunks_by_words(unique_logs, words_per_chunk=words_per_chunk)
        
        for i, chunk in enumerate(chunks):
            chunk_file_path = os.path.join(output_dir, f"chunk_{i+1}.txt")
            with open(chunk_file_path, 'w') as f:
                f.write(chunk)
            logger.info(f"Saved chunk {i+1} with {len(chunk.split())} words to {chunk_file_path}")

    except Exception as e:
        logger.error(f"Error processing logs from S3: {e}")

def download_file(s3_client, bucket_name, file_key, logger):
    try:
        file_obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = file_obj['Body'].read().decode('utf-8')
        logs = file_content.splitlines()
        logger.info(f"Downloaded {file_key} and added to log aggregation.")
        return logs
    except Exception as e:
        logger.error(f"Error downloading {file_key}: {e}")
        return []
