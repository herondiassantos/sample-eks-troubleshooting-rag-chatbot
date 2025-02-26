import boto3
import json
import datetime
import random

def generate_random_log():
    # Randomly select log types
    log_types = ["Frontend", "Backend", "Database", "Auth"]
    log_type = random.choice(log_types)
    
    # Create a log entry based on the selected log type
    if log_type == "Frontend":
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "ERROR",
            "message": "Uncaught TypeError: Cannot read property 'map' of undefined",
            "component": "Frontend",
            "file": "app.js",
            "line": 42,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "sessionId": "abc1234xyz",
            "userId": "user_7890",
            "details": {
                "error": "TypeError",
                "stackTrace": [
                    "at renderList (app.js:42:15)",
                    "at main (app.js:100:25)"
                ]
            }
        }
    elif log_type == "Backend":
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "ERROR",
            "message": "500 Internal Server Error",
            "component": "Backend",
            "file": "server.py",
            "line": 88,
            "userId": "user_7890",
            "details": {
                "error": "ServerError",
                "stackTrace": [
                    "at handleRequest (server.py:88)",
                    "at processData (utils.py:43)"
                ]
            }
        }
    elif log_type == "Database":
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "WARNING",
            "message": "Database connection pool exhausted",
            "component": "Database",
            "query": "SELECT * FROM users WHERE id = ?",
            "userId": "user_7890",
            "details": {
                "error": "PoolExhausted",
                "stackTrace": [
                    "at getConnection (dbpool.js:27)",
                    "at queryDatabase (dbqueries.js:56)"
                ]
            }
        }
    else:  # Auth log
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "INFO",
            "message": "User successfully authenticated",
            "component": "Auth",
            "userId": "user_7890",
            "details": {
                "authMethod": "OAuth",
                "provider": "Google"
            }
        }

    return log_entry


def upload_log_to_s3(bucket_name, log_entry, log_file_name):
    # Convert log entry to JSON string
    log_json = json.dumps(log_entry)
    
    # Upload log to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(Bucket=bucket_name, Key=log_file_name, Body=log_json)
    
    print(f"Log uploaded to s3://{bucket_name}/{log_file_name}")


def generate_and_upload_logs(bucket_name, total_logs=10, prefix="2024"):
    log_file_name_format = f"{prefix}/log_{{}}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    
    # Ensure only one frontend log
    frontend_log_generated = False
    
    for i in range(total_logs):
        # For testing: Ensure only one frontend log
        if not frontend_log_generated and i == random.randint(0, total_logs-1):
            log_entry = generate_random_log()
            if log_entry["component"] == "Frontend":
                frontend_log_generated = True
        else:
            # Generate random logs (frontend will only appear once)
            while True:
                log_entry = generate_random_log()
                if log_entry["component"] != "Frontend":
                    break
        
        log_file_name = log_file_name_format.format(i)
        upload_log_to_s3(bucket_name, log_entry, log_file_name)


# Test the function
if __name__ == "__main__":
    bucket_name = "test-llm-troubleshoot-rag"  # Replace with your S3 bucket name
    
    # Generate 10 logs, with only 1 frontend log
    generate_and_upload_logs(bucket_name, total_logs=50)
