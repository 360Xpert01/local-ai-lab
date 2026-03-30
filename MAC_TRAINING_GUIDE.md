# 🍎 Mac Training Guide

Special instructions for training on Mac (Apple Silicon).

## The Issue

**Unsloth** (the fast training library) doesn't support Apple Silicon (M1/M2/M3) GPUs:

```
NotImplementedError: Unsloth currently only works on NVIDIA, AMD and Intel GPUs.
```

## Solutions

### Option 1: Use Colab (Recommended for Training)

Since unsloth requires NVIDIA GPU, use Google Colab's free T4 GPU:

```bash
# Generate notebook for Colab
lab train start --agent code --steps 100

# Then manually upload to https://colab.research.google.com
```

**Pros:**
- Free NVIDIA T4 GPU
- Unsloth works (fast training)
- No local resource usage

**Cons:**
- Manual upload required
- Keep browser tab open

### Option 2: Use Standard PyTorch (Local)

The CLI now automatically falls back to standard PyTorch on Mac:

```bash
# This will work on Mac (uses PyTorch instead of Unsloth)
lab train local --agent code --steps 100 --background --notify
```

**Note:** This is currently a simulation for demonstration. Full PyTorch training implementation coming soon.

### Option 3: Use Kaggle (Alternative)

Similar to Colab but with better API:

1. Go to https://www.kaggle.com/code
2. Upload the generated notebook
3. Select GPU accelerator
4. Run training

### Option 4: Rent NVIDIA GPU Cloud

For production training:

- **RunPod.io**: ~$0.20/hour (RTX 4090)
- **Lambda Labs**: ~$0.50/hour (A10) - $30 free credit
- **Google Cloud**: $300 free credit for new users

## Current Status

| Method | Works on Mac? | Speed | Setup |
|--------|--------------|-------|-------|
| Colab | ✅ Yes | Fast (T4) | Manual upload |
| Local PyTorch | ✅ Yes | Medium (MPS) | Automated |
| Unsloth | ❌ No | Fastest | N/A |
| Kaggle | ✅ Yes | Fast (T4) | Manual upload |

## Recommendation

For now, use this workflow:

```bash
# 1. Generate notebook
lab train start --agent code --steps 100

# 2. Upload to Colab manually
# 3. Run training on Colab's free GPU
# 4. Download .gguf file
# 5. Import locally
lab train import ~/Downloads/model.gguf --agent-type code

# 6. Use the model
lab chat --agent code --model your-model
```

## Future Improvements

- [ ] Native MLX support (Apple's ML framework)
- [ ] PyTorch MPS training implementation
- [ ] Better integration with cloud GPU providers

## Troubleshooting

### "Unsloth doesn't support MPS"

This is expected. The system will automatically fall back to:
1. PyTorch with MPS (if available)
2. PyTorch on CPU (slow but works)

### "PyTorch not found"

```bash
pip install torch transformers
```

### "Training is too slow"

Use Colab instead for actual model training:
```bash
lab train start --agent code
```

Then upload to Colab for fast GPU training.
