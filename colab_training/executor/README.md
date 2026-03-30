# Google Colab Executor

## ⚠️ Important: Manual Upload Required

Google Colab **does not have a public API** for automation. This is by design to prevent abuse of free GPU resources.

## How It Works

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Local AI Lab  │ ───► │  Your Computer   │ ───► │  Google Colab   │
│                 │      │                  │      │                 │
│  Generates      │      │  You manually    │      │  Free T4 GPU    │
│  notebook file  │      │  upload & run    │      │  Runs training  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

## The Process

### 1. Generate Notebook (Automated)
```bash
lab train start --agent code
```
This generates a `.ipynb` file with all training code pre-configured.

### 2. Upload to Colab (Manual)
You must:
1. Open https://colab.research.google.com
2. Click "Upload" tab
3. Select the generated notebook
4. Upload your `training_data.jsonl` file
5. Runtime → GPU → Run all

### 3. Download & Import (Manual)
When done:
1. Download the `.gguf` file from Colab
2. Import: `lab train import ~/Downloads/model.gguf`

## Why No Automation?

Google intentionally doesn't provide APIs for:
- Running notebooks automatically
- Uploading files programmatically  
- Managing runtime sessions

This prevents:
- Crypto mining on free GPUs
- Automated abuse of resources
- Bots consuming compute

## Alternatives with Automation

| Platform | Automation | Cost | Speed |
|----------|-----------|------|-------|
| **Local Training** | ✅ Full | Free | Fast (M2) |
| **Kaggle** | ✅ API Available | Free | Fast |
| **RunPod** | ✅ API | ~$0.20/hr | Fast |
| **Lambda** | ✅ API | ~$0.50/hr | Fast |
| **Colab** | ❌ None | Free | Fast |

## Recommendation

For fully automated training:
```bash
# Use local training instead (no manual steps!)
lab train local --agent code --background --notify
```

Only use Colab if:
- Your Mac doesn't have enough RAM/GPU
- You specifically need NVIDIA CUDA
- You want to run multiple trainings in parallel

## Keep-Alive Tips

Since you must keep the browser tab open:

**Browser Console Script:**
```javascript
// Press F12 in Colab, paste this in Console:
function clickConnect(){
    console.log("Keeping alive...");
    document.querySelector("colab-connect-button").click();
}
setInterval(clickConnect, 60000);  // Every minute
```

**Extensions:**
- Chrome: "Colab Auto Reconnect" extensions exist
- Firefox: Auto-reload tab extensions

**Best Practice:**
- Use a separate browser window just for Colab
- Don't minimize the window
- Keep it on a separate monitor if possible
