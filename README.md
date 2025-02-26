## EKS LLM Troubleshooting Chatbot

This project is a document retrieval chatbot designed for troubleshooting EKS (Elastic Kubernetes Service) logs. The chatbot uses a FAISS index to retrieve relevant logs from S3 and generates responses based on user queries. The chatbot is deployed using Terraform, which provisions necessary AWS resources like the S3 bucket to store the logs.

## Prerequisites

Before running this project, make sure you have the following installed:

- [Terraform](https://www.terraform.io/downloads.html)
- [AWS CLI](https://aws.amazon.com/cli/)
- [Python 3.8+](https://www.python.org/downloads/)

## Setup and Execution

### Step 1: Provision AWS Resources

First, you need to provision the necessary AWS resources, including the S3 bucket for storing the logs.

1. Clone the repository:

    ```bash
    git clone https://github.com/aws-samples/sample-eks-troubleshooting-rag-chatbot && cd eks-llm-troubleshooting/terraform/
    ```
2. [Optional: Needed for Slack integration] Create `terraform.tfvars` file in the `terraform` directory for Slack webhook and channel name:
    
    Example contents of `terraform.tfvars`
    ```bash
    slack_webhook_url = "https://hooks.slack.com/services/[YOUR-WEBHOOK]"
    slack_channel_name = "alert-manager-alerts"
    ```

3. Run install script to initialize and install terraform modules.

    ```bash
    cd terraform/

    ./install.sh
    ```

    After running the Terraform script, it will output the name of the S3 bucket as an environment variable:

    ```bash
    export BUCKET_NAME=$(terraform output -raw bucket_name)

    cd ../
    ```


### Step 2: Deploy Problem Pods for Testing

You can deploy problem pods into your EKS cluster to generate logs for testing. Use the provided bash script to deploy these pods:

```bash
./provision-delete-error-pods.sh -p db-migration
```

This script will create various pods that are likely to generate errors and logs, which the chatbot can then use for troubleshooting.

### Step 3: Configure Environment Variables
The chatbot uses a set of environment variables to determine the behavior of the application. Set these before running the chatbot.
- **PREFIX**: The S3 path to fetch logs from, based on the format `YYYY/MM/DD/`
- **BUCKET_NAME**: The bucket where logs are stored for retrieval (Default: eks-llm-troubleshooting-logs-rag-eks)
- **DOWNLOAD_DATA**: Determines if new logs will be pulled down from S3 on runtime. (Default: True)


### Step 4: Run the Chatbot

After setting up the environment and provisioning resources, you can now run the chatbot:

```bash
cd rag-chatbot/
pip install -r requirements.txt

python app.py
```

This will start a Gradio interface where you can interact with the chatbot on `http://localhost:7860/`. Type your query into the interface, and the chatbot will retrieve and display relevant logs from the S3 bucket.

*If you recieve an access denied API error, ensure your AWS account has access to `claude-3-sonnet-20240229-v1:0` in the correct region.*

### Configuration

- **Variables**: The `variables.tf` file contains a single variable, `name`, which defaults to `eks-llm-troubleshooting`.
- **Local Variables**: The `locals` section in the Terraform script defines the region, VPC CIDR, and availability zones.
- **Tags**: The provisioned resources are tagged with the blueprint name and the GitHub repository URL.

### Testing

Once the chatbot is running, you can use it to troubleshoot logs from the problematic pods you deployed earlier. The chatbot will fetch relevant logs based on the user's query and provide context-aware responses.

### Cleanup
1. Empty S3 logs bucket
2. `terraform destroy --auto-approve`

## Project Structure

- `rag-chatbot/`
    - `app.py`: The main application script that runs the Gradio interface.
    - `indexer.py`: Handles indexing of log data using FAISS.
    - `embedder.py`: Encodes data and queries for retrieval.
    - `retriever.py`: Retrieves relevant documents based on encoded queries.
    - `s3_utils.py`: Handles interactions with S3, including downloading logs.
    - `bedrock_client.py`: Handles requests to Amazon Bedrock.
    - `data_loader`: Loads data from chunks and filter data.
    - `kubernetes_resource.py`: Regex function to get model kubectl command, and execute it passing the results back to bedrock.
- `terraform/`
    - `variables.tf`: Terraform variable definitions.
    - `main.tf`: Terraform configuration for provisioning AWS resources.
    - `kinesis.tf`: Terraform configuration to provision Kinesis resources for logging stack.
    - `outputs.tf`: Terraform configuration to output bucket name.

## Acknowledgments

This project uses:

- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search.
- [Gradio](https://www.gradio.app/) for the user interface.
- [Terraform AWS EKS Blueprints](https://github.com/aws-ia/terraform-aws-eks-blueprints) as the basis for provisioning the infrastructure.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

