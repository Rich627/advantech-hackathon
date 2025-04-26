import boto3
import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from typing import Optional


class BedrockDataSynthesizer:
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-west-2",
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
   
    def _create_prompt(self, examples: List[Dict[str,Any]], data_samples: List[Dict[Any, Any]], num_to_generate: int) -> str:
        """Create a prompt for the language model to generate similar data."""
        prompt = "Human: 這裡有一些範例資料，請參考它們的格式與細節，然後針對後面給定的裂縫資料，產生 engineer、risk_level、action。\n\n"
        prompt += "=== 範例 (sample_metadata.json) ===\n"
        prompt += json.dumps(examples, ensure_ascii=False, indent=2) + "\n\n"
        prompt += "=== 請根據以下資料產生欄位 ===\n"
        prompt += (
            f"以下是 {num_to_generate} 筆待生成的裂縫資料：\n"
            + json.dumps(data_samples, ensure_ascii=False, indent=2)
            + "\n\n"
        )
        prompt += (
            "請輸出 JSON 陣列，每筆只含三個欄位：\n"
            "1. engineer：從 張工程師、李工程師、王工程師、陳工程師、林工程師 中選一位\n"
            "2. risk_level：根據示例和資料內容判斷，從 Low, Medium, High 選一個\n"
            "3. action：詳盡描述修復流程，至少 30 字，不可只寫「作業描述」等簡化語句\n"
            "Assistant: "
        )
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

    def _validate_llm_output(
        self,
        llm_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Only validate/fix the three LLM‐generated fields:
        - engineer: must be from the fixed list
        - risk_level: must be Low/Medium/High
        - action: must be >=30 chars, and include one of the 4 keywords
        """
        valid_engineers = ["張工程師", "李工程師", "王工程師", "陳工程師", "林工程師"]
        valid_risk_levels = ["Low", "Medium", "High"]
        valid_action_cats = ["灌漿修補", "裂縫填充", "表面處理", "結構加固"]
        # 預設可替補的 action
        default_actions = [
            "使用高滲透性環氧樹脂進行灌漿修補，並在裂縫表面進行打磨以恢復結構完整性。",
            "清除裂縫表面後以彈性防水材料填充，增強防滲水性能。",
            "對結構裂縫處進行表面打磨處理，並塗覆保護塗層提升耐久性。",
            "安裝碳纖維補強材料並塗覆環氧樹脂進行結構加固作業。"
        ]

        validated = []
        for item in llm_data:
            # engineer
            if item.get("engineer") not in valid_engineers:
                item["engineer"] = random.choice(valid_engineers)

            # risk_level
            if item.get("risk_level") not in valid_risk_levels:
                item["risk_level"] = random.choice(valid_risk_levels)

            # action: 長度至少30字、且必須包含至少一個大類關鍵字
            action = item.get("action", "")
            if (not action
                or len(action) < 30
                or not any(cat in action for cat in valid_action_cats)
            ):
                item["action"] = random.choice(default_actions)

            validated.append(item)
        return validated

    def generate_data(self, examples: List[Dict[Any,Any]], base_samples: List[Dict[Any, Any]], total_count: int) -> List[Dict[Any, Any]]:
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
            print(f"⏳ Generating batch of {batch_size} samples... Remaining: {remaining}")

            try:
                prompt = self._create_prompt(examples, base_samples, batch_size)
                response_text = self._invoke_bedrock(prompt)
                batch_data = self._parse_response(response_text)

                # Check response
                if not isinstance(batch_data, list):
                    if isinstance(batch_data, dict):
                        batch_data = [batch_data]
                    else:
                        print(f"⚠️ Unexpected response format: {type(batch_data)}. Skipping this batch.")
                        time.sleep(2)
                        continue

                # Validate and fix data
                valid_batch = self._validate_llm_output(batch_data)

                # 如果回的筆數不足，補滿
                if len(valid_batch) < batch_size:
                    print(f"⚠️ Warning: Requested {batch_size} samples but only received {len(valid_batch)}. Retrying missing {batch_size - len(valid_batch)} samples.")
                    remaining += (batch_size - len(valid_batch))  # 補回需要的量

                all_generated_data.extend(valid_batch)
                remaining -= len(valid_batch)

                print(f"✅ Batch generated: {len(valid_batch)} samples. Total generated so far: {len(all_generated_data)}")

                # 避免被 API rate limit
                if remaining > 0:
                    time.sleep(1)

            except Exception as e:
                print(f"❌ Error generating batch: {str(e)}")
                time.sleep(3)  # After error, wait a bit longer before retrying

        print(f"🎯 Finished generating {len(all_generated_data)} samples.")
        return all_generated_data
    
    def save_to_json(self, data: List[Dict[Any, Any]], output_path: str) -> None:
        """Save generated data to a JSON file."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Successfully saved {len(data)} samples to {output_path}")
        except Exception as e:
            print(f"❌ Error saving data to {output_path}: {str(e)}")


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


def load_image_metadata(folder: str) -> List[Dict[str, Any]]:
    """Load all image_metadata JSON files in the given folder."""
    metadata = []
    for fname in sorted(os.listdir(folder)):
        if fname.lower().endswith('.json'):
            path = os.path.join(folder, fname)
            with open(path, 'r', encoding='utf-8') as f:
                metadata.append(json.load(f))
    return metadata
    

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_folder = os.path.join(base_dir, 'image_metadata')
    output_path = os.path.join(base_dir, 'metadata', 'generated_metadata.json')
    sample_path = os.path.join(base_dir, 'metadata', 'sample_metadata.json')
    examples = load_samples(sample_path)

    # 1. Load base metadata
    image_data = load_image_metadata(metadata_folder)
    if not image_data:
        print("No image metadata found.")
        return

    # 2. Generate LLM fields
    synthesizer = BedrockDataSynthesizer(batch_size=len(image_data))
    llm_results = synthesizer.generate_data(examples, image_data, len(image_data))

    # 3. Merge results
    merged = []
    for base, llm in zip(image_data, llm_results):
        merged_item = base.copy()
        merged_item['engineer'] = llm.get('engineer', '')
        merged_item['risk_level'] = llm.get('risk_level', '')
        merged_item['action'] = llm.get('action', '')
        merged.append(merged_item)

    # 4. Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Saved merged metadata to {output_path}")

if __name__ == "__main__":
    main()
