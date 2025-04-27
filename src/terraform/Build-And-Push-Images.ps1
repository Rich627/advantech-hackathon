# PowerShell 腳本：構建並推送 AWS Lambda Docker 映像
# 適用於 Windows 環境

# 設置變數
$AWS_REGION = "us-west-2"
$ECR_URL = "467392743157.dkr.ecr.us-west-2.amazonaws.com"
$LAMBDA_FUNCTIONS = @(
    "llm_issue_handler",
    "doc_process",
    "util",
    "sns_handler",
    "pdf_ingest_handler",
    "render_frontend",
    "complete",
    "presigned_url"
)
$NO_RETRY = $env:NO_RETRY -eq "true"  # 控制是否禁用重試機制的環境變量

# 顯示使用方法
function Show-Usage {
    Write-Host "用法: $($MyInvocation.MyCommand.Name) [函數名稱]"
    Write-Host "如果沒有提供函數名稱，將構建並推送所有 Lambda 函數"
    Write-Host "可用的函數:"
    foreach ($func in $LAMBDA_FUNCTIONS) {
        Write-Host "  - $func"
    }
    Write-Host ""
    Write-Host "環境變量:"
    Write-Host "  `$env:NO_RETRY='true'    禁用推送失敗時的重試機制"
    exit 1
}

# 構建和推送單個函數的 Docker 映像
function Build-And-Push {
    param (
        [string]$functionName
    )
    
    Write-Host "==== 處理 $functionName ===="
    
    $lambdaPath = Join-Path -Path "..\lambda" -ChildPath $functionName
    
    # 檢查 Lambda 函數目錄是否存在
    if (-not (Test-Path -Path $lambdaPath -PathType Container)) {
        Write-Host "錯誤: 目錄 $lambdaPath 不存在" -ForegroundColor Red
        return $false
    }
    
    # 切換到 Lambda 函數目錄
    $originalDir = Get-Location
    Set-Location -Path $lambdaPath
    
    # 檢查 Dockerfile 是否存在
    if (-not (Test-Path -Path "./Dockerfile" -PathType Leaf)) {
        Write-Host "錯誤: 在 $lambdaPath 中找不到 Dockerfile" -ForegroundColor Red
        Set-Location -Path $originalDir
        return $false
    }
    
    # 備份原始 Dockerfile
    Copy-Item -Path "Dockerfile" -Destination "Dockerfile.bak"
    
    # 修改基礎映像以確保平台兼容性
    $dockerfileContent = Get-Content -Path "Dockerfile" -Raw
    if ($dockerfileContent -match "FROM public.ecr.aws/lambda/python") {
        Write-Host "更新基礎映像以確保平台兼容性..."
        $newContent = "FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9`n"
        $newContent += $dockerfileContent -replace ".*FROM public.ecr.aws/lambda/python.*`n", ""
        Set-Content -Path "Dockerfile" -Value $newContent
    }
    elseif ($dockerfileContent -match "FROM amazon/aws-lambda-python") {
        Write-Host "更新 Amazon 基礎映像以確保平台兼容性..."
        $newContent = "FROM --platform=linux/amd64 amazon/aws-lambda-python:3.9`n"
        $newContent += $dockerfileContent -replace ".*FROM amazon/aws-lambda-python.*`n", ""
        Set-Content -Path "Dockerfile" -Value $newContent
    }
    
    # 確保 requirements.txt 存在
    if (-not (Test-Path -Path "./requirements.txt" -PathType Leaf)) {
        Write-Host "創建空的 requirements.txt"
        New-Item -Path "./requirements.txt" -ItemType File
    }
    
    # 構建 Docker 映像
    Write-Host "為 $functionName 構建 Docker 映像..."
    $env:DOCKER_BUILDKIT = 1
    $buildSuccess = $false
    
    try {
        docker build --platform=linux/amd64 -t "${functionName}:latest" .
        $buildSuccess = $?
    }
    catch {
        $buildSuccess = $false
    }
    
    if (-not $buildSuccess) {
        Write-Host "為 $functionName 構建 Docker 映像失敗" -ForegroundColor Red
        # 恢復原始 Dockerfile
        Move-Item -Path "Dockerfile.bak" -Destination "Dockerfile" -Force
        Set-Location -Path $originalDir
        return $false
    }
    
    # 標記映像
    Write-Host "為 $functionName 標記映像..."
    $tagSuccess = $false
    
    try {
        docker tag "${functionName}:latest" "${ECR_URL}/${functionName}:latest"
        $tagSuccess = $?
    }
    catch {
        $tagSuccess = $false
    }
    
    if (-not $tagSuccess) {
        Write-Host "為 $functionName 標記映像失敗" -ForegroundColor Red
        Move-Item -Path "Dockerfile.bak" -Destination "Dockerfile" -Force
        Set-Location -Path $originalDir
        return $false
    }
    
    # 推送到 ECR，帶重試機制
    Write-Host "將 $functionName 推送到 ECR..."
    $pushSuccess = $false
    
    if ($NO_RETRY) {
        # 不使用重試機制
        try {
            docker push "${ECR_URL}/${functionName}:latest"
            $pushSuccess = $?
        }
        catch {
            $pushSuccess = $false
        }
        
        if ($pushSuccess) {
            Write-Host "成功將 $functionName 推送到 ECR" -ForegroundColor Green
        }
        else {
            Write-Host "推送 $functionName 失敗" -ForegroundColor Red
        }
    }
    else {
        # 使用重試機制
        $maxRetries = 3
        $retryCount = 0
        
        while ($retryCount -lt $maxRetries -and -not $pushSuccess) {
            $retryCount++
            Write-Host "推送嘗試 $retryCount / $maxRetries..."
            
            try {
                docker push "${ECR_URL}/${functionName}:latest"
                $pushSuccess = $?
            }
            catch {
                $pushSuccess = $false
            }
            
            if ($pushSuccess) {
                Write-Host "成功將 $functionName 推送到 ECR" -ForegroundColor Green
            }
            else {
                Write-Host "推送嘗試 $retryCount 失敗" -ForegroundColor Yellow
                
                if ($retryCount -lt $maxRetries) {
                    Write-Host "等待 10 秒後重試..."
                    Start-Sleep -Seconds 10
                    # 重新登錄 ECR 後重試
                    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
                }
            }
        }
        
        if (-not $pushSuccess) {
            Write-Host "所有推送嘗試都失敗了，請檢查網絡連接和 AWS 憑證" -ForegroundColor Red
        }
    }
    
    # 恢復原始 Dockerfile
    Move-Item -Path "Dockerfile.bak" -Destination "Dockerfile" -Force
    
    # 返回到原始目錄
    Set-Location -Path $originalDir
    
    if ($pushSuccess) {
        Write-Host "成功構建並推送 $functionName" -ForegroundColor Green
        return $true
    }
    else {
        return $false
    }
}

