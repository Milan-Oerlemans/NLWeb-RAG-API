#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
AWS_ACCOUNT_ID="910490057295"
AWS_REGION="eu-north-1"
ECR_REPOSITORY="nlweb/app"
CLUSTER_NAME="sitetor-dev-stack-Cluster-Querie-Endpoint" # <-- REPLACE THIS
SERVICE_NAME="NLWeb-core-Service" # <-- REPLACE THISgoogle-api-python-client==2.112.0

# --- Step 1: Authenticate Docker to ECR ---
echo "🔐 Authenticating Docker with ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# --- Step 2: Build the new Docker image ---
echo "🛠️ Building Docker image..."
docker build -t $ECR_REPOSITORY .

# --- Step 3: Tag the image for ECR ---
echo "🏷️ Tagging image for ECR..."
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# --- Step 4: Push the image to ECR ---
echo "🚀 Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# --- Step 5: Force a new deployment in ECS ---
echo "🔄 Forcing new deployment in ECS service..."
echo "aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION"
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION


echo "✅ Deployment complete!"
