# Colab Training Pipeline

This directory contains training data and notebook templates for fine-tuning models via Google Colab Free Tier.

## Directory Structure

```
colab_training/
├── training_data/           # Training datasets for each agent type
│   ├── code/               # Programming examples
│   ├── security/           # Security patterns and fixes
│   ├── ops/                # DevOps configurations
│   └── architecture/       # System design examples
├── templates/              # Jupyter notebook templates
│   └── unsloth_base.ipynb.j2
├── generated/              # Auto-generated notebooks
├── generate.py             # Notebook generation script
└── README.md
```

## Training Data

### Code Examples (`training_data/code/`)
- `alpaca_code.jsonl` - General programming tasks in Alpaca format
- Topics: Algorithms, data structures, Python, TypeScript, SQL

### Security Examples (`training_data/security/`)
- `secure_code.jsonl` - Security audits and fixes
- Topics: SQL injection, XSS, password hashing, session management, file uploads

### DevOps Examples (`training_data/ops/`)
- `docker_examples.jsonl` - Docker configurations
- `k8s_manifests.jsonl` - Kubernetes deployments
- `terraform_examples.jsonl` - Infrastructure as Code
- `github_actions.jsonl` - CI/CD pipelines

### Architecture Examples (`training_data/architecture/`)
- `system_design.jsonl` - System design case studies
- `design_patterns.jsonl` - Architecture patterns
- `api_design.jsonl` - API design examples

## Data Format

All training data uses Alpaca format:

```json
{
  "instruction": "Write a Python function to...",
  "input": "Additional context (can be empty)",
  "output": "The complete solution with explanations"
}
```

## Generating Notebooks

### Using the CLI

```bash
# Generate notebook for code agent with Qwen model
lab train start --agent code --base-model qwen2.5-coder-7b-instruct

# Generate notebook for security agent with Llama model
lab train start --agent security --base-model llama-3.1-8b-instruct
```

### Using the Script Directly

```bash
python colab_training/generate.py \
  --agent code \
  --model qwen2.5-coder-7b-instruct \
  --output colab_training/generated
```

## Fine-tuning Workflow

1. **Prepare Training Data**
   ```bash
   # Edit the JSONL files in training_data/<category>/
   # Add your own examples following the Alpaca format
   ```

2. **Generate Notebook**
   ```bash
   lab train start --agent <type> --base-model <model>
   ```

3. **Upload to Colab**
   - Upload the generated `.ipynb` file
   - Upload your `training_data.jsonl` file

4. **Run Training**
   - Execute all cells in order
   - Training takes ~10-30 minutes on T4 GPU

5. **Download Model**
   - The notebook will download the `.gguf` file
   - Move it to your local setup folder

6. **Import to Ollama**
   ```bash
   lab train import path/to/model.gguf --name my-custom-agent
   ```

## Hardware Requirements

| Model Size | VRAM Required | Colab Free Tier |
|------------|---------------|-----------------|
| 7B Q4_K_M  | ~6 GB         | ✅ T4 GPU       |
| 13B Q4_K_M | ~10 GB        | ⚠️ May OOM      |
| 7B Q8_0    | ~8 GB         | ⚠️ May OOM      |

## Training Tips

1. **Start Small**: Use 50-100 training steps for testing
2. **Quality over Quantity**: 100 good examples > 1000 poor examples
3. **Diverse Examples**: Include various scenarios for your use case
4. **Validate Output**: Always test the fine-tuned model before deployment
5. **Iterate**: Fine-tune in small increments and evaluate

## Custom Training Data

Create your own `training_data.jsonl`:

```jsonl
{"instruction": "Your task description", "input": "", "output": "Expected output"}
{"instruction": "Another task", "input": "Context", "output": "Solution"}
```

## Troubleshooting

### Out of Memory
- Reduce batch size in notebook
- Use Q4_K_M instead of Q8_0 quantization
- Reduce sequence length

### Poor Results
- Increase training steps
- Add more diverse examples
- Check for overfitting (validate on held-out data)

### Colab Disconnects
- Use Colab Pro for longer training
- Save checkpoints more frequently
- Use smaller max_steps and iterate

## References

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
