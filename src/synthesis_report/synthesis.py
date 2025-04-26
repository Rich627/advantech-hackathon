import boto3
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

class BedrockDataSynthesizer:
    def __init__(
        self, 
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0", 
        region: str = "us-east-1",
        temperature: float = 0.7,
        batch_size: int = 3
    ):
        """
        Initialize the BedrockDataSynthesizer.
        
        Args:
            model_id: The Bedrock model ID to use
            region: AWS region
            temperature: Model temperature (higher = more creative)
            batch_size: Number of samples to generate per API call
        """
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id
        self.temperature = temperature
        self.batch_size = batch_size
    
    def _create_prompt(self, data_samples: List[Dict[Any, Any]], num_to_generate: int) -> str:
        """Create a prompt for the language model to generate similar data."""
        prompt = "Human: 你是一個專門協助隧道裂縫維修報告資料生成的專家系統。\n\n"
        prompt += f"我需要你生成 {num_to_generate} 筆新的裂縫報告資料，格式應該與以下範例相似，但內容要有變化且合理：\n\n"
        prompt += f"{json.dumps(data_samples, ensure_ascii=False, indent=2)}\n\n"
        prompt += "請注意以下欄位的限制：\n"
        prompt += "- id: 格式為 issue_YYYY_MM_DD_HH_MM_SS\n"
        prompt += "- timestamp: 格式為 YYYY-MM-DD HH:MM:SS\n"
        prompt += "- length: 範圍 0 ~ 9999\n"
        prompt += "- width: 範圍 0 ~ 9999\n"
        prompt += "- position: 必須是以下其中之一: mountain, valley, urban\n"
        prompt += "- material: 必須是以下其中之一: concrete, steel, composite\n"
        prompt += "- crack_location: 範圍 A ~ Z\n"
        prompt += "- risk_level: 必須是以下其中之一: Low, Medium, High\n"
        prompt += "- action: 必須是以下其中之一: 灌漿修補, 裂縫填充, 表面處理, 結構加固\n\n"
        prompt += f"請幫我生成 {num_to_generate} 筆新的資料，使用與範例相同的格式與欄位，但要有變化、合理且真實的資料。\n"
        prompt += "請直接返回有效的JSON格式陣列，不要有任何額外的文字說明。\n\n"
        prompt += "Assistant: "
        return prompt
        
    def _invoke_bedrock(self, prompt: str) -> str:
        """Call Bedrock model with the given prompt."""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('content', [{}])[0].get('text', '')
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            raise
    
    def _parse_response(self, response_text: str) -> List[Dict[Any, Any]]:
        """Parse the response text to extract JSON data."""
        try:
            # Find the first occurrence of [ or { which should be the start of JSON
            json_start = min(
                response_text.find('['), 
                response_text.find('{') if response_text.find('{') != -1 else float('inf')
            )
            
            if json_start == -1:
                print("Could not find JSON start in response")
                return []
                
            json_text = response_text[json_start:]
            # Find the end of the JSON data
            # Try to find where the valid JSON ends
            result = []
            try:
                result = json.loads(json_text)
                return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                # If full text doesn't parse, try to find a valid JSON subset
                for i in range(len(json_text)-1, 0, -1):
                    try:
                        subset = json_text[:i]
                        if subset.endswith(']') or subset.endswith('}'):
                            parsed = json.loads(subset)
                            return parsed if isinstance(parsed, list) else [parsed]
                    except:
                        continue
                        
            print("Could not parse valid JSON from response")
            return []
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            print(f"Response text: {response_text[:500]}...")
            return []
    
    def _validate_and_fix_data(self, data: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """Validate and fix any issues with the generated data."""
        valid_positions = ['mountain', 'valley', 'urban']
        valid_materials = ['concrete', 'steel', 'composite']
        valid_risk_levels = ['Low', 'Medium', 'High']
        valid_actions = ['灌漿修補', '裂縫填充', '表面處理', '結構加固']
        
        valid_data = []
        for item in data:
            # Generate proper id and timestamp
            current_time = datetime.now()
            item['id'] = f"issue_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}"
            item['timestamp'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Validate length and width
            if 'length' not in item or not isinstance(item['length'], (int, float, str)) or float(item['length']) < 0 or float(item['length']) > 9999:
                item['length'] = str(round(random.uniform(1, 100), 2))
                
            if 'width' not in item or not isinstance(item['width'], (int, float, str)) or float(item['width']) < 0 or float(item['width']) > 9999:
                item['width'] = str(round(random.uniform(1, 50), 2))
            
            # Validate position
            if 'position' not in item or item['position'] not in valid_positions:
                item['position'] = random.choice(valid_positions)
            
            # Validate material
            if 'material' not in item or item['material'] not in valid_materials:
                item['material'] = random.choice(valid_materials)
            
            # Validate crack_location
            if 'crack_location' not in item or not item['crack_location'].isalpha() or len(item['crack_location']) != 1:
                item['crack_location'] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            
            # Validate engineer
            if 'engineer' not in item or not item['engineer']:
                engineers = ["張工程師", "李工程師", "王工程師", "陳工程師", "林工程師"]
                item['engineer'] = random.choice(engineers)
            
            # Validate risk_level
            if 'risk_level' not in item or item['risk_level'] not in valid_risk_levels:
                item['risk_level'] = random.choice(valid_risk_levels)
            
            # Validate action
            if 'action' not in item or item['action'] not in valid_actions:
                item['action'] = random.choice(valid_actions)
            
            # Add image_url if not present
            if 'image_url' not in item:
                item['image_url'] = f"https://s3.amazonaws.com/xxx/image/{item['id']}.jpg"
            
            valid_data.append(item)
        
        return valid_data
        
    def generate_data(self, base_samples: List[Dict[Any, Any]], total_count: int) -> List[Dict[Any, Any]]:
        """
        Generate synthetic data based on provided samples.
        
        Args:
            base_samples: List of sample data dictionaries to use as reference
            total_count: Total number of new samples to generate
            
        Returns:
            List of generated data dictionaries
        """
        all_generated_data = []
        remaining = total_count
        
        print(f"Generating {total_count} synthetic data samples in batches of {self.batch_size}")
        
        while remaining > 0:
            batch_size = min(remaining, self.batch_size)
            print(f"Generating batch of {batch_size} samples. Remaining: {remaining}")
            
            try:
                prompt = self._create_prompt(base_samples, batch_size)
                response_text = self._invoke_bedrock(prompt)
                batch_data = self._parse_response(response_text)
                
                # Validate that we got the expected format
                if not isinstance(batch_data, list):
                    if isinstance(batch_data, dict):
                        # If we got a single dict but expected a list
                        batch_data = [batch_data]
                    else:
                        print(f"Unexpected response format: {type(batch_data)}")
                        continue
                
                # Check if we got the expected number of samples
                if len(batch_data) < batch_size:
                    print(f"Warning: Requested {batch_size} samples but only received {len(batch_data)}")
                
                # Validate and fix data
                valid_batch = self._validate_and_fix_data(batch_data)
                all_generated_data.extend(valid_batch)
                remaining -= len(valid_batch)
                
                # Add a small delay to avoid rate limiting
                if remaining > 0:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error generating batch: {str(e)}")
                # Continue with the next batch if there's an error
                time.sleep(2)  # Wait a bit longer after an error
        
        return all_generated_data
    
    def save_to_json(self, data: List[Dict[Any, Any]], output_path: str) -> None:
        """Save generated data to a JSON file."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved {len(data)} samples to {output_path}")
        except Exception as e:
            print(f"Error saving data to {output_path}: {str(e)}")


def load_samples(file_path: str) -> List[Dict[Any, Any]]:
    """Load sample data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both single object and list formats
            return [data] if isinstance(data, dict) else data
    except Exception as e:
        print(f"Error loading samples from {file_path}: {str(e)}")
        return []


def main():
    """Example usage of the BedrockDataSynthesizer."""
    # Path to sample data
    samples_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "metadata", "sample_metadata.json")
    
    # Path to save generated data
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              "metadata", "generated_metadata.json")
    
    # Load sample data
    samples = load_samples(samples_path)
    if not samples:
        print("Error: No sample data found.")
        return
    
    # Initialize synthesizer
    synthesizer = BedrockDataSynthesizer(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        batch_size=3  # Generate 3 samples per API call
    )
    
    # Generate data
    total_to_generate = 10  # Total number of samples to generate
    generated_data = synthesizer.generate_data(samples, total_to_generate)
    
    # Save generated data
    synthesizer.save_to_json(generated_data, output_path)


if __name__ == "__main__":
    main()