# 主程序
Write-Host "=== AWS Lambda Docker 映像構建和推送工具 ===" -ForegroundColor Cyan
Write-Host "重試機制: $(if ($NO_RETRY) { '已禁用' } else { '已啟用' })"

# 登錄到 ECR
Write-Host "登錄到 ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# 處理參數
$args = $args -join " "

if ([string]::IsNullOrEmpty($args)) {
    # 沒有指定函數，構建所有函數
    Write-Host "將構建和推送所有 Lambda 函數" -ForegroundColor Cyan
    foreach ($func in $LAMBDA_FUNCTIONS) {
        $success = Build-And-Push -functionName $func
        if (-not $success) {
            Write-Host "處理 $func 時出錯，繼續處理下一個函數" -ForegroundColor Yellow
        }
    }
}
elseif ($args.Split().Length -eq 1) {
    # 檢查提供的函數名稱是否有效
    $found = $false
    foreach ($func in $LAMBDA_FUNCTIONS) {
        if ($func -eq $args) {
            $found = $true
            break
        }
    }
    
    if ($found) {
        $success = Build-And-Push -functionName $args
        if (-not $success) {
            exit 1
        }
    }
    else {
        Write-Host "錯誤: 不認識的函數名稱 '$args'" -ForegroundColor Red
        Show-Usage
    }
}
else {
    Show-Usage
}

Write-Host "完成!" -ForegroundColor Green