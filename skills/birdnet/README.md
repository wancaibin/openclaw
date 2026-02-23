# BirdNET 鸟类识别技能

使用 BirdNET API 识别鸟类鸣叫声。

## 配置

### 方式 1：BirdNET API（推荐）

1. 获取 API 密钥：https://birdnet.cornell.edu/api/
2. 在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "birdnet": {
      "apiKey": "YOUR_BIRDNET_API_KEY",
      "apiUrl": "https://birdnet.cornell.edu/api/v1"
    }
  }
}
```

### 方式 2：本地 BirdNET 模型

1. 安装 BirdNET-Analyzer：
```bash
brew install birdnet-analyzer
```

2. 配置本地路径：
```json
{
  "skills": {
    "birdnet": {
      "mode": "local",
      "modelPath": "/path/to/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite",
      "labelPath": "/path/to/labels.txt"
    }
  }
}
```

## 使用方法

### 识别音频文件
```bash
birdnet identify /path/to/recording.wav
```

### 实时监控
```bash
birdnet monitor --device "Built-in Microphone"
```

## 输出示例

```json
{
  "species": "Erithacus rubecula",
  "commonName": "European Robin",
  "confidence": 0.94,
  "timestamp": "2026-02-23T13:21:00Z"
}
```
