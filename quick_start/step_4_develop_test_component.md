# Step 4: 開發和測試 Greengrass 元件

## 1. 建立必要的目錄結構
```bash
# 創建 Greengrass V2 配置和組件文件的目錄
mkdir -p ~/greengrassv2/{recipes,artifacts}
cd ~/greengrassv2
```

## 2. 創建組件配置文件 (Recipe)
執行以下命令創建配置文件：
```bash
nano recipes/com.example.HelloWorld-1.0.0.yaml
```

將以下內容複製到配置文件中：
```yaml
---
RecipeFormatVersion: '2020-01-25'
ComponentName: com.example.HelloWorld
ComponentVersion: '1.0.0'
ComponentDescription: My first AWS IoT Greengrass component.
ComponentPublisher: Amazon
ComponentConfiguration:
  DefaultConfiguration:
    Message: world
Manifests:
  - Platform:
      os: linux
    Lifecycle:
      run: |
        python3 -u {artifacts:path}/hello_world.py "{configuration:/Message}"
  - Platform:
      os: windows
    Lifecycle:
      run: |
        py -3 -u {artifacts:path}/hello_world.py "{configuration:/Message}"
```

## 3. 創建組件代碼目錄
```bash
# 創建存放 Python 代碼的目錄
mkdir -p artifacts/com.example.HelloWorld/1.0.0
```

## 4. 創建 Python 程序文件
創建並編輯 Python 文件：
```bash
nano artifacts/com.example.HelloWorld/1.0.0/hello_world.py
```

添加以下 Python 代碼：
```python
import sys

message = "Hello, %s!" % sys.argv[1]

# Print the message to stdout, which Greengrass saves in a log file.
print(message)
```

## 5. 部署和測試組件

### 5.1 創建本地部署
```bash
sudo /greengrass/v2/bin/greengrass-cli deployment create \
  --recipeDir ~/greengrassv2/recipes \
  --artifactDir ~/greengrassv2/artifacts \
  --merge "com.example.HelloWorld=1.0.0"
```

### 5.2 查看組件日誌
```bash
sudo tail -f /greengrass/v2/logs/com.example.HelloWorld.log
```

預期輸出：
```
Hello, world!
```

## 6. 修改組件代碼
更新 Python 文件內容：
```python
import sys

message = "Hello, %s!" % sys.argv[1]
message += " Greetings from your first Greengrass component."

# Print the message to stdout, which Greengrass saves in a log file.
print(message)
```

## 7. 更新和重啟組件

### 7.1 更新部署
```bash
sudo /greengrass/v2/bin/greengrass-cli deployment create \
  --recipeDir ~/greengrassv2/recipes \
  --artifactDir ~/greengrassv2/artifacts \
  --merge "com.example.HelloWorld=1.0.0"
```

### 7.2 重啟組件
```bash
sudo /greengrass/v2/bin/greengrass-cli component restart \
  --names "com.example.HelloWorld"
```

預期輸出：
```
Hello, world! Greetings from your first Greengrass component.
```